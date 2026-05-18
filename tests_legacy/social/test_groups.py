import pytest
from src_legacy.core.state import AuthoritativeState, GroupRecord
from src_legacy.core.updates import StateUpdate
from src_legacy.engine.apply import ApplyPath
from src_legacy.core.builder import V2EntityBuilder

def test_group_formation():
    # Create two heroes
    h1 = V2EntityBuilder(entity_id=1).role(0).build()
    h2 = V2EntityBuilder(entity_id=2).role(0).build()
    
    state = AuthoritativeState(tick=0, seed=1, entities={1: h1, 2: h2})
    
    # Form a group
    group = GroupRecord(
        id=100,
        leader_id=1,
        member_ids={1, 2},
        anchor=(10.0, 10.0),
        roles={1: "TANK", 2: "HEALER"}
    )
    
    state_upd = StateUpdate(groups_add_or_update=[group])
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    
    assert 100 in new_state.groups
    assert new_state.groups[100].leader_id == 1
    assert "TANK" in new_state.groups[100].roles.values()
    assert new_state.groups[100].roles[2] == "HEALER"

def test_group_dissolution():
    group = GroupRecord(id=100, leader_id=1, member_ids={1}, anchor=(0, 0))
    state = AuthoritativeState(tick=0, seed=1, entities={}, groups={100: group})
    
    state_upd = StateUpdate(groups_remove=[100])
    
    new_state = ApplyPath.apply_generation(state, state_upd)
    
    assert 100 not in new_state.groups

def test_group_cohesion():
    from src_legacy.social.group_service import GroupService
    # h1 is inside (10, 10), h2 is outside (50, 50)
    h1 = V2EntityBuilder(entity_id=1).role(0).at((10.0, 10.0)).build()
    h2 = V2EntityBuilder(entity_id=2).role(0).at((50.0, 50.0)).build()
    
    group = GroupRecord(
        id=100,
        leader_id=1,
        member_ids={1, 2},
        anchor=(10.0, 10.0),
        cohesion_radius=5.0
    )
    
    state = AuthoritativeState(tick=0, seed=1, entities={1: h1, 2: h2}, groups={100: group})
    
    cohesion = GroupService.calculate_cohesion(group, state)
    # Only h1 is inside
    assert cohesion == 0.5
