# Investigation: CacheInvalidationPolicy

`CacheInvalidationPolicy` in `src/engine/world_index.py` already implements `should_invalidate(domain: str, dirty: Optional[DirtySet]) -> bool`.
To fully satisfy Milestone 11 of `perf_test_plan.md`, we need to add `invalidated_indexes(dirty: DirtySet) -> set[str]` and ensure `should_invalidate` and `WorldIndexService` remain seamlessly integrated.

Mapping required by `perf_test_plan.md`:
- `resource_node_ids` -> `active_resource_node_index`
- `building_ids` -> `building_kind_index`
- `movement_entities` / `lifecycle_entities` -> `entity_position_index`, `occupancy_snapshot`
- `ground_item_ids` -> `ground_item_index`
- `corpse_ids` -> `corpse_index`
- `region_ids` -> `region_index`
