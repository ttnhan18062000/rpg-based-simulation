---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260517-WORLD-INDEX-SERVICE
artifact_type: plan
tags: [world, index, service]
---

# Plan: WorldIndexService & SpatialQueryService

## Phase 1: Core Indexing Models and Service (`src/engine/world_index.py`)

1. Define `CacheInvalidationPolicy` with static helper `should_invalidate(domain: str, dirty: DirtySet | None) -> bool`.
2. Define `WorldIndexes` dataclass containing:
   - `tick: int`
   - `active_resource_nodes: dict[tuple[int, int], list[tuple[float, float, int]]]`
   - `buildings_by_kind: dict[str, list[BuildingState]]`
   - `entities_by_tile: dict[tuple[int, int], list[int]]`
3. Define `WorldIndexService.get_indexes(state: AuthoritativeState, dirty: DirtySet | None) -> WorldIndexes`.
   - Attaches `world_indexes` to `state` (or uses existing if valid for tick and not dirty).
   - If dirty or new tick, rebuilds only the invalidated domains.

## Phase 2: SpatialQueryService Enhancement (`src/engine/spatial_query.py` or `world_index.py`)

1. Add `nearest_resource_node(state, pos: tuple[float, float], dirty=None) -> ResourceNodeState | None`
2. Add `nearest_building(state, pos: tuple[float, float], kind: str, dirty=None) -> BuildingState | None`
3. Add `nearby_entities(state, pos: tuple[float, float], radius: float, dirty=None) -> list[int]`
4. Ensure these methods use `WorldIndexService.get_indexes`.

## Phase 3: Scorer Refactoring (`src/ai/goals/scorers.py`)

1. Refactor `HarvestScorer` to use `SpatialQueryService.nearest_resource_node`.
2. Refactor `SleepScorer` to use `SpatialQueryService.nearest_building(..., kind="inn")`.
3. Refactor `EatScorer` to use `SpatialQueryService.nearest_building(..., kind="tavern")`.
4. Remove all ad-hoc `object.__setattr__(state, ...)` from scorers.

## Phase 4: Integration and State Preservation

1. Add `world_indexes` field to `AuthoritativeState` (default None, repr=False, compare=False).
2. Ensure `world_indexes` is preserved or reset cleanly in `to_readonly` and `apply_generation`.

## Phase 5: Verification

1. Implement `tests/unit/optimization/test_world_index_service.py`.
2. Implement `tests/unit/optimization/test_spatial_query_service.py`.
3. Run `pytest tests/unit/optimization/` and full regression test suite.
