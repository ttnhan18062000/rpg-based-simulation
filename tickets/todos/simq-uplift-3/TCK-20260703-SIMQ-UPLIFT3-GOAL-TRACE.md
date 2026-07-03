---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-GOAL-TRACE
phase: open
date: 2026-07-03
tags: [observability, strategy, trace, backlog]
---

# TCK-20260703-SIMQ-UPLIFT3-GOAL-TRACE

## Title
Retain top-3 runner-up goal scores in the cognition trace, not just the winning project's score

## Status
OPEN

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
- [ ] Top-3 candidate goal scores retained at tick commit, not discarded
- [ ] `EntityInspectionSnapshot.goal_scores` (or current equivalent) includes runner-up data
- [ ] `decision_trace.jsonl` schema extended to carry the new data
- [ ] Test confirms runner-up scores are captured and distinguishable from the winner in a
      multi-goal scenario
- [ ] No change to actual goal-selection behavior (regression test: existing goal-selection tests
      unchanged in outcome)

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
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
