# TCK-20260419-MB-TASK1-FREEZE-LAW

## Title
Freeze the runtime signal and governor law set

## Status
INPROGRESS

## Request Summary
Establish the absolute operational contract for Milestone B. This document defines the signal catalog, transition rules, recovery thresholds, and isolation boundaries that make the governor "trustworthy."

## Scope
- [ ] Create `docs/engine/runtime_signals_contract_mb.md` with full signal catalog.
- [ ] Create `docs/engine/mb_test_matrix.md` with explicit proof requirements.
- [ ] Hard-code (or profile-bind) exact transition watermarks.
- [ ] Define the "Confidence Window" law for anti-thrashing.
- [ ] Audit `governor.py` for remaining placeholders.

## Out of Scope
- Implementing the real accounting logic (Task 2).
- Finalizing the full test suite (Task 5).

## Acceptance Criteria
- [ ] Contract document exists and is exhaustive.
- [ ] Test matrix defines at least 15+ operational proof cases.
- [ ] No "magic number" constants in the governor remain undocumented.

## Related Tickets
- `TCK-20260419-MA-TASK5-FINAL-CLOSURE` (Pre-requisite)

## Related Docs
- `resource_implementation_v3_milestone_b.md`
- `resource_handbook.md`

## Related Stored Artifacts
- `staging_artifacts/TCK-20260419-MB-PLANNING/investigation.md`

## Related Code Areas
- `src/engine/governor.py`
- `src/engine/observability.py`

## Assumptions / Open Questions
- Assume "Peak Utilization" is the goal for worker accounting.
- Assume "Sampling Interval" will be moved to `RuntimeProfile`.

## Implementation Notes
- Follow Handbook Principle 5 (Operational Truth).
- Follow Handbook Principle 6 (Boundedness).

## Test Summary
- TBD

## Files Changed
- TBD

## Completion Summary
- TBD
