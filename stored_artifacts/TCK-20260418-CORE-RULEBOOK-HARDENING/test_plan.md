# Test Plan: Core Rulebook Hardening

## 1. Unit Tests (LegalityService)
- Test `get_occupant_id` with valid position, empty position, and dead entity.
- Test `check_targeting_legality` with:
    - Target in range, clear LOS (True)
    - Target out of range (False)
    - Target in range, blocked LOS (False)
    - Adjacent target (True, skips LOS)

## 2. Integration Tests (Refactored Services)
- **Combat Validation**: Verify `CombatAction.validate` still works but no longer calls `grid.has_line_of_sight` directly (mock grid to verify).
- **Movement Model**: Verify `MovementModel` successfully sidesteps using `LegalityService` calls.

## 3. Passive Progression Integrity (Drift Guards)
- Create `tests/engine/test_quiet_tick_integrity.py`.
- **Scenario 1: Dead World**. All entities dead. Verify `world.tick` increments and `Biological Decay` is called (even if it has nothing to do, the path must be exercised).
- **Scenario 2: Sleeping World**. All entities have high `next_act_at`. Verify `hunger_level` increases every tick for at least 5 ticks.
- **Scenario 3: Social World**. Two heroes stationary and silent. Verify `familiarity` increases via proximity bonding.

## 4. Regression
- Run `tests/combat/test_world_time_progression.py` to ensure no regression.
- Run `tests/combat/test_legality.py` (if it exists).
