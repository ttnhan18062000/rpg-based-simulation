---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION
artifact_type: investigation
tags: [agent-monitoring, data-quality, root-cause, bug]
---

# Investigation — TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION

## Current Behavior

**Root cause, confirmed by direct read of `.claude/workflows/implement-ticket.js` (1300 lines,
read in full):**

1. `.claude/workflows/implement-ticket.js:200` — `const events = []`. This is a plain in-memory
   JS array, re-initialized to empty **every time the workflow script is invoked** (every session).
   Nothing before this line reads any persisted state (`agent-monitoring/events.jsonl` or
   `agent-monitoring/tools.jsonl`) for the `run_id` being resumed.

2. `implement-ticket.js:207-218` — `pushEvent`:
   ```js
   const pushEvent = (phaseLabel, agentName, status, summary, ts, toolCallCount, reasonCode) => {
     events.push({
       seq: events.length + 1,
       ...
   ```
   `seq` is derived purely from `events.length`, i.e. purely from this session's own call count.
   Every one of the 11 `pushEvent(...)` call sites (Scope through Finalize) inherits this.

3. `implement-ticket.js:229-236` — `writeSidecar(seq, phase, agent)` takes `seq` as a caller-supplied
   parameter. All 10 call sites pass the identical expression `events.length + 1` (confirmed by
   `tests/tools/test_current_run_sidecar_orchestrator.py:99`'s own regex assertion:
   `await writeSidecar\(events\.length \+ 1, '[^']+', '[^']+'\)` matched exactly 10 times):
   Investigate (`:427`), Plan (`:468`), Review (`:549`), Implement (`:618`),
   Architecture-Verify (`:734`), Test (`:795`), Parity (`:944`), Security-Review (`:1036`),
   Verify (`:1099`), Finalize (`:1153`).

