import pytest
from src.core.state import AuthoritativeState
from src.core.dirty import DirtySet
from src.systems.world_systems.generator import EntityGenerator
from src.api.read_model_cache import ReadModelCache, ReadModelInvalidationPolicy
from src.api.presenters.state_presenter import StatePresenter

@pytest.fixture
def sample_state() -> AuthoritativeState:
    gen = EntityGenerator(seed=42)
    e1 = gen.spawn_hero((10.0, 10.0))
    e2 = gen.spawn_goblin((15.0, 15.0))
    e3 = gen.spawn_goblin((20.0, 20.0))
    return AuthoritativeState(
        tick=1,
        seed=42,
        entities={e1.id: e1, e2.id: e2, e3.id: e3}
    )

def test_read_model_invalidation_policy(sample_state):
    all_ids = set(sample_state.entities.keys())
    
    # 1. None DirtySet invalidates all
    assert ReadModelInvalidationPolicy.get_dirty_entity_ids(None, all_ids) == all_ids
    
    # 2. force_full_scan invalidates all
    ds = DirtySet(movement_entities={1})
    assert ReadModelInvalidationPolicy.get_dirty_entity_ids(ds, all_ids, force_full_scan=True) == all_ids
    
    # 3. Selective DirtySet returns exact dirty subset
    ds_selective = DirtySet(movement_entities={1}, combat_entities={2})
    assert ReadModelInvalidationPolicy.get_dirty_entity_ids(ds_selective, all_ids) == {1, 2}

def test_read_model_cache_minimal_summary(sample_state):
    cache = ReadModelCache()
    cache.update(sample_state)
    summary = cache.get_minimal_summary()
    assert summary["entities_count"] == 3
    assert summary["tick"] == 1

def test_read_model_cache_hit_and_miss(sample_state):
    cache = ReadModelCache()
    cache.update(sample_state)
    
    e1 = sample_state.entities[1]
    
    # First access -> miss
    dto1 = cache.get_entity_dto(e1)
    metrics = cache.get_metrics()
    assert metrics["misses"] == 1
    assert metrics["hits"] == 0
    assert dto1["id"] == 1
    
    # Second access -> hit
    dto2 = cache.get_entity_dto(e1)
    metrics = cache.get_metrics()
    assert metrics["misses"] == 1
    assert metrics["hits"] == 1
    assert dto1 == dto2

def test_selective_invalidation_by_dirtyset(sample_state):
    cache = ReadModelCache()
    cache.update(sample_state)
    
    e1 = sample_state.entities[1]
    e2 = sample_state.entities[2]
    
    # Cache both
    cache.get_entity_dto(e1)
    cache.get_entity_dto(e2)
    assert cache.get_metrics()["cached_entities"] == 2
    
    # Mark e1 dirty
    ds = DirtySet(movement_entities={1})
    invalidated = cache.update(sample_state, dirty_set=ds)
    assert invalidated == {1}
    
    metrics = cache.get_metrics()
    assert metrics["cached_entities"] == 1  # e2 remains cached!
    assert metrics["invalidations"] == 1
    
    # Accessing e2 is a hit
    cache.get_entity_dto(e2)
    assert cache.get_metrics()["hits"] == 1
    
    # Accessing e1 is a miss (rebuilt)
    cache.get_entity_dto(e1)
    assert cache.get_metrics()["misses"] == 3  # (initial 2 + 1 rebuild)

def test_get_entities_paged_uses_cache(sample_state):
    cache = ReadModelCache()
    cache.update(sample_state)
    
    res = cache.get_entities_paged(sample_state, offset=0, limit=2)
    assert len(res["entities"]) == 2
    assert res["total"] == 3
    assert cache.get_metrics()["misses"] == 2
    
    # Second call -> 2 hits
    cache.get_entities_paged(sample_state, offset=0, limit=2)
    assert cache.get_metrics()["hits"] == 2
