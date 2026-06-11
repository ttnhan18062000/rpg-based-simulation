---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260517-WORLD-INDEX-SERVICE
artifact_type: test_plan
tags: [world, index, service]
---

# Test Plan: WorldIndexService & SpatialQueryService

## Target Test Files

1. `tests/unit/optimization/test_world_index_service.py`
2. `tests/unit/optimization/test_spatial_query_service.py`

## Test Cases (`test_world_index_service.py`)

- `test_world_index_builds_active_resource_node_index`: Verify only active nodes with charges > 0 and cooldown <= 0 are indexed.
- `test_world_index_excludes_depleted_resource_nodes`: Verify depleted or cooling down nodes are omitted.
- `test_world_index_builds_buildings_by_kind`: Verify buildings are mapped into lists by kind string.
- `test_world_index_reuses_index_when_tick_and_dirty_domains_unchanged`: Verify consecutive calls return exact same index instance.
- `test_world_index_invalidates_resource_index_when_resource_node_dirty`: Verify dirty resource node rebuilds only resource index.
- `test_world_index_invalidates_building_index_when_building_dirty`: Verify dirty building rebuilds building index.

## Test Cases (`test_spatial_query_service.py`)

- `test_spatial_query_nearest_resource_matches_naive_scan`: Verify `nearest_resource_node` produces identical node to brute force distance scan.
- `test_spatial_query_nearest_building_matches_naive_scan`: Verify `nearest_building` produces identical building to brute force scan.
- `test_spatial_query_nearby_entities_matches_naive_scan`: Verify `nearby_entities` matches brute force distance check.
- `test_scorers_use_spatial_query_without_attaching_hidden_caches`: Run scorers on a mock state and verify no hidden cache attributes (`_active_nodes_grid`, `_inns_cache`, `_taverns_cache`) are attached to state.

## Execution

```bash
pytest tests/unit/optimization/test_world_index_service.py -v
pytest tests/unit/optimization/test_spatial_query_service.py -v
pytest tests/unit/ -m "not slow"
```
