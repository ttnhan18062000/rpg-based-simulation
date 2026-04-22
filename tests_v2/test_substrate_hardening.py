import pytest
from src_v2.core.state import AuthoritativeState, EntityState, IdentityComponent, NavigationComponent, TaskComponent, CombatComponent
from src_v2.core.updates import StateUpdate, EntityUpdate, NavigationUpdate, TaskUpdate, CombatUpdate
from src_v2.engine.apply import ApplyPath

def test_navigation_intent_hardening():
    """Verify that navigation intent is preserved across generations via typed components."""
    # Setup state with a navigation target
    ent = EntityState(
        id=1, kind="HERO", position=(0, 0),
        navigation=NavigationComponent(target=(5, 5))
    )
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
    ent = EntityState(
        id=1, kind="HERO", position=(0, 0),
        task=TaskComponent(work_kind="OLD_ACT", payload={"key": "old"})
    )
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
    ent = EntityState(id=1, kind="HERO", position=(0, 0))
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
