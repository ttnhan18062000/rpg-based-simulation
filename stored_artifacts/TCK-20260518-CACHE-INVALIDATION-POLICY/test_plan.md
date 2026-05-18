# Test Plan: CacheInvalidationPolicy

Implement the following unit tests in `tests/unit/optimization/test_cache_invalidation_policy.py`:
- `test_resource_node_dirty_invalidates_resource_index`
- `test_building_dirty_invalidates_building_index`
- `test_movement_dirty_invalidates_occupancy_and_entity_position_index`
- `test_ground_item_dirty_invalidates_loot_index`
- `test_corpse_dirty_invalidates_corpse_index`
- `test_empty_dirty_invalidates_nothing`
