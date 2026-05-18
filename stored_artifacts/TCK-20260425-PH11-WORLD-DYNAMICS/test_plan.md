# Phase 10 World Dynamics Test Plan

## Unit Tests
- `tests/world/test_hazards.py`: Verify `WorldUpdate` application to `RegionState`.
- `tests/world/test_weather.py`: Verify stat multipliers in `EnvironmentService`.
- `tests/world/test_transformations.py`: Verify state-triggered type changes.

## Integration Tests
- `tests/world/test_suppression.py`: Verify `LegalityServiceV2` blocks actions in suppressed regions.

## Success Criteria
- 100% pass rate in `tests/world/`.
- No regressions in `ApplyPath`.
