# Implementation Plan - AI and Freezing Stabilization (TCK-20260404-STABILIZATION)

Final stabilization of the AOA simulation engine. Resolves critical regressions in AI decision-making and core model freezing.

## Proposed Changes

### AI System Stabilization

#### [MODIFY] [navigation.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/states/navigation.py)
- Consolidate `Perception` imports to the top level.
- Purge redundant and shadowing local imports in `WanderHandler.handle`.

#### [MODIFY] [base.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/states/base.py)
- Ensure `HeroClass` is correctly imported and available in all scopes.

#### [MODIFY] [combat.py](file:///home/vboxuser/Work/rpg-based-simulation/src/ai/states/combat.py)
- Replace any legacy `Perception.get_faction_registry()` calls with `ctx.faction_reg`.

---

### Core Model Hardening

#### [MODIFY] [base.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/models/base.py)
- Update `SimulationModel.freeze()` to handle slotted models and skip already-frozen instances correctly.

## Verification Plan

### Automated Tests
- `pytest tests/e2e/test_combat_arena_e2e.py`
- `pytest tests/unit/core/test_invariants.py`
- `pytest tests/integration/api/test_api_payload.py`
