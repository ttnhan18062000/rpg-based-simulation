# Walkthrough: API & Architecture Refactoring (Phase 1-4)

## Summary
Decomposed the `EngineManager` God Object, standardized API serialization, and transitioned hardcoded game data into core model logic. This significantly improves the maintainability and scalability of the simulation engine.

## Changes Made

### 1. EngineManager Decomposition (Phase 4)
- **[NEW] [world_generator.py](file:///d:/Projects/rpg-based-simulation/src/core/world_generator.py)**: Extracted 400+ lines of world generation logic (Voronoi regions, town placement, road generation, and entity spawning) from `EngineManager`.
- **[MODIFY] [engine_manager.py](file:///d:/Projects/rpg-based-simulation/src/api/engine_manager.py)**: Simplified `_build` to use the new `WorldGenerator` service, while preserving Kafka recovery logic.

### 2. Standardized Serialization (Phase 2 & 3)
- **[MODIFY] [models.py](file:///d:/Projects/rpg-based-simulation/src/core/models.py)**: Implemented `to_slim_schema()` and `to_full_schema()` methods in the `Entity` class.
- **[MODIFY] [classes.py](file:///d:/Projects/rpg-based-simulation/src/core/classes.py)**: Added `to_schema()` to `SkillInstance` for uniform skill representation.
- **[MODIFY] [state.py](file:///d:/Projects/rpg-based-simulation/src/api/routes/state.py)**: Removed 150+ lines of manual dictionary mapping in favor of the new model-driven serialization.

### 3. Core Logic & Bug Fixes
- Resolved critical `IndexError` in `WorldGenerator` during location painting.
- Fixed `AttributeSchema` field mismatches and restored missing imports (`HeroClass`, `Building`).
- Re-enabled `_finalize_build` in `EngineManager` to ensure simulation components (brain, loop) are correctly initialized.

## Results
- **65 tests passed** across the API and World Generation suites.
- **Verified World Generation**: Confirmed stable spawning of 260+ initial entities with valid attributes and gear.
- **API Performance**: Decoupling serialization from routes reduced complexity and improved maintainability.

### Verification Pass
```bash
pytest tests/test_regions.py tests/test_voronoi_regions.py tests/test_terrain_detail.py tests/test_api_payload.py
# Result: 65 passed, 0 failures
```

## Phase 5: Static vs. Dynamic State Separation

In this phase, we completed the architectural cleanup by separating invariant world data from dynamic simulation state.

### Backend Changes
- **Schemas**: Refactored `BuildingSchema`, `ResourceNodeSchema`, and `TreasureChestSchema` in `src/api/schemas.py` to remove dynamic fields.
- **State Schemas**: Created new `BuildingStateSchema`, `ResourceNodeStateSchema`, and `TreasureChestStateSchema` for dynamic updates.
- **Routes**: Updated `get_static` in `src/api/routes/state.py` to return only fixed positions and types. Updated `get_state` to include the new dynamic state collections.

### Frontend Changes
- **Types**: Updated `frontend/src/types/api.ts` to reflect the backend split.
- **Hook**: Refactored `useSimulation.ts` to merge dynamic updates from the `/state` poll into the static world objects.

### Verification
- Ran `pytest tests/test_api_payload.py`: All 8 tests passed, including new assertions for the dynamic/static split.
- Verified that static data (positions, types) is only fetched once, while dynamic status (counts, looted state) is polled correctly.
