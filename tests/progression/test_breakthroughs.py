import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate, IdentityUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder

def test_breakthrough_addition():
    entity = V2EntityBuilder(entity_id=1).role(0).build()
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    # Add breakthrough
    update = EntityUpdate(
        entity_id=1,
        identity=IdentityUpdate(breakthroughs_add=["iron_will"])
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    
    ident = new_state.entities[1].identity
    assert "iron_will" in ident.active_breakthroughs

def test_duplicate_breakthrough_suppression():
    entity = V2EntityBuilder(entity_id=1).role(0).build()
    entity = replace(entity, identity=replace(entity.identity, active_breakthroughs={"iron_will"}))
    state = AuthoritativeState(tick=0, seed=1, entities={1: entity})
    
    # Add same breakthrough again
    update = EntityUpdate(
        entity_id=1,
        identity=IdentityUpdate(breakthroughs_add=["iron_will"])
    )
    state_upd = StateUpdate(entity_updates={1: update})
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    
    ident = new_state.entities[1].identity
    assert len(ident.active_breakthroughs) == 1
    assert "iron_will" in ident.active_breakthroughs
