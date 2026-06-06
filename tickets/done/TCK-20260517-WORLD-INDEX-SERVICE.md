# TCK-20260517-WORLD-INDEX-SERVICE

## Title

WorldIndexService and SpatialQueryService Implementation for Reusable Spatial Indexing

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement `WorldIndexService`, `WorldIndexes`, `SpatialQueryService`, and `CacheInvalidationPolicy` to build reusable spatial indices over world state (active resource nodes, buildings by kind, entities, corpses, ground items) and replace ad-hoc caches in scorers.

## Scope

- Create `WorldIndexes` dataclass in `src/engine/world_index.py`.
- Create `WorldIndexService` to build reusable indices, taking `state` and `dirty` set to determine when to invalidate.
- Create `CacheInvalidationPolicy` to manage invalidation domains based on `DirtySet`.
- Refactor/enhance `SpatialQueryService` (or create in `world_index.py` / update `spatial_query.py`) to provide `nearest_resource_node`, `nearest_building`, and `nearby_entities`.
- Refactor `HarvestScorer`, `SleepScorer`, and `EatScorer` in `src/ai/goals/scorers.py` to use `SpatialQueryService` instead of attaching ad-hoc caches to `state`.
- Implement unit tests verifying index reuse, dirty invalidation, and exact match with naive scans.

## Out of Scope

- Modifying AI goal selection logic beyond spatial query replacement.

## Acceptance Criteria

- [x] Spatial queries match naive scan.
- [x] Index invalidation is dirty-domain based.
- [x] Same-tick repeated query reuses index.
- [x] Scorers no longer attach hidden caches to state.

## Related Tickets

- TCK-20260517-MOVEMENT-PLAN-CACHE.md

## Related Docs

- perf_test_plan.md

## Related Stored Artifacts

- stored_artifacts/TCK-20260517-WORLD-INDEX-SERVICE/

## Related Code Areas

- src/engine/world_index.py
- src/engine/spatial_query.py
- src/ai/goals/scorers.py
- tests/unit/optimization/test_world_index_service.py
- tests/unit/optimization/test_spatial_query_service.py

## Assumptions / Open Questions

- None

## Implementation Notes

- Implemented `WorldIndexes`, `WorldIndexService`, and `CacheInvalidationPolicy` in `src/engine/world_index.py`.
- Upgraded `SpatialQueryService` in `src/engine/spatial_query.py` with `nearest_resource_node`, `nearest_building`, and `nearby_entities`.
- Refactored `HarvestScorer`, `SleepScorer`, and `EatScorer` to use `SpatialQueryService`, eliminating ad-hoc `_inns_cache`, `_taverns_cache`, and `_active_nodes_grid` mutations.
- Preserved `world_indexes` across ticks in `apply_generation` and across readonly copies in `to_readonly`.

## Test Summary

- Run `pytest tests/unit/optimization/test_world_index_service.py`: 6/6 passed in 0.13s.
- Run `pytest tests/unit/optimization/test_spatial_query_service.py`: 4/4 passed in 0.35s.
- Run full regression suite `pytest tests/unit/ -m "not slow"`: 778/778 passed in 12.34s.

## Files Changed

- src/engine/world_index.py [NEW]
- src/engine/spatial_query.py
- src/ai/goals/scorers.py
- src/core/state.py
- src/engine/apply.py
- tests/unit/optimization/test_world_index_service.py [NEW]
- tests/unit/optimization/test_spatial_query_service.py [NEW]

## Completion Summary

Flawlessly completed Milestone 10. `WorldIndexService` provides authoritative, reusable, dirty-domain invalidated spatial indices over world objects, replacing state-attached ad-hoc scorer caches and ensuring strict simulation and architectural truth.
