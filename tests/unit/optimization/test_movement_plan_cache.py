# Compliance IDs: COMB-011, PERF-009
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.dirty import DirtySet
from src.core.enums import EntityRole, ReasonCode
from src.core.movement_modes import MovementMode
from src.engine.movement_cache import MovementPlanCache, MovementPlanKey, MovementPlan
from src.engine.movement import MovementSystem


@pytest.fixture
def cache() -> MovementPlanCache:
    return MovementPlanCache()


@pytest.fixture
def base_state() -> AuthoritativeState:
    e1 = (
        V2EntityBuilder(1)
        .kind("ACTOR")
        .location(10.0, 10.0)
        .navigation(target=(20.0, 20.0), movement_mode=MovementMode.WANDER)
        .combat(alive=True, readiness=20.0, move_cost=10.0)
        .lifecycle(active=True)
        .build()
    )

    state = AuthoritativeState(tick=100, seed=42, world_time=100, entities={1: e1})
    object.__setattr__(state, "movement_cache", MovementPlanCache())
    return state


def test_plan_cache_reuses_plan_when_key_unchanged(cache: MovementPlanCache):
    key = MovementPlanKey(entity_id=1, current_tile=(10, 10), target_tile=(20, 20), occupancy_version=0)
    plan = MovementPlan(next_step=(11.0, 10.0), valid_until_tick=105)

    cache.put(key, plan)
    
    # Hit at tick 100
    assert cache.get(key, current_tick=100) == plan
    # Hit at tick 105
    assert cache.get(key, current_tick=105) == plan
    # Miss at tick 106 (Expired)
    assert cache.get(key, current_tick=106) is None


def test_plan_cache_invalidates_when_entity_moves(cache: MovementPlanCache):
    key = MovementPlanKey(entity_id=1, current_tile=(10, 10), target_tile=(20, 20), occupancy_version=0)
    plan = MovementPlan(next_step=(11.0, 10.0), valid_until_tick=105)
    cache.put(key, plan)

    assert cache.get(key, 100) == plan

    # Invalidate with entity 1 moving
    dirty = DirtySet(movement_entities={1})
    cache.invalidate_for_dirty(dirty)

    # Cache should be evicted and occupancy_version incremented
    assert cache.occupancy_version == 1
    assert cache.get(key, 100) is None


def test_plan_cache_invalidates_when_target_changes(cache: MovementPlanCache):
    key1 = MovementPlanKey(entity_id=1, current_tile=(10, 10), target_tile=(20, 20), occupancy_version=0)
    key2 = MovementPlanKey(entity_id=1, current_tile=(10, 10), target_tile=(30, 30), occupancy_version=0)
    plan = MovementPlan(next_step=(11.0, 10.0), valid_until_tick=105)
    
    cache.put(key1, plan)
    
    assert cache.get(key1, 100) == plan
    assert cache.get(key2, 100) is None


def test_plan_cache_invalidates_when_occupancy_version_changes(cache: MovementPlanCache):
    key = MovementPlanKey(entity_id=1, current_tile=(10, 10), target_tile=(20, 20), occupancy_version=0)
    plan = MovementPlan(next_step=(11.0, 10.0), valid_until_tick=105)
    cache.put(key, plan)

    # Another entity moves, incrementing occupancy version
    dirty = DirtySet(movement_entities={2})
    cache.invalidate_for_dirty(dirty)

    assert cache.occupancy_version == 1
    # Key had version 0, should miss
    assert cache.get(key, 100) is None


def test_plan_cache_does_not_reuse_blocked_step(base_state: AuthoritativeState):
    # Block tile (11, 10)
    base_state.blocked_tiles.add((11, 10))

    updates = MovementSystem.resolve_move(base_state, base_state.entities[1], (20.0, 10.0), mode=MovementMode.WANDER)
    upd = updates[1]
    
    # Verify move failed or sidestepped, and blocked tile was not cached as next_step
    key = MovementPlanKey(entity_id=1, current_tile=(10, 10), target_tile=(20, 10), occupancy_version=base_state.movement_cache.occupancy_version)
    plan = base_state.movement_cache.get(key, base_state.tick)
    
    if plan is not None:
        assert plan.next_step != (11.0, 10.0)


def test_cached_movement_plan_matches_uncached_resolution(base_state: AuthoritativeState):
    target = (20.0, 10.0)
    # First call: Uncached
    res1 = MovementSystem.resolve_move(base_state, base_state.entities[1], target, mode=MovementMode.WANDER)
    
    # Check that it got cached
    key = MovementPlanKey(entity_id=1, current_tile=(10, 10), target_tile=(20, 10), occupancy_version=base_state.movement_cache.occupancy_version)
    cached = base_state.movement_cache.get(key, base_state.tick)
    assert cached is not None
    assert cached.next_step == (11.0, 10.0)

    # Second call: Uses cache
    res2 = MovementSystem.resolve_move(base_state, base_state.entities[1], target, mode=MovementMode.WANDER)
    
    assert res1[1].new_position == res2[1].new_position
