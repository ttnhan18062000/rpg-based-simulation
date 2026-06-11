---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260328
artifact_type: test_plan
tags: []
---

# Test Plan - Backend Restructuring & StatsProxy

## 1. StatsProxy Verification
- **Unit Tests**: `tests/unit/core/test_models_refactor.py` should pass with 100% coverage for all properties (atk, def, spd, etc.).
- **Mock Integrity**: `tests/unit/ai/test_inventory_goals.py` and `tests/unit/ai/test_stuck.py` must be fixed to handle the new `StatsProxy` property access correctly without `TypeError`.

## 2. New Subsystems
### TerritorySystem
- **Test Case**: Entity in hostile territory receives `TERRITORY_DEBUFF`.
- **Test Case**: Entity in home territory receives `TERRITORY_BUFF`.
- **Test Case**: Neutral entity receives no effect.
- **Verification**: Check `entity.effects` for the expected `StatusEffect`.

### CombatTrackingSystem
- **Test Case**: Entity attacking a target sets `combat_target_id`.
- **Test Case**: Entity moving away from combat clears `combat_target_id` after a delay.
- **Test Case**: Threat decays correctly per tick.

### MemorySystem
- **Test Case**: Entity's memory prunes old entries correctly.
- **Test Case**: Terrain mapping (visited regions) updates world knowledge correctly.

### GoalSystem
- **Test Case**: Goal scoring remains deterministic given the same context and RNG.
- **Test Case**: Hysteresis/Boredom modifiers correctly influence the winning goal.

## 3. WorldLoop Integration
- **E2E Smoke Test**: `uv run src/__main__.py --max-ticks 1000`
- **Replay Determinism**: `tests/e2e/test_deterministic_replay.py` must pass to ensure the new modular architecture didn't introduce non-determinism.
