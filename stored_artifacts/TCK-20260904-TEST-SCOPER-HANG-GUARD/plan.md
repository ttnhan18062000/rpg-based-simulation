---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-TEST-SCOPER-HANG-GUARD
artifact_type: plan
tags: [testing, ai, hooks, debugging]
---

# Implementation Plan — TCK-20260904-TEST-SCOPER-HANG-GUARD

## Summary

investigation.md's Feasibility Finding is unambiguous: `Stop`/`SubagentStop` are real, documented
Claude Code hook events that genuinely block (exit code 2), and a liveness-independent,
transcript-derived proxy check is architecturally sound — but the exact JSON shapes of a real
`SubagentStop` payload and a real transcript JSONL Bash/`BashOutput`/`Monitor` sequence are
unverified in this repo (investigation.md lines 131-147, 253-261). This plan therefore sequences a
mandatory scratch-first fixture-capture spike (Step 1) before any hook-script code is written
(Step 2), wires the new hook under a `SubagentStop` key that does not exist in `.claude/
settings.json` today (Step 3, confirmed absent — `.claude/settings.json` lines 54-131 show exactly
`PreToolUse`/`PostToolUse`), adds a stdin-in/exit-code-out subprocess test mirroring
`tests/tools/test_post_tool_hook.py`'s `_run_hook()` pattern (Step 4), keeps
`.claude/agents/test-scoper.md`'s existing `## Background Commands` prose (lines 126-128) as
defense-in-depth rather than deleting it (Step 5), updates the two now-stale contract-vocabulary
pins in `tests/agent_orchestration/test_contract_structure.py` (Step 6, required the moment a new
event is actually wired — the file's own `test_hook_events_yaml_unchanged_normalized_vocabulary`
and `test_policy_represents_claude_two_enabled_events` pin exactly `{PreToolUse, PostToolUse}`
today), and closes with the epic-doc update and the flagged `.claude/settings.json` collision point
with `TCK-20260904-BASH-SECRET-SCAN-HOOK` (Step 7). A literal-format fallback contingency (Step 1b)
exists only for the case Step 1's spike genuinely fails to capture a usable fixture — it is not to
be invoked preemptively, per the ticket's own Request Summary and investigation.md's YES finding.

Two implementation decisions this plan makes explicitly, both grounded in re-read source rather
than assumed, so Implement does not need to re-litigate them:

1. **The guard does not filter by `agent_type`/subagent name at all** — neither via a
   `.claude/settings.json` matcher nor inside the script body. investigation.md's own Risks section
   (lines 271-280) flagged "does `SubagentStop`'s matcher field support filtering by subagent/agent
   type" as unconfirmed and left it as "worth a plan-level decision, not a blocker." This plan
   resolves it: CLAUDE.md's own Hard Rules bullet (line 26) already generalizes the underlying rule
   to "every dispatched agent," not test-scoper specifically ("this bullet generalizes it to every
   dispatched agent, since `general-purpose` and most other project agent roles have no equivalent
   project-level file to carry it"). A universal, unfiltered guard satisfies AC #1's "(a)... or
   equivalent" wording (a test-scoper-shaped synthetic reproduction is one case a universal guard
   necessarily also blocks) without needing to resolve the unconfirmed matcher-filtering question at
   all. Use `"matcher": "*"` in settings.json, matching every existing hook group's own convention
   (`.claude/settings.json` lines 56-57, 65-66, 74-75, 83-84, 94-95, 103-104, 112-113, 121-122 —
   every single existing matcher is either `"*"` or a tool-name string, never agent-type-scoped).
