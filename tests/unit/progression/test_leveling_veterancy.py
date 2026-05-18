import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, IdentityComponent, BiologicalComponent
from src.core.updates import StateUpdate, EntityUpdate, IdentityUpdate
from src.engine.apply import ApplyPath
from src.engine.evolution import EvolutionSystem
from src.core.builder import V2EntityBuilder

def test_level_cap_100():
    """Verify that level is capped at 100 even with massive XP."""
    # Create entity at level 99
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()
    entity = replace(entity, identity=replace(entity.identity, evolution_level=99, evolution_points=0))

    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})

    # Give massive XP
    update = EntityUpdate(
        entity_id=1,
        identity=IdentityUpdate(evolution_points_delta=1000000)
    )
    state_upd = StateUpdate(entity_updates={1: update})

    # Call EvolutionSystem directly (bypassing Pipeline sanitizer which strips proposed identity)
    refined = EvolutionSystem.evaluate(state, state_upd)
    new_state = ApplyPath.apply_generation(state, refined)

    final_identity = new_state.entities[1].identity
    assert final_identity.evolution_level == 100
    # XP should be capped at 0 (or what's left after reaching 100)
    assert final_identity.evolution_points == 0

def test_veterancy_progression():
    """Verify rank progression through multiple ranks."""
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})

    # Rank 0 -> 1 requires 10 points
    update = EntityUpdate(
        entity_id=1,
        identity=IdentityUpdate(veterancy_points_delta=15)
    )
    state_upd = StateUpdate(entity_updates={1: update})

    # Veterancy is applied in ApplyPath directly for now in V2
    new_state = ApplyPath.apply_generation(state, state_upd)

    ident = new_state.entities[1].identity
    assert ident.veterancy_rank == 1
    assert ident.veterancy_points == 5

def test_veterancy_multi_rank():
    """Verify multiple rank-ups in a single tick."""
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})

    # Rank 0->1 (10), Rank 1->2 (20) = Total 30
    update = EntityUpdate(
        entity_id=1,
        identity=IdentityUpdate(veterancy_points_delta=35)
    )
    state_upd = StateUpdate(entity_updates={1: update})

    new_state = ApplyPath.apply_generation(state, state_upd)

    ident = new_state.entities[1].identity
    assert ident.veterancy_rank == 2
    assert ident.veterancy_points == 5
