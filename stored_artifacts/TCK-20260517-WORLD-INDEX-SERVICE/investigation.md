# Investigation: WorldIndexService & SpatialQueryService

## Current State

Currently, AI scorers (`HarvestScorer`, `SleepScorer`, `EatScorer` in `src/ai/goals/scorers.py`) attach ad-hoc caches (`_active_nodes_grid`, `_inns_cache`, `_taverns_cache`) directly to `AuthoritativeState`.
Furthermore, `src/engine/spatial_query.py` implements basic spatial query helpers but also attaches internal maps (`_node_map_cache`, `_building_map_cache`) to `state`.

## Observations & Issues

1. Ad-hoc caches attached via `object.__setattr__` during AI evaluation risk inconsistent state if entities move or resource nodes deplete mid-tick or across sub-phases without proper invalidation.
2. Building an explicit `WorldIndexes` read model managed by an authoritative `WorldIndexService` ensures that spatial indexing is reused efficiently within a tick while remaining strictly bound by dirty set invalidation rules.

## Proposed Design

- `WorldIndexes`: A frozen structure holding `tick`, `spatial_grid` (for entities), `active_resource_nodes` (spatial grid or list of nodes with remaining charges and zero cooldown), `buildings_by_kind` (dict mapping kind string to list of building objects), etc.
- `CacheInvalidationPolicy`: Identifies whether the indices for resources, buildings, or entities must be rebuilt based on `DirtySet` (e.g. `resource_nodes`, `buildings`, `movement_entities`, `lifecycle_entities`).
- `WorldIndexService`: Attaches or accesses `world_indexes` on `AuthoritativeState`. If `tick != state.tick` or relevant dirty flags are set, it rebuilds the required indices.
- `SpatialQueryService`: Upgraded to utilize `WorldIndexService.get_indexes(state, dirty)` to answer queries (`nearest_resource_node`, `nearest_building`, `nearby_entities`) with O(1) index lookups or spatial grid traversals.
- Refactor `HarvestScorer`, `SleepScorer`, `EatScorer` to use `SpatialQueryService.nearest_resource_node(...)` and `SpatialQueryService.nearest_building(...)`.
