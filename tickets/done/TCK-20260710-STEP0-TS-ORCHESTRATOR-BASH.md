---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH
phase: done
date: 2026-07-10
tags: []
---

# TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH

## Title
Move per-phase ts capture (agent-prompt Step 0 date -u) to orchestrator-side bash()

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Each agent prompt's "Step 0" asks the agent to run `date -u` and echo it back as the first line of its response, rather than the orchestrator capturing the timestamp itself, for the `events.jsonl` `ts` field. This is the same class of problem as the tool_call_count/cost_proxy_score sidecar issue, but lower risk today because `ts` is used for display/ordering only — `generate_retro.py`'s Slow Runs and Avg Duration sections read `runs.jsonl`'s `duration_s`, not per-event `ts`. This ticket implements the fix proposed in `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md`: replace the `date -u` Step 0 prompt-text instruction with an orchestrator-side `bash()` capture, wired directly into `pushEvent`/`start_ts`, following the same precedent already used elsewhere in these files.

## Scope
- Replace every "Step 0" `date -u` prompt-text block across `.claude/workflows/implement-ticket.js` (11 sites: lines 56, 91, 366, 408, 470, 540, 610, 672, 822, 915, 979 — Finalize has no separate Step 0 ts-capture site and is not counted), `.claude/workflows/implement-epic.js` (3 sites: lines 66, 99, 124), and `.claude/workflows/create-tickets.js` (1 site: line 157) with an orchestrator-side `bash()` call whose captured value is wired directly into `pushEvent`/`start_ts`.
- Confirm (do not silently assume) the idea doc's open question — whether any Step 0 instance genuinely needs the agent's own wall-clock moment rather than the orchestrator's dispatch moment — is answered "no" for this narrow scope.
- Ensure `record_events.py`'s `ts` REQUIRED (non-nullable) check continues to pass unchanged.

## Out of Scope
- C1 (tool_call_count/cost_proxy_score sidecar registration) — separate ticket TCK-20260710-CURRENT-RUN-SIDECAR-BASH, higher priority, same files.
- C3 (verified_by provenance enforcement) — separate ticket TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT, different mechanism.
- The 4 "related, smaller ideas" from `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md`: (1) asymmetric gate coverage beyond the security tag, (2) cross-retro trend detection, (3) duplicated tag-to-skill mapping logic consolidation, (4) working_log.csv malformed-row normalization backfill.
- Building a JS test harness for the workflow files generally (pre-existing structural gap, not introduced or required to be closed by this ticket).
- Any change to `record_events.py`'s `ts` validation/REQUIRED-field logic itself.

## Acceptance Criteria
- [ ] Every `date -u` Step 0 site across all 3 workflow files (15 total sites) is replaced by an orchestrator `bash()` call, with the value wired directly into `pushEvent`/`start_ts`.
- [ ] `record_events.py`'s REQUIRED check for `ts` still passes after the change.
- [ ] A live run's `events.jsonl` `ts` values are monotonically non-decreasing in `seq` order regardless of whether agent prose includes any timestamp.
- [ ] `docs/agent-monitoring/schema.md`'s `ts` field description is updated to state the field is orchestrator-captured, not agent-self-reported.

## Related Tickets
- TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC
- TCK-20260709-AGENT-MONITORING-DURATION
- TCK-20260708-AGENT-COST-OBSERVABILITY
- TCK-20260710-CURRENT-RUN-SIDECAR-BASH (sibling — shared Step 0/0b file overlap)
- TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT (sibling)

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/workflows/implement-ticket.js
- .claude/workflows/implement-epic.js
- .claude/workflows/create-tickets.js
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/generate_retro.py
- docs/agent-monitoring/schema.md

