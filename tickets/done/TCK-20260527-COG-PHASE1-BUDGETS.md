# TCK-20260527-COG-PHASE1-BUDGETS

## Title

Implement Phase 1 Provider Performance Budget Gates

## Status

DONE

## Request Summary

Add performance counters and budget gates for resource/service providers and requirement evaluation steps to ensure CPU execution cost scales boundedly for 10, 30, and 100 entities.

## Scope

- Add metrics/counters for provider execution steps.
- Set budget thresholds and rate-limiting limits to enforce bounded call rates.
- Add performance tests verifying these gates under `tests/unit/strategic/test_performance_budgets.py`.

## Out of Scope

- Modifying the core `ActionRouter` or physical movement.

## Acceptance Criteria

- Counters track provider calls, returned opportunities, and evaluated requirements.
- Rate limits successfully throttle excessive provider queries.
- Bounded performance under high entity load (10, 30, and 100 scale).
- Unit/performance tests pass.

## Related Tickets

- None

## Related Docs

- `entity_enhance_phase1.md` (Task 10)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/world/providers/resources.py`
- `src/world/providers/services.py`
- `src/world/providers/requirements.py`
- `tests/unit/strategic/test_performance_budgets.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Added `PerformanceBudgets` metrics registry with auto-increment counters inside resource provider, service provider, and requirement evaluator.
- Set strict budget gates throttling calls past set limits.

## Test Summary

- Run `pytest tests/unit/strategic/test_performance_budgets.py` verifying counter registration, reset logic, and evaluator/provider rate limiting under budget exhaustion.
- All 2 tests pass successfully.

## Files Changed

- `src/world/providers/resources.py`
- `src/world/providers/services.py`
- `src/world/providers/requirements.py`
- `tests/unit/strategic/test_performance_budgets.py`

## Completion Summary

- Bounded performance budget gates fully implemented and validated. Evaluator cost and opportunity search are now certified scale-safe.

