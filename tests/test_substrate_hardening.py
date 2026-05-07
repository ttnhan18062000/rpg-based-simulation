import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, NavigationComponent, TaskComponent, CombatComponent
from src.core.updates import StateUpdate, EntityUpdate, NavigationUpdate, TaskUpdate, CombatUpdate
from src.engine.apply import ApplyPath

def test_navigation_intent_hardening():
    """Verify that navigation intent is preserved across generations via typed components."""
    # Setup state with a navigation target
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .navigation(target=(5, 5))
        .build())
    state = AuthoritativeState(tick=0, seed=1, entities={1: ent})
    
    # Update position and set a new path
    upd = EntityUpdate(
        entity_id=1,
        new_position=(1, 0),
        navigation=NavigationUpdate(path_set=[(2, 0), (3, 0)])
    )
    state_upd = StateUpdate(entity_updates={1: upd})
    
    next_state = ApplyPath.apply_generation(state, state_upd, 1, 1000)
    
    # Verify
    new_ent = next_state.entities[1]
    assert new_ent.position == (1, 0)
    assert new_ent.navigation.target == (5, 5) # Preserved
    assert new_ent.navigation.path == [(2, 0), (3, 0)] # Updated

def test_task_intent_hardening():
    """Verify that task intent is preserved across generations via typed components."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .task(work_kind="OLD_ACT", payload={"key": "old"})
        .build())
    state = AuthoritativeState(tick=0, seed=1, entities={1: ent})
    
    upd = EntityUpdate(
        entity_id=1,
        task=TaskUpdate(work_kind_set="NEW_ACT")
    )
    state_upd = StateUpdate(entity_updates={1: upd})
    
    next_state = ApplyPath.apply_generation(state, state_upd, 1, 1000)
    
    new_ent = next_state.entities[1]
    assert new_ent.task.work_kind == "NEW_ACT"
    assert new_ent.task.payload == {"key": "old"} # Preserved

def test_property_bypass_elimination():
    """Ensure that properties are not contaminated by typed state updates."""
    ent = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .build())
    state = AuthoritativeState(tick=0, seed=1, entities={1: ent})
    
    # Attempt to update HP via CombatUpdate
    upd = EntityUpdate(
        entity_id=1,
        combat=CombatUpdate(hp_delta=-10)
    )
    state_upd = StateUpdate(entity_updates={1: upd})
    
    next_state = ApplyPath.apply_generation(state, state_upd, 1, 1000)
    
    new_ent = next_state.entities[1]
    assert new_ent.combat.hp == 90
    assert "hp" not in new_ent.properties # Should NOT be in properties
