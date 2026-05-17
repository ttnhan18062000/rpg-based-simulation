# TCK-20260518-DOC-CHECKLIST-UPDATE

## Title

Update Logic Checklists and Performance Test Plan with Verified Completed Tasks

## Status

DONE

## Request Summary

The user requested to update `docs/logic_checklist_exhaustive.md` and `perf_test_plan.md` to mark all newly completed and verified tasks.

## Scope

- Update `perf_test_plan.md` lines 1354-1376 to check `[x]` for items 1 through 11 (CandidateSelector, Full-scan compliance, Static guards, DirtyDependencyGraph, StateUpdateCompactor, MovementCandidateSelector, OccupancySnapshot, MovementPlanCache, WorldIndexService, SpatialQueryService, CacheInvalidationPolicy).
- Audit `docs/logic_checklist_exhaustive.md` for newly implemented optimization and engine hardening tests (e.g., optimization tests, candidate selector, compactor, etc.) and mark them `[x]` with appropriate `<!-- SOURCE: ... TEST: ... PROOF: ... -->` evidence comments.

## Out of Scope

- Implementing new game features or new engine optimization mechanisms.

## Acceptance Criteria

- `perf_test_plan.md` has all 14 recommended test implementation order items marked `[x]`.
- Verified optimization test items in `docs/logic_checklist_exhaustive.md` are marked `[x]` with correct citation tags.
- All tests pass successfully (83/83 in optimization and perf suites).

## Related Tickets

- TCK-20260517-PERF-OPT-HARDENING (and related optimization tickets)

## Related Docs

- docs/archive/profiling_performance/perf_test_plan.md
- docs/logic_checklist_exhaustive.md

## Related Stored Artifacts

- stored_artifacts/TCK-20260517-*

## Related Code Areas

- tests/unit/optimization/
- tests/integration/optimization/
- tests/perf/
- tests/static/

## Assumptions / Open Questions

- None

## Implementation Notes

- Verified 83/83 tests passing across optimization, perf, static, and integration test suites.

## Test Summary

- Run `pytest tests/unit/optimization tests/integration/optimization tests/static/test_no_direct_dirtyset_candidate_selection.py tests/unit/perf` (83 passed).

## Files Changed

- docs/archive/profiling_performance/perf_test_plan.md
- docs/logic_checklist_exhaustive.md

## Completion Summary

- Successfully updated `perf_test_plan.md` to check `[x]` for all 14 recommended test suites.
- Added `Z20. Performance Optimization Mechanisms (Milestone 3)` to `docs/logic_checklist_exhaustive.md` listing all 14 verified optimization items with complete proof tags.
