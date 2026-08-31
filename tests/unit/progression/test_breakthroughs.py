import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, AttributeComponent
from src.core.updates import EntityUpdate, IdentityUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder
from src.progression.breakthroughs import BreakthroughService

def test_breakthrough_addition():
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()
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
    entity = V2EntityBuilder(entity_id=1).identity(role=0).build()
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


def test_apply_bonuses_iron_will_returns_spirit_wisdom_plus_two():
    base_attributes = AttributeComponent(spirit=5, wisdom=5)
    result = BreakthroughService.apply_bonuses({"iron_will"}, base_attributes)
    assert result.spirit == base_attributes.spirit + 2
    assert result.wisdom == base_attributes.wisdom + 2
    assert result.strength == base_attributes.strength
    assert result.agility == base_attributes.agility
    assert result.vitality == base_attributes.vitality


def test_apply_bonuses_sums_multiple_breakthrough_ids():
    base_attributes = AttributeComponent(spirit=5, wisdom=5, strength=5)
    result = BreakthroughService.apply_bonuses({"iron_will", "titan_grip"}, base_attributes)
    assert result.spirit == base_attributes.spirit + 2
    assert result.wisdom == base_attributes.wisdom + 2
    assert result.strength == base_attributes.strength + 4


def test_apply_bonuses_empty_ids_returns_unchanged():
    base_attributes = AttributeComponent(spirit=5, wisdom=5, strength=5)
    result = BreakthroughService.apply_bonuses(set(), base_attributes)
    assert result == base_attributes


def test_apply_bonuses_unknown_id_returns_unchanged_no_raise():
    base_attributes = AttributeComponent(spirit=5, wisdom=5, strength=5)
    result = BreakthroughService.apply_bonuses({"nonexistent_breakthrough_xyz"}, base_attributes)
    assert result == base_attributes


def test_apply_bonuses_mixed_known_and_unknown_ids():
    base_attributes = AttributeComponent(spirit=5, wisdom=5, strength=5)
    result = BreakthroughService.apply_bonuses({"iron_will", "nonexistent_xyz"}, base_attributes)
    assert result.spirit == base_attributes.spirit + 2
    assert result.wisdom == base_attributes.wisdom + 2
    assert result.strength == base_attributes.strength
