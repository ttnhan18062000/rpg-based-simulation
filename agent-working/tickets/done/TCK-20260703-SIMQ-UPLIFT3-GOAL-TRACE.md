---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-GOAL-TRACE
phase: done
date: 2026-07-03
tags: [observability, strategy, trace, backlog, duplicate-work]
---

# TCK-20260703-SIMQ-UPLIFT3-GOAL-TRACE

## Title
Retain top-3 runner-up goal scores in the cognition trace, not just the winning project's score — CLOSED AS DUPLICATE, already implemented by TCK-20260627-P1H-GOAL-RUNNERUP

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Carried over from `docs/plans/audit_fix_plan.md` P1-H (confirmed still open 2026-07-03).
`source_goal_score` in cognition snapshots captures only the winning project's score. Runner-up
scores — why goal X won over goal Y this tick — are computed transiently inside `execute_brain()`
and discarded at tick boundary. This means a developer inspecting why an entity appears "stuck"
cannot distinguish "stuck because every alternative genuinely scored lower" from "stuck on a
high-priority goal that should have been interrupted but wasn't" — a real diagnostic gap for
anyone debugging AGENCY/strategic-cognition behavior (including future work on
`TCK-20260703-SIMQ-UPLIFT3-BRANCH-B` and any AGENCY-adjacent investigation).

## Scope
1. Re-verify against current `src/` that runner-up scores are still discarded (this ticket may be
   picked up after other changes land).
2. Retain the top-3 candidate scores at tick commit in the cognition snapshot — add to
   `EntityInspectionSnapshot.goal_scores` (or the current equivalent field/structure).
3. Extend the existing `decision_trace.jsonl` infrastructure to carry this data — extend the trace
   record schema rather than inventing a new sidecar file.
4. Add a test proving the top-3 scores are captured and distinguishable from the winning score in
   a scenario with at least 2 competing goals of different priority.

## Out of Scope
- Any change to how goals are actually scored or selected (`execute_brain()`'s decision logic
  itself) — this ticket only retains data that's already computed, it does not change behavior
- Building new tooling/dashboards to visualize the runner-up data (that's a follow-on consumer, not
  this ticket's scope)

## Acceptance Criteria
- [x] Top-3 candidate goal scores retained at tick commit, not discarded — already true, via
      `DecisionTraceWriter.write_trace()`'s bounded `_latest_goal_scores` cache
- [x] `EntityInspectionSnapshot.goal_scores` (or current equivalent) includes runner-up data —
      already true, populated from that same cache (`entity_inspector.py:142`)
- [x] `decision_trace.jsonl` schema extended to carry the new data — already true,
      `source_goal_score` + `runner_up_scores` fields, documented in
      `docs/observability/decision_trace_contract.md`
- [x] Test confirms runner-up scores are captured and distinguishable from the winner in a
      multi-goal scenario — already true, 4 dedicated tests in
      `tests/unit/observability/test_decision_trace.py`, confirmed passing (24/24) 2026-07-04
- [x] No change to actual goal-selection behavior — trivially true, this ticket made no code
      changes at all

## Related Tickets
- None currently open covering this — carried over fresh from `docs/plans/audit_fix_plan.md` P1-H

## Related Docs
- `docs/plans/audit_fix_plan.md` P1-H — original finding, source of this ticket

## Related Stored Artifacts
- None yet

## Related Code Areas
- `src/domains/adventure/phase.py` — `execute_brain()`, where candidate scores are computed
  transiently
- `src/observability/cognition/recorder.py` — cognition snapshot recording

## Assumptions / Open Questions
None currently identified — this is a well-scoped, additive observability change. Investigation
phase should confirm the exact current shape of `EntityInspectionSnapshot` and
`decision_trace.jsonl` before implementation, since both may have changed since the original D15
audit finding.

## Implementation Notes
Investigation found this ticket describes work that was already completed by
`TCK-20260627-P1H-GOAL-RUNNERUP` (done 2026-06-27) — the "still open" status carried over from
`docs/plans/audit_fix_plan.md`'s 2026-07-03 status refresh was itself a false negative: that
refresh grepped `src/observability/cognition/recorder.py` and `src/domains/adventure/phase.py` (the
files named in the *original* D15 finding), but the actual fix landed in
`src/observability/cognition/decision_trace_writer.py::DecisionTraceWriter.write_trace()` (sorts
candidates descending, emits `source_goal_score` + `runner_up_scores` for ranks 2-3, bounded
per-entity cache `_latest_goal_scores`) and
`src/observability/live/entity_inspector.py::EntityInspectionSnapshot.goal_scores` (populated from
that cache) — neither file was checked during the 2026-07-03 refresh.

`recorder.py` is a genuinely separate system (the cognition graph-snapshot/diff recorder feeding
narrative diffing, with its own single-value `source_goal_score` copied from `ProjectState.score`)
that was never in scope for the 2026-06-27 fix and is not what this ticket's acceptance criteria
target — confirmed by direct source read, not assumed.

No source or test code was changed. The only action taken: corrected
`docs/plans/audit_fix_plan.md`'s P1-H entry (and its Summary Table row, Suggested Fix Order
section, and "still open" list) from OPEN to RESOLVED, with the corrected file citations and an
explicit note that the 2026-07-03 re-check was a false negative — so this gap in the traceability
record doesn't get rediscovered a third time.

## Test Summary
No new tests written — none needed. Re-ran the existing test suite covering this exact behavior
to confirm it is genuinely working, not just documented as working:
`pytest tests/unit/observability/test_decision_trace.py -q` → 24 passed, 0 failed, including the
4 tests specifically covering runner-up score capture
(`test_decision_trace_runner_up_scores_present`, `_source_goal_score_present`,
`_runner_up_fewer_than_3`, `_runner_up_single_candidate`).

## Files Changed
- `docs/plans/audit_fix_plan.md` — P1-H entry corrected from OPEN to RESOLVED with accurate file
  citations; Summary Table row updated; Suggested Fix Order section's "still open" list and
  correction-note both updated

## Completion Summary
Closed as duplicate work: this ticket's entire scope was already implemented by
`TCK-20260627-P1H-GOAL-RUNNERUP` (done 2026-06-27). The "still open" status this ticket carried
over from `docs/plans/audit_fix_plan.md`'s own 2026-07-03 status refresh was a false negative in
that refresh (it grepped the original finding's cited files, not the files the actual fix landed
in). Verified the existing implementation is genuinely correct and tested (24/24 tests passing),
not just claimed — then corrected the traceability record (`audit_fix_plan.md`) so this doesn't get
flagged as open a third time. No source or test code changes; this is a documentation-only
closure, mirroring the "detect duplicate work" outcome CLAUDE.md's Context Scan step exists to
catch.
