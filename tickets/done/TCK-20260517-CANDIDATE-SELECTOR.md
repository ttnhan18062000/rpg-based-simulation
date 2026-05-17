# TCK-20260517-CANDIDATE-SELECTOR

## Title

CandidateSelector & ScanPolicy Implementation

## Status

DONE

## Request Summary

Implement `CandidateSelector` as an authoritative centralized candidate selection mechanism for engine phases, eliminating scattered direct `update.dirty_set` reads. Validate via comprehensive unit tests guaranteeing deterministic ordering, active/inactive filtering, and exact domain union logic.

## Scope

- Implement `CandidateSelector` class in `src/core/dirty.py`
- Map all pipeline domains (movement, combat, inventory, strategic, social, lifecycle, biological, attributes, town, interactions, groups, shop, capacity, redirection, all) to appropriate dirty entity sets
- Enforce full-scan fallback when `update.force_full_scan` is True or `update.dirty_set` is None
- Implement active/inactive entity filtering based on `include_inactive` flag
- Ensure deterministic output order (sorted integer tuple)
- Implement exhaustive unit test suite in `tests/unit/optimization/test_candidate_selector.py` matching all 7 required test cases

## Out of Scope

- Refactoring existing engine phases to use `CandidateSelector` (this is reserved for subsequent milestones in the performance plan)
- Modifying `DirtySet` or `StateUpdate` internal structure or serialization

## Acceptance Criteria

- `CandidateSelector.entities` adheres perfectly to the specified contract
- All 7 required unit test cases in `test_candidate_selector.py` pass deterministically
- 100% test pass rates across the unit test suite without regressions

## Related Tickets

- Epic 16: Performance Audit (`epic-16-performance-audit.md`)

## Related Docs

- `perf_test_plan.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260517-CANDIDATE-SELECTOR/`

## Related Code Areas

- `src/core/dirty.py`
- `tests/unit/optimization/test_candidate_selector.py`

## Assumptions / Open Questions

- Assumes `entity.active` property accurately reflects entity liveness (`self.lifecycle.active`). Verified during test implementation.

## Implementation Notes

- Implemented `CandidateSelector.entities` static method in `src/core/dirty.py` supporting all 15 engine domains.
- Safely checks liveness via `self.lifecycle.active` and verifies entity existence against `state.entities`.
- Enforces strict deterministic return ordering via `tuple(sorted(...))`.

## Test Summary

- Executed `pytest tests/unit/optimization/test_candidate_selector.py -v`: 7/7 passed.
- Executed `pytest tests/unit/ -m "not slow" -v`: 737/737 passed.

## Files Changed

- `src/core/dirty.py`
- `tests/unit/optimization/test_candidate_selector.py`

## Completion Summary

- Milestone 1 (`CandidateSelector / ScanPolicy`) successfully implemented, verified, and certified against all requirements with zero regressions.
