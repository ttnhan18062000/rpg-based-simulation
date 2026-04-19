# TCK-20260419-MA-TASK3-PIN-SCHEDULER

## Title
Complete and pin deterministic scheduler classes

## Status
DONE

## Request Summary
Hard-code the deterministic work hierarchy and tie-break rules for the simulation scheduler. Ensure no placeholders remain in the baseline path and verify the exact sorting behavior via tests.

## Scope
- [x] Hard-code `CRITICAL` > `PERIODIC` > `DEFERRED` hierarchy.
- [x] Implement exact tie-break laws in `DeterministicScheduler.select_work`.
- [x] Expand test coverage for all work classes and tie-break scenarios.
- [x] Explicitly gate or remove `OPPORTUNISTIC` branch for Milestone A.

## Out of Scope
- Implementing actual Opportunistic systems (vfx, traces).
- Changes to the Governor's policy logic itself.

## Acceptance Criteria
- [x] Scheduler strictly follows the documented hierarchy.
- [x] Tie-breaks for Critical, Periodic, and Deferred are enforced.
- [x] Tests prove sorting stability with mixed work sets.
- [x] No `pass` placeholders in the final scheduler baseline.

## Related Tickets
- `TCK-20260419-MA-TASK1-FREEZE-LAW` (Predecessor)

## Related Docs
- `runtime_completion_contract_ma.md`
- `ma_test_matrix.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260419-MA-TASK3-PIN-SCHEDULER/investigation.md`
- `stored_artifacts/TCK-20260419-MA-TASK3-PIN-SCHEDULER/plan.md`
- `stored_artifacts/TCK-20260419-MA-TASK3-PIN-SCHEDULER/test_plan.md`

## Related Code Areas
- `src_v2/engine/scheduler.py`
- `src_v2/core/work.py`

## Assumptions / Open Questions
- None.

## Implementation Notes
- Removed the `pass` placeholder in the `OPPORTUNISTIC` branch and added a Milestone A Law comment.
- Fixed `PeriodicDefinition` and `AuthoritativeState` instantiation in tests (added missing `cadence` and `seed` arguments).
- Verified the `CRITICAL` > `PERIODIC` > `DEFERRED` hierarchy via `test_full_work_hierarchy`.

## Test Summary
- `test_readiness_driven_selection`: PASSED
- `test_deterministic_tiebreak`: PASSED
- `test_periodic_selection`: PASSED
- `test_full_work_hierarchy`: PASSED
- `test_deferred_tiebreak`: PASSED
- `test_mixed_periodic_tiebreak`: PASSED
- `test_governor_gating_non_auth_periodic`: PASSED

## Files Changed
- `src_v2/engine/scheduler.py`
- `tests_v2/engine/test_scheduler_contract.py`

## Completion Summary
- Successfully pinned the deterministic scheduler classes. The scheduler now follows a strict hierarchy and uses exact tie-break rules as defined in the Milestone A Law. Comprehensive tests ensure that these rules remain stable and that no accidental placeholders contaminate the baseline path.
