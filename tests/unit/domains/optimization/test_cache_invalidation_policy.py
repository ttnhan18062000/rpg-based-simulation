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
    # PERF-010: semantic_region_index is a distinctly-named additive domain (TCK-20260822-SEMANTIC-ENTITY-INDEX)
    # sharing the same region_ids trigger as the pre-existing (phantom, unconsumed) region_index tag.
    assert "semantic_region_index" in invalidated
    assert len(invalidated) == 2
    assert CacheInvalidationPolicy.should_invalidate("regions", dirty) is True
    assert CacheInvalidationPolicy.should_invalidate("region", dirty) is True


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
    assert CacheInvalidationPolicy.should_invalidate("identity", dirty) is False
    assert CacheInvalidationPolicy.should_invalidate("region", dirty) is False
    assert CacheInvalidationPolicy.should_invalidate("needs", dirty) is False
    # knowledge conservatively always invalidates -- information_providers has no DirtySet tag
    assert CacheInvalidationPolicy.should_invalidate("knowledge", dirty) is True

    # None dirty set should invalidate everything (fallback)
    assert CacheInvalidationPolicy.should_invalidate("resources", None) is True


def test_cache_invalidation_policy_unrelated_domains_unaffected():
    """
    TCK-20260822-SEMANTIC-ENTITY-INDEX Step 3 anti-drift guard: adding identity/region/needs/
    knowledge domains for SemanticEntityIndexService must not change should_invalidate()'s
    results for the five pre-existing spatial domains against dirty inputs specific to the new
    domains (identity/biological-only dirt), and the pre-existing per-field expectations
    (resources/buildings/entities/ground_items/corpses/regions each only fire on their own tag)
    still hold exactly as before this ticket.
    """
    spatial_domains = ("resources", "buildings", "entities", "ground_items", "corpses", "regions")

    identity_only = DirtySet(identity_entities={7})
    biological_only = DirtySet(biological_entities={8})
    for domain in spatial_domains:
        assert CacheInvalidationPolicy.should_invalidate(domain, identity_only) is False
        assert CacheInvalidationPolicy.should_invalidate(domain, biological_only) is False

    assert CacheInvalidationPolicy.should_invalidate("resources", DirtySet(resource_node_ids={1})) is True
    assert CacheInvalidationPolicy.should_invalidate("buildings", DirtySet(building_ids={2})) is True
    assert CacheInvalidationPolicy.should_invalidate("entities", DirtySet(movement_entities={3})) is True
    assert CacheInvalidationPolicy.should_invalidate("ground_items", DirtySet(ground_item_ids={5})) is True
    assert CacheInvalidationPolicy.should_invalidate("corpses", DirtySet(corpse_ids={6})) is True
    assert CacheInvalidationPolicy.should_invalidate("regions", DirtySet(region_ids={"north_woods"})) is True
