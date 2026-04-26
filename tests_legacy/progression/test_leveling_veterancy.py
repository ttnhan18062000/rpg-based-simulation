import pytest
from dataclasses import replace
from src_legacy.core.state import EntityState, IdentityComponent, CombatComponent, AuthoritativeState
from src_legacy.core.updates import EntityUpdate, IdentityUpdate, StateUpdate
from src_legacy.engine.apply import ApplyPath
from src_legacy.progression.leveling import LevelingService
from src_legacy.progression.veterancy import VeterancyService
from src_legacy.core.builder import V2EntityBuilder

def test_level_cap_100():
    # Create entity at level 99
    entity = V2EntityBuilder(entity_id=1).role(0).build()
    entity = replace(entity, identity=replace(entity.identity, evolution_level=99, evolution_points=0))
    
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    # Give massive XP
    update = EntityUpdate(
        entity_id=1,
        identity=IdentityUpdate(evolution_points_delta=1000000)
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    
    final_identity = new_state.entities[1].identity
    assert final_identity.evolution_level == 100
    assert final_identity.evolution_points == 0 # Clamped at cap

def test_veterancy_progression():
    entity = V2EntityBuilder(entity_id=1).role(0).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    # Rank 0 -> 1 requires 10 points
    update = EntityUpdate(
        entity_id=1,
        identity=IdentityUpdate(veterancy_points_delta=15)
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    
    ident = new_state.entities[1].identity
    assert ident.veterancy_rank == 1
    assert ident.veterancy_points == 5 # 15 - 10

def test_veterancy_multi_rank():
    entity = V2EntityBuilder(entity_id=1).role(0).build()
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
