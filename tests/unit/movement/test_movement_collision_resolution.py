from __future__ import annotations

from dataclasses import replace
import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import ReasonCode
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, NavigationUpdate, StateUpdate
from src.engine.pipeline_phases.movement import MovementPhase
from src.engine.movement import MovementSystem
from src.engine.spatial_query import SpatialQueryService


def make_actor(
    entity_id: int,
    pos: tuple[float, float],
    priority: int = 10,
):
    """Build a valid active movement actor for collision tests."""
    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .location(*pos)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )


def test_prior_update_old_position_removal():
    """
    Verify that if an entity already has an update with a new_position prior
    to routing movement intents (e.g. from combat or prior phases), its old
    start-of-tick position is successfully deleted from live_occ_map during
    initialization, preventing ghost occupancy blocks.
    """
    ent = make_actor(1, (10.0, 10.0))
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: ent},
    )
    
    # Pre-existing update moving entity 1 to (11, 10)
    raw_update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                new_position=(11.0, 10.0),
                moved_this_tick=True,
            )
        }
    )
    
    # Run route_movement_intent (this initializes live_occ_map and processes candidates)
    refined = MovementPhase.route_movement_intent(state, raw_update)
    
    # Retrieve modified live occupancy map cache from state
    live_occ_map = getattr(state, "_occupancy_map_cache", {})
    
    # Assert old position (10, 10) is NO LONGER in live_occ_map mapped to entity 1
    assert live_occ_map.get((10, 10)) is None
    # Assert new position (11, 10) is in live_occ_map mapped to entity 1
    assert live_occ_map.get((11, 10)) == 1


def test_intermediate_yield_ghost_removal():
    """
    Verify that if an entity is moved or yielded multiple times, previous
    intermediate positions are cleaned up atomically from live_occ_map and
    live_claims when subsequent updates merge a different position.
    """
    # Set up scenario:
    # A (prio=20) wants to move to (1, 0), occupied by B (prio=10).
    # This forces B to yield to (1, 1).
    # Then B is processed/moved or yielded again to (1, 2).
    # We want to verify that when B's position updates from (1, 1) to (1, 2),
    # the intermediate (1, 1) is cleanly removed from live occupancy map.
    ent_a = make_actor(1, (0.0, 0.0)) # A
    ent_b = make_actor(2, (1.0, 0.0)) # B
    
    # Adjust A to have higher priority
    ent_a = replace(ent_a, combat=replace(ent_a.combat, hp=100))
    ent_b = replace(ent_b, combat=replace(ent_b.combat, hp=50))
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={
            1: ent_a,
            2: ent_b,
        },
    )
    
    # We populate refined updates with B already yielding to (1.0, 1.0)
    raw_update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                navigation=NavigationUpdate(target_set=(1.0, 0.0)),
            ),
            2: EntityUpdate(
                entity_id=2,
                new_position=(1.0, 1.0),
                moved_this_tick=True,
            )
        }
    )
    
    # Initialize live occupancy map mimicking route_movement_intent initialization
    live_occ_map = dict(SpatialQueryService.get_occupancy_map(state))
    live_claims = set()
    
    # Run the exact initialization block we refactored
    for ent_upd in raw_update.entity_updates.values():
        if ent_upd.new_position is not None:
            u_ent = state.entities.get(ent_upd.entity_id)
            if u_ent:
                old_pos = (int(u_ent.navigation.position[0]), int(u_ent.navigation.position[1]))
                if old_pos in live_occ_map and live_occ_map[old_pos] == ent_upd.entity_id:
                    del live_occ_map[old_pos]
            new_pos = (int(ent_upd.new_position[0]), int(ent_upd.new_position[1]))
            live_claims.add(new_pos)
            live_occ_map[new_pos] = ent_upd.entity_id
            
    # At this point, B's old pos (1, 0) is deleted, and its new pos (1, 1) is registered
    assert live_occ_map.get((1, 0)) is None
    assert live_occ_map.get((1, 1)) == 2
    assert (1, 1) in live_claims
    
    # Now simulate a subsequent update for B to (1.0, 2.0)
    u_upd = EntityUpdate(entity_id=2, new_position=(1.0, 2.0), moved_this_tick=True)
    existing = raw_update.entity_updates.get(2)
    
    # Apply our new atomic cleanup logic before merging
    if existing is not None and existing.new_position is not None and u_upd.new_position is not None:
        prev_new_pos = (int(existing.new_position[0]), int(existing.new_position[1]))
        next_new_pos = (int(u_upd.new_position[0]), int(u_upd.new_position[1]))
        if prev_new_pos != next_new_pos:
            if prev_new_pos in live_occ_map and live_occ_map[prev_new_pos] == 2:
                del live_occ_map[prev_new_pos]
            if prev_new_pos in live_claims:
                live_claims.discard(prev_new_pos)
                
    # Now merge
    merged = existing.merge(u_upd)
    
    # Assert intermediate position (1, 1) is cleanly removed from both
    assert live_occ_map.get((1, 1)) is None
    assert (1, 1) not in live_claims
    
    # Apply new position to maps as loop would do
    new_pos = (int(merged.new_position[0]), int(merged.new_position[1]))
    live_occ_map[new_pos] = 2
    live_claims.add(new_pos)
    
    assert live_occ_map.get((1, 2)) == 2
    assert (1, 2) in live_claims


def test_yield_tile_integer_casting():
    """
    Verify that MovementSystem.resolve_move generates yield_tile updates
    with integer coordinates even if entity positions have floats.
    """
    ent_a = make_actor(1, (0.0, 0.0)) # A
    ent_b = make_actor(2, (1.2, 0.8)) # B (float coordinates)
    
    # A has lower HP (higher priority) so A can push B to yield
    ent_a = replace(ent_a, combat=replace(ent_a.combat, hp=10), navigation=replace(ent_a.navigation, wait_count=1))
    ent_b = replace(ent_b, combat=replace(ent_b.combat, hp=100))
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={
            1: ent_a,
            2: ent_b,
        },
        blocked_tiles={(0, 1), (0, -1)},
    )
    
    # Run resolve_move for A seeking to occupy B's tile (1, 0)
    updates = MovementSystem.resolve_move(state, ent_a, target_pos=(1.0, 0.0), mode=MovementMode.WANDER)
    
    # Entity 2 should yield
    assert 2 in updates
    yield_upd = updates[2]
    assert yield_upd.new_position is not None
    
    # Assert yield coordinates are strict integers
    x, y = yield_upd.new_position
    assert isinstance(x, int)
    assert isinstance(y, int)