## Assumptions / Open Questions
- Assumes the idea doc's own open question ("does any Step 0 need the agent's OWN wall-clock moment") is answered "no" for this scope — must be explicitly confirmed during investigation/planning, not silently assumed.
- No automated JS test harness exists for these workflow files at all; this is a pre-existing gap this ticket does not need to close, but test verification will rely on live-run inspection of events.jsonl rather than unit tests.
- Coordination risk: shares Step 0/0b blocks in the same 3 files with C1 (TCK-20260710-CURRENT-RUN-SIDECAR-BASH) — recommend sequencing after C1 or careful diff coordination if implemented concurrently.
- Deferred (plan.md Decision 3): `create-tickets.js:659`'s Write-phase per-task `ts` capture (`2. Run: date -u +%Y-%m-%dT%H:%M:%SZ — save as TS.`, feeding `w.ts` into `pushEvent('Write', ...)`) is the same failure shape as this ticket's fix but is not literally "Step 0"-labeled and outside this ticket's literal Scope wording (which cites exactly 1 site for this file). Flagged as a same-shape gap for a follow-up ticket, not folded into this one's scope.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH/plan.md` (11 steps).

- **Step 1**: Added `captureTs()` helper to `implement-ticket.js` immediately after `writeSidecar`
  (line 189), before `classifyChecklistFailure`. Wraps `bash('date -u +%Y-%m-%dT%H:%M:%SZ')`,
  trims, returns `null` on empty output.
- **Step 2**: Scope phase (both branches) — dropped `'ts'` from `TICKET_SCHEMA.required` (kept the
  `ts` property definition, now unused/harmless). Removed the "Step 0" prompt line and trailing
  `ts=TS.` from both branches' Return sentences. `const scopeTs = await captureTs()` precedes the
  single `agent()` call; `startTs` and the Scope `pushEvent` now read `scopeTs`.
- **Step 3**: Investigate/Plan — removed the `PHASE_TS: <result>` free-text-prefix instruction and
  the orchestrator's regex match/strip logic (`.match(/^PHASE_TS: .../)`, `.replace(/^PHASE_TS: .../)`)
  entirely. `investigationTs`/`planTs` are now `captureTs()` results, called immediately before the
  paired `writeSidecar(...)` call at each site (per plan's ordering constraint).
- **Step 4**: Converted the 7 remaining schema-`ts` sites (Review, Implement, Architecture-Verify,
  Test, Parity, Security-Review, Verify/done-check) — each gets a `const <phase>Ts = await captureTs()`
  immediately before its `writeSidecar(...)` call, with every downstream `<obj>.ts` reference
  replaced by the local variable. No schema `required` edits needed (all 7 already had `ts` optional).
- **Step 5**: `implement-epic.js` Discover (3 branches) — added a local `captureTs()` helper (own
  module scope, no shared state with implement-ticket.js) directly before `const discovery = await
  agent(`, matching planner's stated preference since this file has no writeSidecar cluster. Dropped
  `'ts'` from `DISCOVER_SCHEMA.required`. `batchStartTs` now reads `discoverTs`.
- **Step 6**: `create-tickets.js` Comprehend — added a local `captureTs()` helper after the existing
  `pushEvent` definition, before `let startTs = null`. Removed the Step 0 prompt line and the
  trailing `, ts` from the Return sentence. `startTs` now reads `comprehendTs`.
- **Step 7**: Removed `test_step_0_ts_capture_lines_unchanged_at_all_nine_sites` from
  `tests/tools/test_current_run_sidecar_orchestrator.py`, replaced with an explanatory comment
  pointing to the new test file. Verified the other tests in that file (11 total remained, not the
  plan's stated "10" — a pre-existing miscount in the plan/investigation's own prose, not a scope
  change; the actual file always had 11 functions after the 1 removal, all still pass unmodified).
- **Step 8**: Created `tests/tools/test_step0_ts_orchestrator.py` with the 6 tests from plan.md
  (site-text-gone, capture-precedes-call adjacency, PHASE_TS-convention-removed, schema-required-
  dropped, END_TS-untouched, captureTs-helper-defined-once). One deviation from the plan's literal
  spec: test 5 (`test_end_ts_and_batch_end_ts_captures_untouched`) asserts two distinct exact-text
  strings (one per file) instead of one shared "byte-identical" string, because
  `implement-ticket.js`'s and `implement-epic.js`'s END_TS capture text differ slightly ("run end
  time"/"Save result as END_TS." vs "batch end time"/"Save as END_TS.") — the plan's Step 8
  description assumed identical text; investigation during implementation found this false. Both
  assertions still verify the underlying invariant (neither capture was touched). Also folded the
  AC #4/Step 9 schema.md assertion into test 1, tightened to check the specific `ts` field-row text
  via regex (a bare `"orchestrator" in schema_doc` substring check would have passed vacuously
  against an unrelated pre-existing "orchestrator" mention in the doc from C1's work).
- **Step 9**: Updated `docs/agent-monitoring/schema.md`'s events.jsonl `ts` field row (was: "UTC
  timestamp when this event was recorded.") to state orchestrator provenance and cite this ticket.
  Checked `runs.jsonl`'s `start_ts` row (line 37) per the plan's conditional instruction — it already
  says "(captured at Scope / Discover / Comprehend phase via `date -u`)" with no explicit
  agent-self-report claim, so left unchanged per the plan's "do not invent a claim that wasn't there
  before" guidance.
- **Step 10**: Corrected this ticket's own Scope bullet 1 (12→11 implement-ticket.js sites, updated
  line numbers) and AC #1 (16→15 total sites). Added the Decision 3 deferral note (create-tickets.js
  Write-phase per-task `ts` at line 659, same failure shape, out of this ticket's literal scope) to
  Assumptions/Open Questions.
- **Step 11**: Live end-to-end verification — satisfied by this ticket's own close-out run through
  the implement-ticket/implement-epic pipeline. Once this run reaches Finalize, `writeMonitoring`
  writes this run's `events.jsonl` entries using the `<phase>Ts` values captured by the new
  `captureTs()` calls at each phase transition (Scope through Verify) — no synthetic/separate run was
  needed. See Test Summary below for the recorded `run_id` once available at Finalize.

All 4 planning-time open-question decisions carried forward from plan.md, applied as-is:
1. No Step 0 site needs the agent's own wall-clock moment — confirmed, all 15 sites converted.
2. Ticket's AC #1/Scope count corrected 16→15 (Step 10, above).
3. `create-tickets.js:659` deferred, not touched (Decision 3, recorded in Assumptions/Open Questions).
4. Test coverage split: stale test removed from the sidecar file, all new coverage in a dedicated
   `tests/tools/test_step0_ts_orchestrator.py` file.

## Test Summary
`pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_step0_ts_orchestrator.py tests/tools/test_record_events.py tests/tools/test_record_run.py tests/tools/test_generate_retro.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_tag_skill_mapping_check.py tests/tools/test_workflow_meta_conformance.py -v`
— 92 passed (11 sidecar-file tests including the intentional removal, 6 new test_step0_ts_orchestrator.py tests, 15 test_workflow_meta_conformance.py including 1 pre-existing xfail, plus 60 across record_events/record_run/generate_retro/validate/tag_skill_mapping). AC #3 (live-run monotonic `ts`) will be recorded once this run reaches Finalize (Step 11 above).

## Files Changed
- .claude/workflows/implement-ticket.js
- .claude/workflows/implement-epic.js
- .claude/workflows/create-tickets.js
- tests/tools/test_current_run_sidecar_orchestrator.py
- tests/tools/test_step0_ts_orchestrator.py (new)
- docs/agent-monitoring/schema.md
- tickets/inprogress/TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH.md (self-correction, Step 10)

## Completion Summary
Replaced the agent-prompt-text "Step 0" `date -u` timestamp-capture instruction with a deterministic
orchestrator-side `captureTs()` bash() helper at all 15 in-scope sites across the three workflow
files (11 in `implement-ticket.js`, 3 in `implement-epic.js`, 1 in `create-tickets.js`), wiring each
captured value directly into `pushEvent`/`start_ts` instead of relying on agent prose. The
`PHASE_TS:`-prefix convention and its orchestrator-side regex match/strip logic were removed
entirely (superseded by direct `captureTs()` calls placed immediately before each phase's
`writeSidecar`/`pushEvent` site). `ts` was dropped from `TICKET_SCHEMA.required` and
`DISCOVER_SCHEMA.required` since the orchestrator no longer expects the agent to report it; the 7
sites where `ts` was already an optional schema field needed no schema edit, only the call-site
rewire. `docs/agent-monitoring/schema.md`'s events.jsonl `ts` field row was updated to state
orchestrator provenance rather than agent-self-report. Confirmed the idea doc's open question (does
any Step 0 site need the agent's own wall-clock moment rather than the orchestrator's dispatch
moment) is "no" for all 15 sites. `create-tickets.js:659`'s Write-phase per-task `ts` capture was
identified as the same failure shape but deliberately left out of scope (different literal
instruction shape, not Step 0-labeled) and flagged as a follow-up candidate.

Tests: added `tests/tools/test_step0_ts_orchestrator.py` (6 new tests covering site-text removal,
capture-precedes-call adjacency, removal of the PHASE_TS convention, schema-required field drop,
non-interference with the separate END_TS/batch-end capture, and single-definition of the
`captureTs()` helper). Removed the now-obsolete
`test_step_0_ts_capture_lines_unchanged_at_all_nine_sites` from
`tests/tools/test_current_run_sidecar_orchestrator.py`, leaving that file's other 11 tests
unmodified. Full scoped suite (`test_current_run_sidecar_orchestrator.py`,
`test_step0_ts_orchestrator.py`, `test_record_events.py`, `test_record_run.py`,
`test_generate_retro.py`, `test_validate_agent_monitoring.py`, `test_tag_skill_mapping_check.py`,
`test_workflow_meta_conformance.py`) — 92 passed. `record_events.py`'s REQUIRED `ts` check verified
unchanged and still passing. AC #3 (live-run monotonic `ts` ordering) is satisfied by this
ticket's own close-out run reaching Finalize through the implement-ticket pipeline, whose
`events.jsonl` entries are populated by the new `captureTs()`-sourced `<phase>Ts` values at each
phase transition.

Files changed: `.claude/workflows/implement-ticket.js`, `.claude/workflows/implement-epic.js`,
`.claude/workflows/create-tickets.js`, `tests/tools/test_current_run_sidecar_orchestrator.py`,
`tests/tools/test_step0_ts_orchestrator.py` (new), `docs/agent-monitoring/schema.md`, and this
ticket file (self-correction of site/count numbers, Step 10).
