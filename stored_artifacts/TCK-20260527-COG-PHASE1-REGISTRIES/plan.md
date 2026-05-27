# Implementation Plan - Phase 1 Data Registries

## Proposed Changes

### Component: Data Registries
#### [NEW] [registries.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/registries.py)
- Implement `ItemRegistry`, `ResourceRegistry`, `EnemyRegistry`, `RecipeRegistry`, `ServiceRegistry`, and `RegionRegistry`.
- Load `phase1_adventure_seed` pack dynamically from JSON.

#### [NEW] [test_registries.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/strategic/test_registries.py)
- Write registry lookup, read-only enforcement, and startup referential validation tests.

## Verification Plan

### Automated Tests
- Run `pytest tests/unit/strategic/test_registries.py`
