---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260710-CURRENT-RUN-SIDECAR-BASH
artifact_type: investigation
tags: [agent-monitoring, workflows, data-quality]
---

# Investigation — TCK-20260710-CURRENT-RUN-SIDECAR-BASH

## Current Behavior

### `.claude/workflows/implement-ticket.js` — 12 total `await agent(` call sites

Full inventory (line numbers of the `await agent(` opening):

| Line | `label` | Phase / agent | Has Step 0b sidecar write today? |
|---|---|---|---|
| 52 | `scope` | Scope / ticket-scoper (both "load existing" and "create new" branches) | **NO** — no `.claude/current_run` write anywhere in either branch (lines 52-136) |
| 195 | `monitoring-write` | (writeMonitoring helper, called from every exit path) | **NO** — by design, see Risks #3 |
| 344 | `investigate` | Investigate / investigator | YES — line 350 |
| 387 | `plan` | Plan / planner | YES — line 393 |
| 450 | `architecture-review` | Review / architecture-reviewer | YES — line 455 |
| 521 | `implement` | Implement / implementer | YES — line 526 |
| 592 | `architecture-verify` | Architecture-Verify / architecture-reviewer | YES — line 597 |
| 655 | `test-scope-and-run` | Test / test-scoper | YES — line 660 |
| 806 | `parity-update` | Parity / parity-updater | YES — line 811 |
| 900 | `security-review` | Security-Review / security-reviewer (conditional) | YES — line 905 |
| 965 | `done-check` | Verify / done-checker | YES — line 970 |
| 1022 | `finalize` | Finalize | YES — line 1025, but combined: this is the file's only call site where the sidecar write **is** "Step 0" itself (no separate ts-capture line, because Finalize's `pushEvent('Finalize', 'finalizer', ...)` at line 1125 passes no `ts` argument and the call has no JSON `schema`) |