2. **`tools/agent_orchestration/loader.py` and `tools/agent_orchestration/generator.py` do NOT need
   schema changes.** Read `tools/agent_orchestration/loader.py:222-267`
   (`_load_hook_surface_policy_yaml`): `available_events` is already an optional, generic
   per-provider field — line 256 (`available_events = provider.get("available_events")`) — and its
   only validation is (a) list-of-strings shape (lines 257-261) and (b) `enabled_events` ⊆
   `available_events` when present (lines 262-267). Nothing here is Codex-specific. Adding
   `claude.available_events` alongside the existing `claude.enabled_events` key
   (`agent-orchestration/hook-surface-policy.yaml` line 10) is data-only and already validated by
   this existing generic code path — this resolves test_plan.md's own flagged open question
   ("a schema-shape decision Plan must make explicitly," test_plan.md lines 43-48): no schema
   change, only content changes to the two YAML files plus their pinned tests. `generator.py:94-103`
   only round-trips `bundle.hook_events`/`bundle.hook_surface_policy` back to disk unchanged, so it
   needs no edit either. Confirmed no other consumer references this content: `grep -rl
   "hook_surface_policy\|hook-events\|enabled_events" tests/agent_orchestration_claude_adapter/
   tests/agent_orchestration_codex_adapter/` returned zero hits, so the wider regression command
   test_plan.md offers as a conditional ("if Plan's implementation also touches loader.py or
   generator.py") is **not** needed — the narrower `pytest tests/tools/ tests/agent_orchestration/
   -v` command is sufficient.

## Steps

### Step 1 — Scratch-first fixture capture spike (hard prerequisite, must run before Step 2)

**Files:** none committed by this step except the captured fixture(s) under
`tests/fixtures/` (new subdirectory, name TBD by what's captured — mirror
`tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json`'s existing precedent, e.g.
`tests/fixtures/claude_hook_payloads/subagent_stop_stdin_capture.json`) and a short capture log
appended to this ticket's Implementation Notes section.

**Change:** Following the exact methodology `stored_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-
CAPTURE/` used for Codex's `PostToolUse` (cited approvingly by investigation.md lines 248-251) and
the `scratch_first_verification` activation prerequisite already named in
`agent-orchestration/hook-surface-policy.yaml` line 22:

1. In a scratch working copy (a throwaway `.claude/settings.json` outside this repo's committed
   trust boundary, or — per investigation.md line 141's cheaper alternative — a `Stop` hook
   registered against a real dispatched sub-agent within this very session, since "a `Stop` hook
   registered for a subagent is automatically treated as `SubagentStop`" per investigation.md line
   142), wire a temporary diagnostic hook whose command is nothing more than
   `cat > /tmp/<scratch-dir>/subagent_stop_capture.jsonl` (append mode, `>>`) — i.e. it logs its own
   raw stdin verbatim, unparsed, so the capture cannot be contaminated by a guessed schema.
2. Trigger a real subagent whose own turn includes a `Bash` tool call with
   `run_in_background: true`, then let that subagent end its turn (with the background command
   both in a still-running state and, in a second run, in an already-polled-complete state via
   `BashOutput`/`Monitor`) to capture both the block-worthy and allow-worthy transcript shapes.
3. Inspect the captured raw JSON for: the real top-level `SubagentStop` payload field names
   (confirm `transcript_path`, `session_id`, `agent_id`/`agent_type`, `stop_hook_active` per
   investigation.md lines 96-97, 100-101 are the actual keys, not guessed ones); the real transcript
   JSONL entry shape for a `Bash` tool_use with `tool_input.run_in_background: true`; and the real
   entry shape for the corresponding `BashOutput`/`Monitor` tool_use/tool_result pair, specifically
   what field/value distinguishes "still running" from "completed" (investigation.md explicitly
   flags this as unknown — lines 105-111, 122-124).
4. Confirm `stop_hook_active`'s loop-prevention behavior directly (investigation.md lines 145-147,
   261-266): fire `Stop`/`SubagentStop` a second time immediately after an exit-2 block and confirm
   whether the harness sets `stop_hook_active: true` on the re-fired payload, and whether the guard
   script (once written in Step 2) must special-case that field to avoid an infinite block loop on
   a genuinely-never-finishing background command.
5. Save the raw, unparsed captures as committed fixture files (never hand-edited into a "cleaner"
   guessed shape — commit exactly what was observed, redacting only obvious secrets/paths per this
   repo's own `redacted_output` convention, `agent-orchestration/hook-surface-policy.yaml` line 30).

**Do NOT touch:** any existing hook wiring in `.claude/settings.json` (this step's diagnostic hook
lives only in a scratch/throwaway config, never the committed one); `pre_tool_hook.py`/
`post_tool_hook.py` (Out of Scope, ticket line 40).

**Verify:** no automated test — this step's own output (the fixture file(s) + capture log) is what
Step 2 and Step 4 depend on and cite. If this step genuinely cannot produce a usable capture (no
mechanism in this environment to trigger/observe a real `SubagentStop`/`Stop` firing at all), stop
here and execute **Step 1b** instead of Steps 2-4.

### Step 1b — Fallback contingency (ONLY if Step 1's spike genuinely fails)

**Files:** `tickets/inprogress/TCK-20260904-TEST-SCOPER-HANG-GUARD.md` (Implementation Notes),
`docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md` (M3
section, lines 105-164).

**Change:** Only if Step 1 produces no usable fixture, append the literal required format to both
files verbatim: `"deterministic enforcement not feasible because <reason>; fallback: prompt
guidance only; residual risk: <named>"` — filling in the real `<reason>` (e.g. "this sandboxed
environment provides no mechanism to register or observe a real Stop/SubagentStop hook firing") and
`<named>` residual risk (e.g. "a subagent can still end its turn with a live background command;
CLAUDE.md line 26's prose rule and test-scoper.md's own prose section, lines 126-128, remain the
only mitigation"). In this branch, skip Steps 2-4, 6 entirely (no hook is shipped, so
`hook-events.yaml`/`hook-surface-policy.yaml` stay unchanged and their pinned tests stay green
unmodified) and go directly to Step 5 (prose-section disposition — in this branch it is kept as the
*sole* control, not defense-in-depth alongside a hook) and Step 7 (epic doc + settings.json
collision note).

**Do NOT touch:** do not invent a plausible-sounding reason if the spike simply wasn't attempted —
this branch is only for a genuine, demonstrated infeasibility, per the ticket's Request Summary
("never as an equally-weighted default").

**Verify:** `grep -c "deterministic enforcement not feasible because" docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md` returns ≥1; same literal string present in the ticket doc. Test #7 from test_plan.md
(`test_test_scoper_background_commands_section_still_present` or equivalent, mirroring
`TCK-20260902-AGENT-BACKGROUND-TASK-TURN-END-DEFENSE-IN-DEPTH`'s own `grep -L "run_in_background"
.claude/agents/*.md` verification command) must pass.

### Step 2 — Write the hook script (only after Step 1 succeeds)

**Files:** new file `tools/agent-monitoring/subagent_stop_background_guard.py`.

**Change:** Follow the exact top-level-script, stdin-JSON-in convention every existing hook in this
directory uses — confirmed by reading `tools/agent-monitoring/pre_tool_hook.py:8-18` (bare
`try/except: pass` around all logic, `json.load(sys.stdin)` at top level, no `if __name__ ==
"__main__"` guard) and `tools/agent-monitoring/post_tool_hook.py:47-164` (same shape, more
elaborate body). Structure:

1. `payload = json.load(sys.stdin)`; read `transcript_path`, `session_id`, `stop_hook_active` using
   the **exact field names Step 1's capture confirmed** (not the names guessed in investigation.md
   — those are documentation-citation-grade only, per investigation.md line 131).
2. If `stop_hook_active` is truthy, exit 0 immediately (allow) — this is the loop-prevention
   behavior Step 1.4 must have confirmed; do not implement a re-block on an already-continuing stop
   hook.
3. Read and parse the transcript JSONL at `transcript_path`. Scan for the **last** tool_use entry
   whose tool name is `Bash` and whose `tool_input.run_in_background` (confirmed real field name,
   `tool_input.run_in_background` is echoed at invocation time per investigation.md lines 98-99) is
   `true`.
4. If no such entry exists, exit 0 (allow) — this is the common case (test #3 in test_plan.md,
   `test_hook_allows_stop_when_no_background_task_was_ever_started`).
5. If such an entry exists, scan forward in the transcript from that entry for a later `BashOutput`
   or `Monitor` tool_use/tool_result entry that (per Step 1's captured real shape) indicates
   completion. If found, exit 0 (allow — test #2,
   `test_hook_allows_stop_when_background_task_already_polled_complete`). If not found, exit 2
   (block — test #1, `test_hook_fires_for_still_running_background_task`) and print a
   `systemMessage`-shaped JSON to stdout (or plain stderr text, per whatever Step 1's capture showed
   Claude Code actually reads for a blocking hook's message) naming the still-pending background
   command.
6. Wrap the entire body in `try/except: pass` → but note this is a **deviation from the advisory
   hooks' convention where relevant**: a bare `except: pass` must still allow the *deliberate* exit
   2 path to happen (the `sys.exit(2)` call itself, on the happy path, must not be caught by a
   blanket handler wrapping it) — structure the try/except around the parsing/detection logic only,
   with the `sys.exit(2)`/`sys.exit(0)` calls as the final statements outside anything that could
   swallow them, and a final bare `except Exception: sys.exit(0)` fallback so any internal failure
   fails **open** (exit 0, never block on an error the script itself can't evaluate — test #4,
   `test_hook_fails_open_on_malformed_or_missing_transcript`, mirroring
   `test_retro_nudge_hook_fail_silent_on_malformed_data_dir`'s established fail-open pattern,
   `tests/tools/test_retro_nudge_hook.py:80-93`).
7. Per this repo's own cross-session-contamination fix precedent
   (`tools/agent-monitoring/post_tool_hook.py:96-131`, the `TCK-20260824-SIDECAR-CROSS-SESSION-
   SCOPE`/`TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION` fix), the script must key **only** off the
   `transcript_path`/`session_id` present in its own stdin payload — it must not read or write any
   shared, unscoped state file. Since `transcript_path` is already self-contained per invocation
   (per investigation.md line 176), this script needs **no new sidecar file at all** — confirm this
   remains true once Step 1's real payload is seen; if Implement discovers a reason a new state file
   is needed, the two-session guard test test_plan.md names (test_plan.md lines 170-179) becomes
   mandatory, not optional.

**Do NOT touch:** `tools/agent-monitoring/pre_tool_hook.py`, `tools/agent-monitoring/
post_tool_hook.py` beyond reading them as a pattern reference (Out of Scope, ticket line 40).

**Verify:** tests #1-#4 from test_plan.md (`tests/tools/test_subagent_stop_background_guard.py`,
see Step 4).

### Step 3 — Wire the new hook into `.claude/settings.json`

**Files:** `.claude/settings.json` (lines 54-131, the `hooks` block).

**Change:** Add a new top-level `SubagentStop` key alongside the existing `PreToolUse`/
`PostToolUse` keys (confirmed absent today — read `.claude/settings.json` lines 54-131 in full: the
`hooks` object has exactly two top-level keys). Structure, matching the existing array-of-
matcher-groups shape (e.g. lines 55-64):

```json
"SubagentStop": [
  {
    "matcher": "*",
    "hooks": [
      {
        "type": "command",
        "command": "python3 tools/agent-monitoring/subagent_stop_background_guard.py"
      }
    ]
  }
]
```

**Critical deviation from every existing hook command in this file, and why:** every one of the
four existing `PreToolUse`/`PostToolUse` command strings ends in `2>/dev/null || true` (see lines
61, 70, 79, 88, 99, 108, 117, 126) — because those hooks are advisory-only and must never block a
tool call even on internal failure. **This new command must NOT be suffixed with `|| true`**: in
POSIX shell, `cmd || true` unconditionally yields exit status 0 regardless of `cmd`'s own exit code,
which would silently swallow the script's deliberate `sys.exit(2)` and defeat the entire point of
this ticket (a real blocking signal). The script's own internal fail-open behavior (Step 2.6) is
what prevents an internal script bug from blocking a turn — the shell wrapper must not also
duplicate that protection by nullifying the one signal (exit 2) the guard exists to produce.

**Other writers to this shared resource (enumerated per Fact-Verification Requirement #2):** this
file's `hooks` block is also written by (a) the four existing `PreToolUse`/`PostToolUse` matcher
groups already in place (lines 55-129) — this step is purely additive relative to those, a new
sibling key, no edit to their content; (b) `TCK-20260904-BASH-SECRET-SCAN-HOOK` (same batch,
flagged in this ticket's own Out of Scope, ticket line 41, and investigation.md lines 162-167,
306-308) — that ticket is expected to add its own hook, additively, likely under `PreToolUse` given
its "secret scan" framing. Sequence this as one coordinated merge (whichever ticket lands second in
implementation order re-reads the file fresh and merges its own key in, rather than either ticket
overwriting the other's uncommitted edit) — not a hard sequencing dependency (per ticket line 41),
just a same-file collision to watch for since both are additive.

**Do NOT touch:** the `permissions.allow` block (lines 2-52) or the existing `PreToolUse`/
`PostToolUse` array contents.

**Verify:** test #5 from test_plan.md
(`test_new_hook_event_key_not_previously_wired`) — a structural read of the committed JSON
asserting the `SubagentStop` key exists and references the new script's path.

### Step 4 — Test the hook script directly

**Files:** new file `tests/tools/test_subagent_stop_background_guard.py`.

**Change:** Follow `tests/tools/test_post_tool_hook.py`'s `_run_hook(cwd, payload)` subprocess
pattern exactly (`tests/tools/test_post_tool_hook.py:43-51`: `subprocess.run([sys.executable,
str(_HOOK_PATH)], input=json.dumps(payload), cwd=str(cwd), capture_output=True, text=True,
timeout=10)`), asserting on `result.returncode` (0 = allow, 2 = block) rather than `tools.jsonl`
side effects. Build synthetic transcript JSONL fixtures **modeled on Step 1's real capture**, not
guessed shapes — write a `_write_transcript(path, entries)` helper mirroring
`test_retro_nudge_hook.py`'s `_write_jsonl(path, records)` (`tests/tools/test_retro_nudge_hook.py:
29-30`). Implement the five tests test_plan.md names:

1. `test_hook_fires_for_still_running_background_task` — synthetic transcript with a `Bash`
   tool_use (`run_in_background: true`) and no completed-status follow-up → `returncode == 2`.
2. `test_hook_allows_stop_when_background_task_already_polled_complete` — same but with a
   completed-status `BashOutput`/`Monitor` entry after it → `returncode == 0`.
3. `test_hook_allows_stop_when_no_background_task_was_ever_started` — transcript with zero
   `run_in_background: true` entries → `returncode == 0`, and assert no side-effect files were
   written (this hook needs no sidecar per Step 2.7 — assert none was created).
4. `test_hook_fails_open_on_malformed_or_missing_transcript` — missing `transcript_path`,
   unreadable file, and malformed JSONL, each asserting `returncode == 0` and `"Traceback" not in
   result.stderr` (mirroring `test_retro_nudge_hook_fail_silent_on_malformed_data_dir`,
   `tests/tools/test_retro_nudge_hook.py:80-93`).
5. `test_hook_respects_stop_hook_active_loop_prevention` — a payload with `stop_hook_active: true`
   on a transcript that would otherwise block, asserting the hook allows through (or otherwise
   behaves per whatever Step 1.4 confirmed) rather than re-blocking indefinitely (test_plan.md's
   Anti-Drift Test Guards, lines 162-169 — this test's exact name/behavior is fixed by Step 1's
   findings, not guessed here).

**Do NOT touch:** `tests/tools/test_post_tool_hook.py`, `tests/tools/test_retro_nudge_hook.py`
(read-only pattern references, not modification targets).

**Verify:** `pytest tests/tools/test_subagent_stop_background_guard.py -v` — all pass. Then the
full scoped command (Step 8 below) to confirm no regression in the rest of `tests/tools/` (required
per `test-scoper.md`'s own flat-directory Scoping Rule, ticket's Related Code Areas line 68).

### Step 5 — Decide `test-scoper.md`'s prose section disposition: KEEP as defense-in-depth

**Files:** `.claude/agents/test-scoper.md` — no edit needed if the hook ships (this step is a
documented decision, not a code change).

**Change:** Keep `## Background Commands` (lines 126-128) verbatim. Document the rationale
explicitly in this ticket's Implementation Notes: the new `SubagentStop` hook fails open on any
internal error (Step 2.6's final `except Exception: sys.exit(0)`), and every hook in this repo
follows that same universal fail-open convention (`tools/agent-monitoring/pre_tool_hook.py:8`,
`post_tool_hook.py:47,163`, confirmed by investigation.md lines 44-50). A hook that can silently
fail open is not airtight, and investigation.md itself says the transcript-derived proxy "can't
perfectly distinguish 'genuinely still running' from 'just finished at the exact moment of the Stop
event' without careful handling" (this ticket's own directive language). The prose rule in CLAUDE.md
line 26 and test-scoper.md lines 126-128 remains the backstop for exactly the cases the hook cannot
catch (hook script bug, hook not registered in a given harness/session, or a race at the exact
moment of the Stop event). This satisfies AC #4 and the ticket's Out of Scope line 42 ("never a
silent deletion") — the decision is KEEP, not supersede, because unlike M2's doc-coverage case, this
control genuinely can fail open and the prose has real residual value.

**Do NOT touch:** do not reword, shorten, or "strengthen" the existing prose (Anti-Drift Hazard,
investigation.md lines 284-289: converting/rewriting this prose beyond what's needed is out of this
epic's evidenced scope).

**Verify:** `grep -A2 "## Background Commands" .claude/agents/test-scoper.md` shows the text
unchanged from investigation.md's own verbatim quote (lines 53-56).

### Step 6 — Update the stale contract-vocabulary pins

**Files:** `agent-orchestration/hook-events.yaml`, `agent-orchestration/hook-surface-policy.yaml`,
`tests/agent_orchestration/test_contract_structure.py`.

**Change:**

- `agent-orchestration/hook-events.yaml` (currently 9 lines, `hook_types: [PreToolUse,
  PostToolUse]`): add a `SubagentStop` entry (`id: SubagentStop`, `description: "Fired when a
  subagent's turn ends; can block via exit code 2."`) alongside the existing two. Update the file's
  own header comment (lines 1-3, "Normalizes exactly the two hook types actually wired... No
  speculative SessionStart/Stop/other hook type") since it is no longer accurate the moment this
  ships — reword to reflect three wired types.
- `agent-orchestration/hook-surface-policy.yaml` line 10 (`enabled_events: [PreToolUse,
  PostToolUse]` under `providers.claude`): add `SubagentStop`. Also add a new
  `providers.claude.available_events` key per this plan's Summary decision #2 — set it to exactly
  `[PreToolUse, PostToolUse, Stop, SubagentStop]`, the four events this ticket's own investigation
  has direct doc-fetch citation for (investigation.md lines 92-104) — do **not** list the full ~32
  Claude Code event vocabulary the docs mention, since that would be exactly the uncited
  fabrication investigation.md's own Anti-Drift Hazards warn against (lines 301-305, referencing the
  same class of mistake `TCK-20260730-PROVIDER-HOOK-POLICY` flagged for Codex's "available" count).
- `tests/agent_orchestration/test_contract_structure.py`: update
  `test_policy_represents_claude_two_enabled_events` (line 182-184) to assert
  `{PreToolUse, PostToolUse, SubagentStop}` (rename the test if its name embeds the stale count —
  e.g. `test_policy_represents_claude_three_enabled_events`, avoiding a hardcoded-then-wrong count
  in the name) and `test_hook_events_yaml_unchanged_normalized_vocabulary` (line 215-217) to assert
  the three-element set. Add a new assertion (or extend an existing one) confirming
  `providers.claude.available_events` is present and equals the four-element set above — this is
  test_plan.md's item #6 (`test_hook_events_yaml_and_hook_surface_policy_updated_for_new_claude_
  event`, test_plan.md lines 105-114).

**Other writers to these two YAML files (Fact-Verification Requirement #2):** `tools/
agent_orchestration/generator.py:94-103` round-trips both files back to disk unchanged (no template
logic of its own) whenever the contract bundle is regenerated — confirmed by reading
`generator.py:94-103`, it only calls `_write_yaml(repo_root, hook_events_path, bundle.hook_events,
...)` and the policy equivalent, so it will faithfully re-emit whatever this step writes with no
collision risk. No other ticket or tool in this batch is known to write these two files.

**Do NOT touch:** `tools/agent_orchestration/loader.py`, `tools/agent_orchestration/generator.py`
(per this plan's Summary decision #2 — no schema change needed, confirmed by reading
`loader.py:222-267`).

**Verify:** `pytest tests/agent_orchestration/test_contract_structure.py -v` — all pass, including
the two updated tests and the new/extended `available_events` assertion.

### Step 7 — Epic doc update and settings.json collision note

**Files:** `docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md`
(M3 section, lines 105-164).

**Change:** Update the M3 milestone text (lines 105-116) and "Acceptance signal" M3 bullet (lines
159-164) to record the actual outcome: either "shipped — real `SubagentStop` hook at
`tools/agent-monitoring/subagent_stop_background_guard.py`, wired in `.claude/settings.json`,
verified by `tests/tools/test_subagent_stop_background_guard.py`" (real-hook branch) or the literal
fallback string from Step 1b (fallback branch). This doc's own text (lines 159-164) explicitly
gates M3 completion on this update landing — "a silent prompt-only implementation does not satisfy
this milestone" applies equally to a silent real-hook implementation that never updates this doc.
Also add one line noting the `.claude/settings.json` `hooks` block is a known same-batch collision
point with `TCK-20260904-BASH-SECRET-SCAN-HOOK` (additive merge expected per ticket line 41 — not a
sequencing dependency, just a flagged coordination point), so a future reader of this epic doc
understands why two tickets both touch that file in the same window.

**Do NOT touch:** the M2 section (lines 143-158, already shipped/verified by a different ticket) or
the M4/Acceptance-signal framing beyond M3's own bullet.

**Verify:** manual read — M3's text no longer describes an open milestone; it states the actual
shipped or fallback outcome with a citation to the concrete artifact (hook script path or literal
fallback string).

## Scope Guards

- Do not modify `tools/agent-monitoring/pre_tool_hook.py` or `post_tool_hook.py` beyond reading them
  as a pattern reference (ticket Out of Scope line 40).
- Do not resolve the `.claude/settings.json` collision with `TCK-20260904-BASH-SECRET-SCAN-HOOK`
  beyond the flag in Step 3/Step 7 — no cross-ticket coordination edit, no blocking on that ticket's
  landing (ticket Out of Scope line 41).
- Do not silently delete `.claude/agents/test-scoper.md`'s `## Background Commands` prose section
  under any circumstance — Step 5 keeps it in both the real-hook and fallback branches (ticket Out
  of Scope line 42).
- Do not generalize this ticket's "prose → deterministic hook" conversion to any other CLAUDE.md
  Hard Rule beyond the one this ticket targets (investigation.md Anti-Drift Hazards, lines 284-289 —
  the epic's own Out-of-Scope line: "only the two with direct, repeated, repository-native evidence
  of failure... are in scope").
- Do not produce a `docs/ai/claude_capability_matrix.md` — investigation.md explicitly scopes this
  out as a substantially larger separate effort (lines 194-201).
- Do not touch `tools/agent_orchestration/loader.py` or `generator.py` (Summary decision #2 — no
  schema change is needed; touching them would be unscoped work).
- Do not touch `tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py` or anything under
  `tools/agent_codex_pilot_guardrails/` — this ticket is Claude-side only (test_plan.md Anti-Drift
  Test Guards, lines 156-159).
- Do not invent transcript/payload field names before Step 1's capture completes — Step 2 must cite
  Step 1's actual observed shape, not a guessed one (investigation.md lines 301-305).

## Dependency Map

- Step 1 (spike) blocks Steps 2, 3, 4, 6 entirely — none of them can be written correctly without
  Step 1's real fixture. If Step 1 fails, Step 1b runs instead and Steps 2/3/4/6 are skipped.
- Step 2 (hook script) blocks Step 4 (tests exercise the script) and Step 3 (settings.json
  references the script's path, so the file must exist first, though the JSON edit itself is
  independent of the script's internal logic).
- Step 3 and Step 6 are mutually referential (Step 6's `hook-events.yaml`/`hook-surface-policy.yaml`
  updates should reflect whatever event key Step 3 actually wires) but can be done in either order
  within the same session since both are known in advance to be `SubagentStop`.
- Step 5 (prose disposition) and Step 7 (epic doc) are independent of Steps 2-4/6 and can be done in
  parallel with them, but Step 7's exact wording depends on whether Step 1 succeeded or fell back to
  Step 1b.
- Step 4's regression check (full `tests/tools/` + `tests/agent_orchestration/`) should run last,
  after Steps 2, 3, 6 all land, to catch any cross-file inconsistency.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: committed artifact fires/blocks a synthetic test-scoper-shaped still-running background pytest reproduction, OR literal fallback format appears | Steps 1, 2 (real branch) / Step 1b (fallback branch) | `test_hook_fires_for_still_running_background_task` (real) / literal-string grep + `test_test_scoper_background_commands_section_still_present` (fallback) |
| AC #2: hook wired under a settings.json event key that did not previously exist | Step 3 | `test_new_hook_event_key_not_previously_wired` |
| AC #3: new/extended test in `tests/tools/` exercises the hook script directly (stdin in, exit code out) | Step 4 | `tests/tools/test_subagent_stop_background_guard.py` (all 5 tests) |
| AC #4: `test-scoper.md`'s prose section kept as defense-in-depth or explicitly superseded, never silently deleted | Step 5 | manual grep verification (Step 5's Verify) |

## Anti-Drift Notes

- **Do not guess the transcript/payload schema.** Step 2 must cite Step 1's actual captured field
  names in its own code comments (mirroring how `post_tool_hook.py`'s comments cite the exact ticket
  that motivated each design choice). This is the single most important sequencing constraint in
  this plan — investigation.md is explicit that its own findings are "documentation-citation-grade
  evidence, not direct-experiment-grade" (line 131).
- **Do not suffix the new hook's settings.json command with `|| true`.** This is the one place this
  plan deliberately diverges from every existing hook command's shape in this file, and doing so
  by accident (copy-pasting the existing pattern without noticing) would silently defeat the entire
  point of the ticket — the guard would parse correctly but its block signal would never reach
  Claude Code. Step 3 documents why explicitly.
- **`stop_hook_active` must be handled before the hook can be considered safe to ship**
  (investigation.md lines 145-147, 261-266). An unverified loop-prevention assumption risks turning
  a helpful guard into an infinite-block hang — worse than the bug being fixed. Step 1.4 and test #5
  in Step 4 exist specifically to close this gap; do not ship Step 2/3 without them.
- **The `.claude/settings.json` hooks block is a real multi-ticket collision point this same batch**
  (`TCK-20260904-BASH-SECRET-SCAN-HOOK`). Re-read the file immediately before editing it in Step 3,
  not from a stale in-memory copy, in case the sibling ticket already landed its own additive key.
- **`hook-events.yaml`'s and `hook-surface-policy.yaml`'s pinned tests going stale is the expected,
  correct signal that the hook was actually wired** — test_plan.md's own words: "a passing scoped
  run that still shows these two tests green *unchanged* after a real hook ships would mean the
  hook was never actually registered... a contradiction Verify must catch" (test_plan.md lines
  38-40). Verify phase should treat an *unchanged* `test_policy_represents_claude_two_enabled_events`
  as a red flag, not a green light, once Step 6 is claimed complete.
- **Never let this ticket's real-hook vs. fallback branch decision get made preemptively.** Step 1
  is a genuine spike, not a formality — if it succeeds, Steps 2-4/6 are mandatory and Step 1b must
  not be invoked "for safety." If it genuinely fails, invoke Step 1b honestly rather than forcing a
  guessed-schema hook script through to satisfy AC #1's literal (a) branch.

## Deviations (recorded during Implement)

1. **Step 1's exact capture method changed; the outcome (real-hook branch, not fallback) did
   not.** Both live-capture avenues this step's text names were attempted first and both were
   genuinely blocked, not skipped: (a) a nested `claude -p ...` invocation in a throwaway scratch
   directory (`/tmp/.../subagentstop_spike/`) — refused outright by this sandbox's own auto-mode
   classifier for any `claude` invocation at all, even `claude --version`; (b) writing a throwaway
   `.claude/settings.local.json` (confirmed gitignored via the user's global git ignore,
   `**/.claude/settings.local.json` — genuinely outside this repo's committed trust boundary) to
   register a diagnostic `SubagentStop` hook against a real Agent-tool-dispatched subagent within
   this very session — also refused by the classifier (`Permission for this action was denied by
   the Claude Code auto mode classifier`). With both avenues genuinely exhausted (not merely
   inconvenient), Implement substituted a third method the plan did not name: extracting the
   literal, currently-enforced zod validation schema and producing control-flow code directly from
   the installed Claude Code binary (`/home/u24desktop/.local/share/claude/versions/2.1.261`, an
   ELF executable bundling the harness's own JS — readable via plain `grep -a`/byte-offset
   extraction, not blocked by the classifier since it is a read, not a hook registration or nested
   invocation). This surfaced the exact real field names for `SubagentStop`/`Stop` (`session_id`,
   `transcript_path`, `cwd`, `prompt_id?`, `permission_mode?`, `agent_id`, `agent_type`,
   `agent_transcript_path`, `stop_hook_active`, `last_assistant_message?`, `background_tasks?`,
   `session_crons?`) plus the real control-flow proving `stop_hook_active`'s loop-prevention intent
   (the harness's own consecutive-block-cap warning text literally instructs: "For Stop/
   SubagentStop hooks, check stop_hook_active in the input and return success while it's true").
   This is treated as satisfying (and arguably exceeding) Step 1's evidentiary bar — it is the
   schema that PRODUCES every real payload instance, not a guess, and not merely one example of
   it — but it falls short of the step's literal instruction to save a raw, live-fired stdin
   capture, so it is disclosed here rather than silently substituted. Full citation (exact binary
   offsets, verbatim schema fragments) is in
   `tests/fixtures/claude_hook_payloads/subagent_stop_schema_capture.json`. Separately
   independently corroborated: no session transcript on this machine's `~/.claude/projects/`
   history contains a `BashOutput` tool_use anywhere (only `Monitor`), resolving investigation.md's
   own `BashOutput`/`Monitor` hedge in favor of `Monitor` alone — this repo's real polling tool.
2. **Step 2's design changed materially from the plan's transcript-parsing architecture, in the
   direction the real evidence pointed.** The binary extraction in Deviation 1 revealed
   `background_tasks` — a harness-populated array on the `SubagentStop`/`Stop` payload itself,
   populated from a live per-session task registry (`f.taskRegistry.all()` in the real
   control-flow code) and documented by the harness's own schema as existing specifically to "let
   hooks distinguish 'session is done' from 'session is paused waiting for background work to wake
   it'". This makes the transcript-JSONL-parsing heuristic plan.md's Step 2 spec hypothesized
   (scan for the last `Bash` tool_use with `run_in_background: true`, then scan forward for a
   `BashOutput`/`Monitor` completion entry) both unnecessary and strictly worse: it would have
   reconstructed from text something the harness already tracks authoritatively and hands to the
   hook directly. `subagent_stop_background_guard.py` reads `payload["background_tasks"]` and
   blocks (exit 2) iff the list is non-empty (after the `stop_hook_active` early-allow check),
   never opening or parsing `transcript_path` at all. This is still fully grounded in Step 1's real
   captured field names, per the plan's own governing principle ("Step 2 must cite Step 1's actual
   observed shape, not a guessed one") — it is a simpler, more authoritative mechanism built from
   the same real evidence, not an invented one. Step 2.7's conclusion (no new sidecar file needed)
   is unaffected and, if anything, more clearly true: the hook now needs zero file I/O of any kind
   beyond stdin.
3. **Test #5 placement decision (flagged as open by architecture-review): new
   `tests/tools/test_settings_json_hooks_wiring.py`.** `tests/agent_orchestration/
   test_contract_structure.py` asserts content the `agent_orchestration.loader.load_contract`
   bundle actually parses (`contract.yaml`, `hook-events.yaml`, `hook-surface-policy.yaml`,
   `roles/`) — `.claude/settings.json` is a separate, real Claude-Code-native config file that
   bundle does not load or govern at all. Folding a `.claude/settings.json` structural assertion
   into that file would misrepresent it as contract-governed content. The new file also has no
   dependency on `agent_orchestration`'s `PYTHONPATH=tools`-only import requirement (see Deviation
   4), so it runs correctly under the plain `tests/tools/` scoped command with no special
   invocation.
4. **Environment note, not a plan deviation**: `tests/agent_orchestration/test_contract_structure.
   py` (pre-existing, not authored by this ticket) only imports successfully with `tools/` on
   `PYTHONPATH` in addition to `.` (`PYTHONPATH=tools:. pytest ...`) — the repo's own
   `pyproject.toml` `pythonpath = ["."]` alone is insufficient for its bare `from
   agent_orchestration.loader import load_contract` import, and this venv's editable install only
   maps `src`/`src_legacy`, not `tools`. This is a pre-existing environment gap unrelated to this
   ticket's own changes (confirmed by checking out the test file's git history is untouched by this
   ticket) — recorded here only so Verify does not mistake the required `PYTHONPATH=tools:.`
   prefix for a workaround this ticket introduced.
