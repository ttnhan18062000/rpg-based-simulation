---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP
artifact_type: investigation
tags: [agent-monitoring, process-improvement, hooks]
---

# Investigation — TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP

## Sidecar shape (confirmed against current code)

`.claude/workflows/implement-ticket.js:256-263`, `writeSidecar(seq, phase, agent)`:

```js
const writeSidecar = async (seq, phase, agent) => {
  await bash(`python3 -c "
import json, sys
open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': int(sys.argv[2]), 'phase': sys.argv[3], 'agent': sys.argv[4], 'execution_id': sys.argv[5], 'provider': sys.argv[6]}))
" "${tid}" "${seq}" "${phase}" "${agent}" "${executionId}" "${PROVIDER}" 2>/dev/null || true`)
}
```

Shape: `{run_id, seq, phase, agent, execution_id, provider}`. `execution_id` = `claude-{tid}-{unix_ms}-{8 hex chars}` (`PROVIDER = 'claude'`, generated once per run via `secrets.token_hex(4)`, `implement-ticket.js:210-217`).

10 call sites, one per phase: Investigate(492)/Plan(595)/Review(676)/Implement(745)/Document-Update(814)/Architecture-Verify(947)/Test(1008)/Parity(1164)/Security-Review(1256)/Verify(1319). Scope registers its own sidecar inline (can't reuse `writeSidecar` — `tid` not known yet at ticket-creation time), and `writeMonitoring`'s Step 0 clears the sidecar to `{}` at every exit (`TCK-20260719-...` fix, per schema.md:392) so its own bash/python calls are correctly unattributed.

`tools/agent-monitoring/post_tool_hook.py:44-58` reads `.claude/current_run` on every `PostToolUse` and tags the `tools.jsonl` row; a missing file or read failure leaves all fields `None`/`null` (fail-open, no error).

## Why hand-orchestration forgets it

`.claude/skills/implement-ticket/SKILL.md`'s JS→tool translation table has a row for "Orchestrator-run `await bash(...)` (no `agent()` wrapper)" → "Run the exact command yourself via Bash... never skip it because it 'looks like a detail'". `writeSidecar(...)` calls ARE exactly this construct — but the skill file never names `writeSidecar`/`current_run`/`sidecar` explicitly anywhere (confirmed: `grep -n "sidecar\|current_run" .claude/skills/implement-ticket/SKILL.md` returns zero matches). The instruction to replicate it is present only implicitly, folded into the generic "translate every bash() line" rule — there is no standalone, named callout an orchestrating agent's eye would catch while skimming the phase table. `docs/agent-monitoring/schema.md` documents the mechanism in detail but is a reference doc, not something read at phase-transition time.

Contrast with the two existing PreToolUse hooks in `.claude/settings.json` (grep-nudge on `Bash`, context-search nudge on `Agent`) — both are hooks, not prose, so they fire unconditionally regardless of whether the orchestrating agent happened to reread the skill file closely enough that turn. Prose-only guidance has already been shown insufficient once (a cross-session memory note — "Sidecar shape and index staleness" — already existed for this exact gap and it still recurred).

## PreToolUse hook design

New `.claude/settings.json` PreToolUse entry, matcher `Edit|Write` (not `Bash` — Bash's trivial-command false-positive rate, e.g. `cat`/`ls`/`grep`, is much higher; Edit/Write are reliably substantive):

```
FILE=$(python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',d).get('file_path',''))" 2>/dev/null || true)
case "$FILE" in
  */tickets/*|*/staging_artifacts/*|*/src/*|*/tests/*|*/docs/*)
    if ls tickets/inprogress/*.md >/dev/null 2>&1; then
      RUN_ID=$(python3 -c "import json; print(json.load(open('.claude/current_run')).get('run_id') or '')" 2>/dev/null || true)
      if [ -z "$RUN_ID" ]; then
        echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"sidecar-check: tickets/inprogress/ has an active ticket but .claude/current_run has no run_id. If you are hand-orchestrating implement-ticket.js, write the sidecar (writeSidecar shape: run_id/seq/phase/agent/execution_id/provider) before continuing, or tool_call_count/cost_proxy_score will read 0 for this phase."}}'
      fi
    fi
    ;;
esac
```

### False-positive analysis

1. **Paused ticket, unrelated work happening while it sits in `tickets/inprogress/`.** Real case — the heuristic can't distinguish "actively hand-orchestrating right now" from "ticket parked mid-pipeline, agent doing something else." Accepted, not mitigated further: the hook is advisory (`additionalContext`, non-blocking) — worst case is one extra sentence of context on a file-edit that has nothing to do with the parked ticket. Cost is noise, not correctness. Matches the existing grep-nudge/context-search-nudge hooks' own risk profile (both have the identical class of false positive and are already accepted as-is).
2. **Self-limiting once the sidecar IS written correctly.** Once an orchestrating agent writes the sidecar for a phase, `run_id` is non-empty and the hook stays silent for the rest of that phase's Edit/Write calls — it does not nag on every single tool call throughout a correctly-orchestrated run, only when the sidecar is genuinely missing.
3. **File-path scoping (`*/tickets/*|*/staging_artifacts/*|*/src/*|*/tests/*|*/docs/*`)** keeps it from firing on incidental edits to files clearly unrelated to ticket work (e.g. this investigation.md write itself would fire — intentionally, since staging_artifacts writes are real phase-attributable work).
4. Did **not** add a debounce/rate-limit marker file — considered, but rejected as unneeded complexity: since the hook goes silent the moment the sidecar is correctly populated, spam only occurs across genuinely-missing-sidecar tool calls, which is exactly the condition worth flagging repeatedly (each one is really unattributed).

## Existing hook test pattern

`tests/tools/` has no test file for the two existing PreToolUse case-statement hooks (grep-nudge, context-search-nudge) — they live as inline shell in `.claude/settings.json` itself, untested by any `test_*hook*.py`. `test_post_tool_hook.py` and `test_codex_hook_payload_fixture.py` exist but cover `post_tool_hook.py` (a real Python script), not the settings.json-embedded shell one-liners. There is no established Python-testable pattern for this class of hook — consistent with the other two, this ticket's new hook is also inline shell in `.claude/settings.json`, not a standalone script, so it inherits the same untested-by-pytest status as its two precedents. Not treated as a gap this ticket must close (would be scope creep beyond what the two precedent hooks themselves have).

## Skill doc strengthening

`.claude/skills/implement-ticket/SKILL.md`'s translation table gets one explicit new row naming `writeSidecar` directly (see Plan) rather than leaving it implicit under the generic bash-translation rule.
