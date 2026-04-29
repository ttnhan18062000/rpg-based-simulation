"""
Party agency and leadership tests.
- RPG-0058: social_party_cooperation
"""
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, GroupRecord, EntityState, IdentityComponent, CombatComponent, StrategicComponent, InventoryComponent
from src.core.enums import EntityRole
from src.systems.groups import GroupSystem
from src.core.updates import StateUpdate, EntityUpdate

def create_mock_entity(id, pos=(0,0), hp=100):
    return EntityState(
        id=id,
        kind="ACTOR",
        position=pos,
        identity=IdentityComponent(faction="HERO_FACTION", role=EntityRole.HERO),
        combat=CombatComponent(hp=hp, max_hp=100, atk=10, range=1, alive=hp > 0),
        readiness=100.0,
        active=True,
        inventory=InventoryComponent(max_slots=10, max_weight=100.0),
        strategic=StrategicComponent()
    )

def test_party_leadership_loss_dissolution():
    """
    Law: If the leader dies or is removed, the group dissolves.
    RPG-1676: group_dissolution_leader_loss
    """
    h1 = create_mock_entity(1, pos=(0,0), hp=100) # Leader
    h2 = create_mock_entity(2, pos=(1,1), hp=100) # Member
    
    group = GroupRecord(
        id=100,
        leader_id=1,
        member_ids={1, 2},
        anchor=(0,0)
    )
    
    state = AuthoritativeState(tick=1, seed=1, entities={1: h1, 2: h2}, groups={100: group})
    
    # 1. Kill the leader
    h1_dead = replace(h1, combat=replace(h1.combat, hp=0, alive=False))
    state_dead_leader = replace(state, entities={1: h1_dead, 2: h2})
    
    update = GroupSystem.update_groups(state_dead_leader)
    
    assert 100 in update.groups_remove
    assert update.entity_updates[1].group_id_set == -1
    assert update.entity_updates[2].group_id_set == -1

def test_party_agency_target_propagation():
    """
    Law: Group members inherit the shared target from the leader.
    """
    from src.core.updates import TaskUpdate
    h1 = create_mock_entity(1, pos=(0,0))
    # Leader has a target in task payload
    h1 = replace(h1, task=replace(h1.task, payload={"target_id": 999}))
    h2 = create_mock_entity(2, pos=(1,1))
    
    group = GroupRecord(
        id=100,
        leader_id=1,
        member_ids={1, 2},
        anchor=(0,0)
    )
    
    state = AuthoritativeState(tick=1, seed=1, entities={1: h1, 2: h2}, groups={100: group})
    
    update = GroupSystem.update_groups(state)
    
    # Updated group should have shared_target_id=999
    assert update.groups_add_or_update[0].shared_target_id == 999

def test_party_member_abandonment_on_distance():
    """
    Law: Members too far from the anchor are removed from the group.
    RPG-1674: group_cohesion_check
    """
    h1 = create_mock_entity(1, pos=(0,0)) # Leader at anchor
    h2 = create_mock_entity(2, pos=(100,100)) # Way too far (cohesion is 5.0)
    
    group = GroupRecord(
        id=100,
        leader_id=1,
        member_ids={1, 2},
        anchor=(0,0),
        cohesion_radius=5.0
    )
    
    state = AuthoritativeState(tick=1, seed=1, entities={1: h1, 2: h2}, groups={100: group})
    
    update = GroupSystem.update_groups(state)
    
    # Since h2 is gone, only h1 remains. 
    # But a group needs >= 2 members (line 74 in groups.py)
    # So the group dissolves.
    assert 100 in update.groups_remove
    assert update.entity_updates[2].group_id_set == -1