So: **9 call sites** use the two-line `Step 0` (ts) / `Step 0b` (sidecar) pattern (lines 347+350, 390+393, 453+455, 524+526, 595+597, 658+660, 809+811, 903+905, 968+970). **1 call site** (Finalize) uses a single combined `Step 0` line that is purely the sidecar write. **2 call sites** (`scope`, `monitoring-write`) have never had any sidecar-write instruction at all. This totals 12 `await agent(` sites, matching the ticket's "~12 confirmed call sites," but only 10 of them currently register a sidecar — the ticket's Scope bullet 1 ("Replace every Step 0b sidecar-write prompt-text instruction... ~12 confirmed call sites") is imprecise on this point (see Risks #1).

Every sidecar-write line uses the identical literal:
```
python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${tid}','seq':${events.length + 1}}))" 2>/dev/null || true
```
`tid` is `ticketInfo.ticket_id` (a validated `TCK-...` string returned by the Scope-phase agent call, implement-ticket.js:140). `events.length + 1` is computed synchronously in JS at the exact template-literal-construction instant, before the `await agent(...)` call is issued — since JS execution here is single-threaded and each phase is `await`-sequenced (no parallel `agent()` calls), there is no race between this read of `events.length` and the `pushEvent(...)` call that later appends to `events` after the agent returns (implement-ticket.js:156-167, e.g. line 381 `pushEvent('Investigate', ...)` runs only after `investigation = await agent(...)` resolves). This resolves the ticket's own "Assumptions/Open Questions" bullet about `events.length + 1` timing drift — confirmed non-issue; moving this same expression from inside a prompt string to inside a `bash()` call string is a purely mechanical relocation with no semantic change.

### Established orchestrator-side `bash()` convention already in this file

Seven existing orchestrator-run `bash()` calls establish the pattern the fix must mirror:
- `tagCheckOutput` (implement-ticket.js:254-261) — args passed as individually-quoted argv elements (`tagsArgs`), never JSON-embedded in the `-c` string; output uses a `TAG_CHECK_JSON:` marker prefix, parsed via `indexOf` + `try/catch JSON.parse`.
- `archCheckOutput` (564-571), `p0ScanOutput` (765-773), `expectedSubsystemsOutput` (797-804), `crossRefOutput` (837-846), `finalizeCheckOutput` (1077-1084), `monitoringCheckOutput` (1135-1142) — same shape.
- The `p0ScanOutput` comment block (implement-ticket.js:756-763, the exact lines the ticket's Scope section cites) explicitly documents *why*: embedding a JSON blob directly inside a double-quoted `python3 -c "..."` string causes the shell to strip the blob's own unescaped nested double-quotes, corrupting the script into a Python `NameError` and silently failing the check open. This is the concrete rationale behind the ticket's "never JSON-embed in python3 -c strings" instruction — directly applicable here since `tid`/`seq` would otherwise be an obvious candidate for inline embedding.

### `tools/agent-monitoring/post_tool_hook.py` (PostToolUse hook, runs on every tool call)

Lines 42-50: on every tool call, reads `.claude/current_run`, sets `run_id = sidecar.get('run_id') or None`, `seq = sidecar.get('seq') or None`; on any read/parse failure (file missing, malformed JSON), both silently default to `None` — no error surfaced. These values are stamped onto the `agent-monitoring/tools.jsonl` record (line 60-69) unconditionally.

`.claude/settings.json:53-91` confirms `PreToolUse`/`PostToolUse` hooks use `matcher: "*"` — they fire for **every** tool call in the session, with no distinction between "the orchestrator's own `bash()`/`agent()` calls" and "a spawned subagent's own tool calls." This means the orchestrator's own sidecar-write `bash()` call is itself subject to the same `PostToolUse` hook: by the time that hook fires, the write has already landed, so the write call gets attributed to the very seq it just wrote (the upcoming agent's seq), not to some hypothetical "orchestrator" identity. Net effect: exactly the same number of tool-call records get attributed to that seq as today (today the agent's own Step 0b bash call self-attributes as call #1 of its own tool usage) — moving the write to the orchestrator doesn't change the count, only which actor issues the write.

### `implement-epic.js` — zero sidecar registration anywhere

`grep -n "current_run"` returns no hits. Its 3 own `await agent(` calls (`discover` at line 62, `batch-monitoring-write` at line 231, `folder-cleanup` at line 260) never write a sidecar. Its "Implement" phase events (implement-epic.js:221-227, `batchEvents`) are synthesized locally from `workflow('implement-ticket', ticketArgs)` results — **one event per child ticket**, not per `agent()` call — and the object literal has no `tool_call_count` key at all, so this concept doesn't map onto that array the same way it does for `implement-ticket.js`'s own phase events. A sidecar fix, if brought into implement-epic.js, would only be relevant to its own 3 direct `agent()` calls, not the per-child batch events.

`docs/agent-monitoring/schema.md` does **not** document this gap anywhere — it only documents the analogous gap for `create-tickets.js` (line 185: *"`create-tickets` does not register a `.claude/current_run` sidecar per agent call, so `tool_call_count` is always `null`"*). No equivalent sentence exists for `implement-epic.js`.

### `create-tickets.js` — zero sidecar registration, matches documented gap

`grep -n "current_run"` returns no hits, confirming schema.md:185's existing claim is accurate for this file specifically.

## Mechanics / Engine Constraints

None. This ticket is `layer: ai` / agent-monitoring tooling — not simulation mechanics. No chapter of `docs/mechanics/` or contract of `docs/engine/` governs `.claude/workflows/*.js` orchestration or `agent-monitoring/` bookkeeping.

## Parity Ledger Overlap

None found. `grep -rn "agent-monitoring|current_run|tool_call_count|sidecar" docs/parity_ledger/` returns zero hits across all 8 subsystem YAML files. This ticket does not touch any parity-ledger-tracked subsystem (substrate, combat_movement, strategic_cognition, town_resource, progression, social_narrative, world_dynamics, infrastructure) — `infrastructure.yaml`'s scope ("Replay, telemetry, observability, workers") covers simulation-runtime observability, not this dev-tooling agent-monitoring system. No parity ledger entries need updating for this ticket.

## Prior Work

- **`tickets/done/TCK-20260709-AGENT-MONITORING-DURATION.md`** (hotfix, no `stored_artifacts/` — self-evident intent per hotfix tier) is the direct precedent this ticket's own idea doc cites: the identical failure *shape* (`duration_s` documented as required but never actually computed, because every caller — `implement-ticket.js`, `implement-epic.js`, `create-tickets.js`, manual invocations — was trusted to pass it and none did). Fixed by moving the computation into `record_run.py` itself, at write time, so it can no longer be forgotten by any caller. This ticket's fix is architecturally analogous but not identical: `duration_s` was fixed by *computing at the point of write* (a single downstream chokepoint); `tool_call_count`/`cost_proxy_score` attribution is fixed by *moving a mechanical side-effect from agent-prompt text to orchestrator code* (a single upstream chokepoint) — same underlying principle ("stop trusting a caller to remember a mechanical step"), different mechanism, so no code is directly reusable, only the design posture.
- **`stored_artifacts/TCK-20260705-GATE-DET-MECHANICS-AUDITOR/`, `TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER/`, `TCK-20260705-GATE-DET-DONE-CHECKER/`, `TCK-20260705-GATE-DET-PARITY-UPDATER/`** established the "orchestrator runs a static Python check via `bash()` before the `agent()` call, injects results into the prompt for the agent to judge rather than self-derive" pattern that produced every `archCheckOutput`/`p0ScanOutput`/etc. call site cited above. Same architectural family as this ticket, but for verdict-provenance fields, not tool-call attribution — this ticket's sibling `TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT` extends that family further for `verified_by`.
- **`stored_artifacts/TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT/`** hardened `record_events.py`/`record_run.py` REQUIRED-field validation at write time — explicitly Out of Scope for this ticket per its own Scope section ("Any change to record_events.py's REQUIRED-field validation logic itself").
- **`tests/tools/test_tag_skill_mapping_check.py`** (against `tools/tag_skill_mapping_check.py`) is the established precedent for a Python test that statically parses `.claude/workflows/implement-ticket.js`'s **raw source text** (never executes it) to assert an invariant about its content — e.g. it currently verifies the tag→skill mapping table embedded in the file's prompt strings stays consistent across the file's multiple independent copies. This is the directly reusable pattern for a new regression test that verifies the Step 0b text is gone and/or that a sidecar-write `bash()` call precedes each `agent()` call — see test_plan.md.

## Risks and Open Questions

1. **BLOCKING — Scope-phase (`ticket-scoper`) coverage is ambiguous.** The Scope-phase `agent()` call (lines 52-136) has **never** had a sidecar-write instruction, in either branch. Its own event (`pushEvent('Scope', 'ticket-scoper', ...)`, line 275) still gets a `seq` (always 1) and is written to `events.jsonl`, but `tool_call_count` for that seq is computed from whatever `.claude/current_run` happened to contain during that call — i.e. leftover state from a prior run's Finalize-phase clear (`printf '{}' > .claude/current_run`, line 237) or, if a prior run crashed before reaching Finalize, genuinely stale data from an unrelated run. The ticket's AC #1 says "every agent() call site... **with** a Step 0b instruction" (literally excludes Scope, since it never had one) — but the ticket's Scope bullet 1 also says "~12 confirmed call sites," which is the total `await agent(` count, not the 10 that actually write a sidecar today. **This is a real, pre-existing correctness gap, distinct from (and not mentioned by) either the ticket text or `docs/agent-monitoring/schema.md`.** Does closing this ticket mean extending sidecar coverage to the Scope phase too (going beyond the literal AC wording, but closing an equivalent-severity gap in the same file), or leaving it exactly as-is (undocumented, unaddressed, matching the AC's literal wording)? Flagging for planner — not decided here.
2. **BLOCKING (named by the ticket itself, Scope bullet 3) — `implement-epic.js`/`create-tickets.js` disposition.** Both files have **zero** sidecar registration of any kind today — there is nothing in either file to "replace," only something that could be "added." `create-tickets.js`'s gap is already documented in `schema.md:185`; `implement-epic.js`'s identical gap is **not** documented anywhere. The ticket requires this ticket to "explicitly resolve... or explicitly document deferring it with rationale" — this is a decision for planner/architecture-review, not something investigation should resolve unilaterally. Two sub-considerations for whoever decides: (a) `implement-epic.js`'s 3 own `agent()` calls are structurally like `implement-ticket.js`'s call sites and could receive the identical fix; (b) `implement-epic.js`'s per-child-ticket `batchEvents` array is NOT one event per `agent()` call, so a sidecar fix there is not applicable to that array regardless of the decision on (a).
3. **`writeMonitoring()`'s own `agent()` call (line 195, label `monitoring-write`) must remain sidecar-free by design — not a gap to "fix."** It doesn't correspond to any `pushEvent`-tracked seq (it's the process that writes `events.jsonl`/`runs.jsonl`, not itself one of the tracked phase events), and it is the exact call that *computes* `tool_call_count`/`cost_proxy_score` by reading `tools.jsonl` (Step 2, lines 202-224) — giving it its own sidecar would create a self-referential ordering problem (it would need to read tool-call records attributed to a seq that doesn't exist until after this same call runs). The plan must explicitly exclude this call site, not accidentally "complete" it while iterating over all `await agent(` sites.
4. **AC #2 cannot be verified by `pytest` alone.** No JS test runner exists in this repo for `.claude/workflows/*.js` (confirmed: no references to these files under any `tests/` directory except the static-text-parsing precedent in `test_tag_skill_mapping_check.py`; these files execute only inside the Claude Code orchestration runtime). AC #2 ("Running implement-ticket.js end-to-end with Step 0b prompt text fully absent still produces non-empty tool_call_count/cost_proxy_score in events.jsonl") is a *runtime outcome* claim. A static text-level regression test (mirroring `test_tag_skill_mapping_check.py`) can prove the **structural** shape (no leftover Step 0b prompt text; a sidecar-write `bash()` call precedes each `agent()` call) but cannot itself execute the workflow to prove the outcome. Satisfying AC #2 as literally worded requires either a live end-to-end `/implement-ticket` run (expensive, and inherently non-deterministic re: LLM agent behavior) documented as a manual verification step, or an explicit, documented decision that the structural static test is accepted as sufficient proxy evidence. Flag for planner and for Test phase.
5. Minor: whether to keep the existing `2>/dev/null || true` fail-open suffix on the relocated sidecar-write command. Recommend keeping it — CLAUDE.md's Hard Rule ("monitoring write failure must never fail the workflow") argues for preserving today's fail-open behavior unchanged, even though orchestrator-run `bash()` calls elsewhere in this file (`tagCheckOutput`, etc.) don't carry it (those calls are checks whose failure the workflow is designed to notice, unlike this one, which is pure bookkeeping).

## Anti-Drift Hazards

- **Do not implement sibling scope.** Every one of the 9 two-line call sites has its `Step 0` (ts capture, e.g. line 347) immediately above its `Step 0b` (sidecar write, e.g. line 350) — textually adjacent, in the same block, in the same 3 files that sibling ticket `TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH` (C2) will separately touch. A careless block-level edit (rather than a precise, line-scoped edit removing only the Step 0b line and leaving Step 0 untouched) risks slurping C2's scope into this ticket's diff, or breaking the `ts` capture while removing the sidecar line. Do not touch the `Step 0: run \`date -u ...\`` lines at all.
- **Do not implement `TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT`'s (C3) `verified_by` scope** — unrelated mechanism (provenance self-report), even though it's also file-adjacent.
- **Do not touch `record_events.py`'s REQUIRED-field validation** — explicitly Out of Scope.
- **Do not touch any of the 4 "related, smaller ideas"** from `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md` (asymmetric gate coverage, cross-retro trend detection, tag→skill dedup, `working_log.csv` backfill) — explicitly named Out of Scope in the ticket.
- **Finalize's call site is structurally different from the other 9** — it has no separate `ts` line and no `ts` field in its (nonexistent) schema. A mechanical find-and-replace across all "Step 0b" occurrences risks either leaving Finalize's sidecar write in place unmodified (inconsistent with the other 9) or introducing a spurious unused `ts` capture into Finalize where none exists today.
- **`.claude/current_run` is a single global, session-wide file with no per-run/session partitioning** — this is a pre-existing characteristic (not introduced by this fix) shared by every concurrent tool call in the whole Claude Code session, including the orchestrator's own `bash()` calls. Do not attempt to fix this partitioning gap under this ticket (out of scope, not named anywhere in Scope), and do not accidentally regress it further (e.g. do not remove or reorder the Step 5 sidecar-clear in `writeMonitoring`, implement-ticket.js:236-237).
- **The ticket is sequenced first of 3 children specifically to avoid line-number collisions with C2/C3** — this ticket's diff should land cleanly (committed/finalized) before C2 or C3 begin editing the same 3 files, per the epic's stated ordering; this is an epic-orchestration concern, not something to enforce inside this ticket's own diff, but worth surfacing since all three tickets touch overlapping line ranges in `implement-ticket.js`.
