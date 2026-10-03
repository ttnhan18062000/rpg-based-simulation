---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260425-PH11-WORLD-DYNAMICS
artifact_type: test_plan
tags: [ph11, world, dynamics]
---

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
