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


# --- compute_tick_delta (TCK-20260821-WS-ENTITY-DELTA-BROADCAST) ---

def test_compute_tick_delta_changed_includes_only_dirty_and_alive_entities(sample_state):
    cache = ReadModelCache()
    e1, e2, e3 = sample_state.entities[1], sample_state.entities[2], sample_state.entities[3]
    import dataclasses
    dead_e2 = dataclasses.replace(e2, combat=dataclasses.replace(e2.combat, alive=False))
    state = dataclasses.replace(
        sample_state, entities={e1.id: e1, e2.id: dead_e2, e3.id: e3}
    )

    ds = DirtySet(movement_entities={e1.id, e2.id})
    payload = cache.compute_tick_delta(state, ds, force_full_scan=False, tick=1)

    assert payload is not None
    changed_ids = {c["id"] for c in payload["changed"]}
    assert changed_ids == {e1.id}
    assert payload["removed"] == []


def test_compute_tick_delta_removed_is_gone_from_state_not_alive_false(sample_state):
    """Anti-drift guard: removed = entities_remove-style pop from state.entities, never a bare
    combat.alive=False flip on an entity that's still present."""
    import dataclasses
    cache = ReadModelCache()
    e1, e2, e3 = sample_state.entities[1], sample_state.entities[2], sample_state.entities[3]

    dead_but_present = dataclasses.replace(e2, combat=dataclasses.replace(e2.combat, alive=False))
    state = dataclasses.replace(
        sample_state, entities={e1.id: e1, e2.id: dead_but_present}
    )

    # e3.id is dirty but has been popped from state.entities entirely -- a real removal.
    ds = DirtySet(movement_entities={e2.id, e3.id})
    payload = cache.compute_tick_delta(state, ds, force_full_scan=False, tick=1)

    assert payload is not None
    assert payload["removed"] == [e3.id]
    changed_ids = {c["id"] for c in payload["changed"]}
    assert e2.id not in changed_ids
    assert e3.id not in changed_ids


def test_compute_tick_delta_quiet_tick_returns_none(sample_state):
    cache = ReadModelCache()
    ds = DirtySet()
    assert cache.compute_tick_delta(sample_state, ds, force_full_scan=False, tick=21) is None


def test_compute_tick_delta_heartbeat_tick_returns_payload_even_when_quiet(sample_state):
    cache = ReadModelCache()
    ds = DirtySet()
    payload = cache.compute_tick_delta(sample_state, ds, force_full_scan=False, tick=20)
    assert payload is not None
    assert payload["changed"] == []
    assert payload["removed"] == []
    assert payload["tick"] == 20


def test_compute_tick_delta_values_are_absolute_never_diffed(sample_state):
    import dataclasses
    cache = ReadModelCache()
    e1 = sample_state.entities[1]
    ds = DirtySet(movement_entities={e1.id})

    state_a = dataclasses.replace(
        sample_state,
        entities={**sample_state.entities, e1.id: dataclasses.replace(e1, combat=dataclasses.replace(e1.combat, hp=100))},
        tick=1,
    )
    payload_a = cache.compute_tick_delta(state_a, ds, force_full_scan=False, tick=1)
    entry_a = next(c for c in payload_a["changed"] if c["id"] == e1.id)
    assert entry_a["hp"] == 100

    state_b = dataclasses.replace(
        sample_state,
        entities={**sample_state.entities, e1.id: dataclasses.replace(e1, combat=dataclasses.replace(e1.combat, hp=80))},
        tick=2,
    )
    payload_b = cache.compute_tick_delta(state_b, ds, force_full_scan=False, tick=2)
    entry_b = next(c for c in payload_b["changed"] if c["id"] == e1.id)
    assert entry_b["hp"] == 80


def test_compute_tick_delta_fields_present_and_correct(sample_state):
    cache = ReadModelCache()
    ds = DirtySet(movement_entities={1})
    payload = cache.compute_tick_delta(sample_state, ds, force_full_scan=False, tick=7)
    assert payload["tick"] == 7
    assert set(payload.keys()) == {"tick", "changed", "removed", "events"}


def test_compute_tick_delta_does_not_touch_entity_dtos_cache(sample_state):
    """Guard against slim/full DTO cache-key collision (test_plan.md Anti-Drift Test Guards)."""
    cache = ReadModelCache()
    e1 = sample_state.entities[1]
    cache.get_entity_dto(e1)
    assert cache.get_metrics()["cached_entities"] == 1

    ds = DirtySet(movement_entities={e1.id})
    cache.compute_tick_delta(sample_state, ds, force_full_scan=False, tick=1)

    assert cache.get_metrics()["cached_entities"] == 1
    assert cache.get_entity_dto(e1) is cache.get_entity_dto(e1)
