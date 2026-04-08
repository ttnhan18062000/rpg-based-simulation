# Test Plan: TCK-20260408-PHASE3-ROUTINE

## Unit Tests
- `tests/unit/core/logic/test_routine_service.py`:
    - Test `calculate_routine_biases` with various debt levels.
    - Verify circadian rhythm multipliers (day vs night).

## Integration Tests
- `tests/integration/biological/test_routine_cycle.py`:
    - Setup: Entity with 0 hunger, 0 sleep debt.
    - Step 1: Advance time (ticks) until hunger > 0.5.
    - Verify: Entity eventually selects `GoalType.EAT`.
    - Step 2: Ensure `EAT` action reduces hunger.
    - Step 3: Advance time until night.
    - Verify: Entity eventually selects `GoalType.SLEEP`.
    - Step 4: Ensure sleeping reduces sleep debt.

## E2E / UI Tests
- Run simulation via CLI.
- Inspect entity via Web UI.
- Verify biological stats are visible and updating.
