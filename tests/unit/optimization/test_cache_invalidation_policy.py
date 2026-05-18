# Compliance IDs: PERF-011
import pytest
from src.core.dirty import DirtySet
from src.engine.world_index import CacheInvalidationPolicy


def test_resource_node_dirty_invalidates_resource_index():
    dirty = DirtySet(resource_node_ids={1, 2})
    invalidated = CacheInvalidationPolicy.invalidated_indexes(dirty)
    assert "active_resource_node_index" in invalidated
    assert len(invalidated) == 1
    assert CacheInvalidationPolicy.should_invalidate("resources", dirty) is True
    assert CacheInvalidationPolicy.should_invalidate("buildings", dirty) is False


def test_building_dirty_invalidates_building_index():
    dirty = DirtySet(building_ids={10})
    invalidated = CacheInvalidationPolicy.invalidated_indexes(dirty)
    assert "building_kind_index" in invalidated
    assert len(invalidated) == 1
    assert CacheInvalidationPolicy.should_invalidate("buildings", dirty) is True
    assert CacheInvalidationPolicy.should_invalidate("resources", dirty) is False


def test_movement_dirty_invalidates_occupancy_and_entity_position_index():
    dirty = DirtySet(movement_entities={100})
    invalidated = CacheInvalidationPolicy.invalidated_indexes(dirty)
    assert "entity_position_index" in invalidated
    assert "occupancy_snapshot" in invalidated
    assert len(invalidated) == 2
    assert CacheInvalidationPolicy.should_invalidate("entities", dirty) is True

    dirty_lifecycle = DirtySet(lifecycle_entities={200})
    invalidated_life = CacheInvalidationPolicy.invalidated_indexes(dirty_lifecycle)
    assert "entity_position_index" in invalidated_life
    assert "occupancy_snapshot" in invalidated_life
    assert len(invalidated_life) == 2
    assert CacheInvalidationPolicy.should_invalidate("entities", dirty_lifecycle) is True


def test_ground_item_dirty_invalidates_loot_index():
    dirty = DirtySet(ground_item_ids={50})
    invalidated = CacheInvalidationPolicy.invalidated_indexes(dirty)
    assert "ground_item_index" in invalidated
    assert len(invalidated) == 1
    assert CacheInvalidationPolicy.should_invalidate("ground_items", dirty) is True


def test_corpse_dirty_invalidates_corpse_index():
    dirty = DirtySet(corpse_ids={13})
    invalidated = CacheInvalidationPolicy.invalidated_indexes(dirty)
    assert "corpse_index" in invalidated
    assert len(invalidated) == 1
    assert CacheInvalidationPolicy.should_invalidate("corpses", dirty) is True


def test_region_dirty_invalidates_region_index():
    dirty = DirtySet(region_ids={"north_woods"})
    invalidated = CacheInvalidationPolicy.invalidated_indexes(dirty)
    assert "region_index" in invalidated
    assert len(invalidated) == 1
    assert CacheInvalidationPolicy.should_invalidate("regions", dirty) is True


def test_empty_dirty_invalidates_nothing():
    dirty = DirtySet()
    invalidated = CacheInvalidationPolicy.invalidated_indexes(dirty)
    assert len(invalidated) == 0
    assert CacheInvalidationPolicy.should_invalidate("resources", dirty) is False
    assert CacheInvalidationPolicy.should_invalidate("buildings", dirty) is False
    assert CacheInvalidationPolicy.should_invalidate("entities", dirty) is False
    assert CacheInvalidationPolicy.should_invalidate("ground_items", dirty) is False
    assert CacheInvalidationPolicy.should_invalidate("corpses", dirty) is False
    assert CacheInvalidationPolicy.should_invalidate("regions", dirty) is False

    # None dirty set should invalidate everything (fallback)
    assert CacheInvalidationPolicy.should_invalidate("resources", None) is True