4. `implement-ticket.js:44-53` — the Scope-phase resume branch (the one named explicitly in the
   ticket prompt as the site to inspect):
   ```js
   if (ticketId) {
     await bash(
       `python3 -c "
   import json, sys
   open('.claude/current_run', 'w').write(json.dumps({'run_id': sys.argv[1], 'seq': 1, 'phase': 'Scope', 'agent': 'ticket-scoper'}))
   " "${ticketId}" 2>/dev/null || true`
     )
   } else {
     await bash(`printf '{}' > .claude/current_run 2>/dev/null || true`)
   }
   ```
   The literal `'seq': 1` on the line above is hardcoded — it does not read `.claude/current_run`'s
   prior contents, nor any persisted `agent-monitoring/*.jsonl` record, before writing. This is the
   very first sidecar write of a resumed session, and it is unconditionally 1 regardless of whether
   this `run_id` already has phases 1-6 recorded from a prior (pre-pause) session.

**Net effect**: two independent restart-at-1 points, both keyed only off in-session state
(`events.length` / the hardcoded literal), with zero lookup against this `run_id`'s prior history in
`agent-monitoring/events.jsonl` or `agent-monitoring/tools.jsonl`. A resumed session's `seq` values
1, 2, 3... are therefore guaranteed to collide with the pre-pause session's `seq` values 1, 2, 3...
for as many phases as both sessions ran, exactly reproducing the `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION`
table in the ticket (`seq=2` ground truth 61 tool calls attributed to both `Investigate` in session 1
and `Implement` in session 2, etc.) — `tools.jsonl` groups purely by `(run_id, seq)`
(`tools/agent-monitoring/post_tool_hook.py:75-76`, `tools/agent-monitoring/record_events.py`'s
`compute_tool_stats()` at `:34-65` reading `TOOLS_FILE` grouped by `(run_id, seq)` only), so the hook
and the aggregator have no way to distinguish which physical session produced a given `(run_id, seq)`
pair.

**This confirms the ticket's own framing exactly**: the bug is not in `writeSidecar` itself (it
faithfully writes whatever `seq` it's given) and not in the hook (`post_tool_hook.py:53-63` faithfully
reads whatever the sidecar currently says) — it is that nothing anywhere in the resume path computes
a `seq` value that is aware of a prior session's history for this `run_id`. This is a **third**,
genuinely distinct gap from the two `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` closed
(Scope-phase sidecar coverage gap; `writeMonitoring` self-pollution) — that ticket's fixes are both
still correctly in place (verified: `if (ticketId) {...} else {...}` block exists exactly as that
ticket left it; `writeMonitoring`'s Step 0 sidecar-clear precedes Steps 1-3, confirmed at
`implement-ticket.js:294-304`) — they just never addressed cross-session `seq` continuity because
that ticket explicitly ruled out concurrency/cross-session causes as out of scope for its own bug
(see `tickets/done/TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION.md`'s Implementation Notes:
"Root cause correction... the initial hypothesis (concurrent/overlapping workflow runs... resolved to
deterministic single-session bugs").

**Which candidate approach is implementable:**

The plan doc (`docs/plans/idea_agent_monitoring_pause_resume_seq_collision.md`) names two candidates.
Given the actual code structure read above:

- **Candidate 1 (max-seq continuation) is directly implementable and minimal.** Every seq-producing
  site in the file funnels through exactly one expression shape, `events.length + 1`, used
  identically at all 10 `writeSidecar(...)` call sites and inside `pushEvent`'s one definition. A
  single `seqOffset` value, computed once (via a new orchestrator-run `bash()` lookup, analogous in
  shape to the existing `resolveScopeTicketLocation()` helper at `implement-ticket.js:257-263`,
  which already reads `tools/agent-monitoring/scope_ticket_relocate.py` via a MARKER-prefixed JSON
  `bash()` call before the Scope agent() call — precedent confirmed by direct read of that function
  and its backing script), added into `pushEvent`'s `seq: events.length + 1` expression and every
  `writeSidecar(events.length + 1, ...)` call site, would make the whole in-session numbering
  continue past whatever this `run_id` already has in `agent-monitoring/events.jsonl`/`tools.jsonl`.
  The Scope-phase resume branch's hardcoded `'seq': 1` literal (line 48) would need to become
  `seqOffset + 1` (the resume branch is exactly where `seqOffset` must first be computed, since
  `ticketId` — the resume `run_id` — is known there and nowhere earlier).
  `seqOffset` is `0` on the brand-new-ticket branch (no prior `run_id` history exists to look up),
  preserving today's exact behavior for non-resumed runs.

- **Candidate 2 (unique per-invocation token instead of int `seq`) is technically possible but not
  minimal — much larger blast radius.** `seq` as an integer is load-bearing in >6 places beyond
  `implement-ticket.js` itself: `tools/agent-monitoring/post_tool_hook.py:56` writes it verbatim from
  the sidecar; `record_events.py`'s `REQUIRED` set (`seq` is a required int field, tested by
  `tests/tools/test_current_run_sidecar_orchestrator.py:295-296`'s
  `test_record_events_required_fields_unchanged`) and its `compute_tool_stats()` grouping key;
  `validate.py`'s `compute_tool_count_drift_report()` grouping key (`tools.py:137-155`); the
  `DONE_SCHEMA`/event schema's `seq: int` contract; and `docs/agent-monitoring/schema.md`'s
  documented `"seq | int | No | 1-based call order..."` field description and Join Example. Changing
  the attribution key's *type* would touch all of these, versus Candidate 1's single computed offset
  touching only `implement-ticket.js`. Candidate 1 is the minimal, safe fix given the real code
  structure — Candidate 2 is not recommended unless Candidate 1 is found insufficient during Plan.

**Where the lookup should read from**: `agent-monitoring/events.jsonl` (not `tools.jsonl`) is the
correct source — it already has exactly one row per `(run_id, seq)` pair (one per agent call), so
`max(seq where run_id == ticketId)` is a direct one-pass scan, mirroring
`compute_tool_count_drift_report`'s own existing `actual_counts[(run_id, seq)] += 1` pattern
(`validate.py:137-142`) for how this codebase already reads that file. `tools.jsonl` also carries
`seq` (FK to `events.seq`, `docs/agent-monitoring/schema.md:244`) and could serve as a second/fallback
source if `events.jsonl`'s write for the pre-pause session's last phase is somehow missing, but
`events.jsonl` is the authoritative 1:1 record and should be primary.

## Mechanics / Engine Constraints

N/A — this is agent-tooling/observability infrastructure (`.claude/workflows/`,
`tools/agent-monitoring/`), not simulation logic. No `docs/mechanics/` chapter or `docs/engine/`
contract governs this behavior.

## Parity Ledger Overlap

N/A — `docs/parity_ledger/` tracks simulation-mechanics parity (combat, economy, strategic cognition,
etc.) against the Mechanics Bible. `agent-monitoring/` is orchestration/observability tooling, outside
that ledger's subsystem list (`substrate`, `combat_movement`, `strategic_cognition`, `town_resource`,
`progression`, `social_narrative`, `world_dynamics`, `infrastructure`). No parity ledger entry ID
applies to this ticket's scope. (Confirmed: `implementation.parity_subsystems` in the Implement-phase
schema has no category matching agent-monitoring internals; the Parity phase's own skip-eligibility
check — `parityNoSrcChange = implementation.files_changed.every(f => !f.startsWith('src/'))` — will
almost certainly evaluate true for this ticket's expected file set, since the changes land in
`.claude/workflows/implement-ticket.js` and `tools/agent-monitoring/`, not `src/`.)

## Prior Work

- **`tickets/done/TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION.md`** — direct precedent, same
  failure class (silent `tools.jsonl` attribution collision corrupting `tool_call_count`/
  `cost_proxy_score`), same fix location (`implement-ticket.js`), same validation-tooling home
  (`tools/agent-monitoring/validate.py`). Its Implementation Notes document that the *original*
  concurrency hypothesis for that ticket was disproven — both of its real mechanisms were
  deterministic single-session bugs. This ticket's mechanism is different: it fires only across two
  genuinely separate workflow invocations sharing one `run_id`, a case that ticket's own
  investigation explicitly never covered (stated in both that ticket's Implementation Notes and this
  ticket's own Request Summary). Its `compute_tool_count_drift_report()` (`validate.py:124-167`) is
  the natural home for a new, distinguishing check per this ticket's Scope item 2 — it currently
  detects *that* `recorded != actual` for a `(run_id, seq)` pair, but has no logic to detect *why*
  (multi-invocation collision vs. any other future cause).
- **`docs/plans/idea_agent_monitoring_pause_resume_seq_collision.md`** — the plan doc this ticket
  implements. Already contains the full root-cause table and both candidate approaches (reproduced
  and evaluated above). Its "Natural Integration Points" table names exactly the three touch points
  this investigation confirms by direct code read: `implement-ticket.js`'s Scope-phase sidecar write,
  `validate.py`'s `compute_tool_count_drift_report()`, and `docs/agent-monitoring/schema.md`'s "How
  tool calls are attributed to agent events" section.
- **`tests/tools/test_current_run_sidecar_orchestrator.py`** — existing regression suite for the
  sidecar mechanism, static/raw-source-text-parsing style (`Path.read_text()` against
  `implement-ticket.js`, never executes the JS). Contains
  `test_scope_phase_has_sidecar_coverage` (asserts the exact `if (ticketId) { ... }` / hardcoded
  `'seq': 1` text block this ticket must change — **this existing test will need updating**, since it
  currently asserts the literal string `"'seq': 1,"` is present; a resume-aware fix that replaces the
  literal `1` with a computed `seqOffset + 1` expression will break this assertion unless the test is
  updated in the same change) and `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded`
  (asserts `writeSidecar`'s argv-quoting shape — any change to `writeSidecar`'s signature to add an
  offset parameter must preserve this shape or update this test alongside it).
- **`tickets/done/TCK-20260710-CURRENT-RUN-SIDECAR-BASH.md`** (referenced, not re-read in full —
  cited by both the sibling ticket and the sidecar test module docstring) — established the
  orchestrator-side `writeSidecar(seq)` pattern this ticket must extend, not replace.

## Risks and Open Questions

- **Open question carried from the plan doc, not resolved here (per this role's mandate not to
  collapse investigation into an answer the evidence doesn't support):** is `max(seq) + 1` sufficient
  for a *third* resume of the same ticket, or could the lookup itself race with a stale sidecar read
  if two sessions were ever truly concurrent? The sibling ticket's investigation already established
  (via direct code read, not speculation) that true concurrent/overlapping sessions on this `run_id`
  have never been observed in the real corpus — pause/resume is sequential by construction (a human
  walks away and later restarts a session; the prior session is not still running). A max-seq lookup
  performed once at Scope-phase start, before this session's own writes begin, is safe under that
  sequential-resume assumption. It would only be unsafe if two resumed sessions for the *same*
  `run_id` were started concurrently — not observed, and arguably out of scope to defend against
  speculatively (this ticket's own Out of Scope section excludes backfilling/redesign work beyond
  prevention).
- **Whether `implement-epic`'s per-child dispatch has an analogous issue is explicitly flagged as not
  yet checked** by both the ticket and the plan doc. Per `docs/agent-monitoring/schema.md:206-211`
  ("Neither `create-tickets` nor `implement-epic` registers a `.claude/current_run` sidecar per agent
  call... `tool_call_count` is always absent"), `implement-epic.js` never writes `seq`-keyed sidecar
  values at all — it has no `writeSidecar`/`pushEvent`-with-`events.length`-style mechanism to
  inherit this bug in the first place. This strongly suggests the answer is "not applicable" (no
  mechanism to collide), but this investigation did not read `implement-epic.js` directly to confirm;
  flagging as open rather than asserting.
- **Test-file collateral**: `test_scope_phase_has_sidecar_coverage` (see Prior Work above) asserts a
  literal `'seq': 1` string that a correct fix will necessarily change. This is expected collateral,
  not a gap — call it out explicitly in test_plan.md so Implement doesn't treat the resulting test
  failure as a regression to work around rather than a test to update.
- **Where exactly to compute `seqOffset`** (inline `python3 -c` one-liner vs. a new named function in
  a script file, mirroring `resolveScopeTicketLocation()`/`scope_ticket_relocate.py`'s shape) is a
  Plan-phase implementation-shape decision, not resolved here — both are structurally available given
  the file's existing conventions (compare the small inline `tagCheckOutput`/`p0ScanOutput` one-liners
  vs. the dedicated `scope_ticket_relocate.py` module). Given the lookup needs its own unit tests
  (per this ticket's AC) and mirrors `compute_tool_count_drift_report`'s existing grouping logic, a
  named, importable function is likely preferable to an inline one-liner — but this is a
  recommendation for Plan, not a decision made here.

## Anti-Drift Hazards

- **Do not touch `writeMonitoring`'s own sidecar-clear-at-Step-0 ordering** (`implement-ticket.js:294-304`)
  — that is the sibling ticket's fix for a different, already-closed mechanism. This ticket's fix is
  additive (an offset applied at the point `seq` is computed), not a reordering of existing steps.
- **Do not change `writeSidecar`'s existing argv-quoting shape** (`"${tid}" "${seq}" "${phase}" "${agent}"`,
  individually quoted, never JSON-embedded — `implement-ticket.js:230-235`) when adding offset
  awareness. `test_tid_and_seq_and_phase_and_agent_passed_as_argv_not_json_embedded` guards this
  exactly; if `writeSidecar` gains a new parameter, keep the quoting convention identical for the
  existing four.
- **Do not widen this fix into Candidate 2** (unique per-invocation token replacing int `seq`) without
  a fresh Plan-phase decision — it touches `record_events.py`'s `REQUIRED` set, `tools.jsonl`'s
  documented schema, and `validate.py`'s grouping key, none of which this ticket's Scope calls for.
  `test_record_events_required_fields_unchanged` (`tests/tools/test_current_run_sidecar_orchestrator.py:295-296`)
  will catch an accidental `REQUIRED` set change.
- **Do not backfill historical `tools.jsonl`/`events.jsonl` records** for the 8 already-collided
  `run_id`s named in the ticket — Out of Scope, same append-only precedent as the sibling ticket.
  Prevention-only.
- **Do not fold in the wall-clock `duration_s` pause/resume contamination fix**
  (`docs/plans/idea_agent_monitoring_active_duration.md`) — explicitly named as Out of Scope in the
  ticket; different field, different consumer, deliberately kept as a separate ticket.
- **`seqOffset` must be `0`, not `null`/`undefined`, on the brand-new-ticket branch** (the `else`
  branch at `implement-ticket.js:51-53`) — there is no `run_id` to look up yet, and the numeric
  arithmetic (`events.length + 1 + seqOffset`) must not silently become `NaN` for every non-resumed
  run, which is the overwhelmingly common path and must be provably unaffected by this change.
