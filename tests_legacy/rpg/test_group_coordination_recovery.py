import pytest
from src_legacy.core.state import AuthoritativeState, EntityState, StrategicComponent, GroupRecord
from src_legacy.core.strategic import ProjectState, ProjectStatus
from src_legacy.core.enums import Faction
from src_legacy.core.state import IdentityComponent
from src_legacy.systems.groups import GroupSystem
from src_legacy.core.updates import StateUpdate, EntityUpdate

def test_purpose_driven_group_formation():
    """
    Law: Groups must form from shared purpose, not just proximity.
    """
    # 1. Setup: Two allies, near each other, but different purposes
    proj_a = ProjectState(id="proj_a", kind="harvesting", status=ProjectStatus.ACTIVE)
    proj_b = ProjectState(id="proj_b", kind="combat", status=ProjectStatus.ACTIVE)
    
    ent_a = EntityState(
        id=1, kind="HERO", position=(10, 10),
        identity=IdentityComponent(faction=Faction.HERO_GUILD),
        strategic=StrategicComponent(
            projects={"proj_a": proj_a},
            current_project_id="proj_a"
        )
    )
    ent_b = EntityState(
        id=2, kind="HERO", position=(11, 11),
        identity=IdentityComponent(faction=Faction.HERO_GUILD),
        strategic=StrategicComponent(
            projects={"proj_b": proj_b},
            current_project_id="proj_b"
        )
    )
    
    state = AuthoritativeState(tick=100, seed=1, entities={1: ent_a, 2: ent_b})
    
    # Run update_groups
    upd = GroupSystem.update_groups(state)
    
    # Verify NO group formed (different purposes)
    assert len(upd.groups_add_or_update) == 0
    
    # 2. Update B to have SAME purpose
    ent_b_same = replace(ent_b, strategic=replace(ent_b.strategic,
        projects={"proj_a": proj_a},
        current_project_id="proj_a"
    ))
    state_same = AuthoritativeState(tick=101, seed=1, entities={1: ent_a, 2: ent_b_same})
    
    upd_same = GroupSystem.update_groups(state_same)
    
    # Verify group formed
    assert len(upd_same.groups_add_or_update) == 1
    new_group = upd_same.groups_add_or_update[0]
    assert new_group.purpose == "harvesting"
    assert 1 in new_group.member_ids
    assert 2 in new_group.member_ids

def test_group_dissolution_on_purpose_change():
    """
    Law: Groups dissolve when purpose ends or changes.
    """
    # 1. Setup: Group with purpose "harvesting"
    proj_a = ProjectState(id="proj_a", kind="harvesting", status=ProjectStatus.ACTIVE)
    group = GroupRecord(
        id=1000, leader_id=1, member_ids={1, 2}, 
        anchor=(10, 10), purpose="harvesting"
    )
    
    ent_a = EntityState(
        id=1, kind="HERO", position=(10, 10), group_id=1000,
        identity=IdentityComponent(faction=Faction.HERO_GUILD),
        strategic=StrategicComponent(
            projects={"proj_a": proj_a},
            current_project_id="proj_a"
        )
    )
    ent_b = EntityState(
        id=2, kind="HERO", position=(11, 11), group_id=1000,
        identity=IdentityComponent(faction=Faction.HERO_GUILD),
        strategic=StrategicComponent(
            projects={"proj_a": proj_a},
            current_project_id="proj_a"
        )
    )
    
    state = AuthoritativeState(tick=200, seed=1, entities={1: ent_a, 2: ent_b}, groups={1000: group})
    
    # 2. Change leader A's purpose to "combat"
    proj_combat = ProjectState(id="proj_c", kind="combat", status=ProjectStatus.ACTIVE)
    ent_a_changed = replace(ent_a, strategic=replace(ent_a.strategic,
        projects={"proj_c": proj_combat},
        current_project_id="proj_c"
    ))
    
    state_changed = AuthoritativeState(tick=201, seed=1, entities={1: ent_a_changed, 2: ent_b}, groups={1000: group})
    
    upd = GroupSystem.update_groups(state_changed)
    
    # Verify group is removed
    assert 1000 in upd.groups_remove
    # Verify members have group_id reset
    assert upd.entity_updates[1].group_id_set == -1
    assert upd.entity_updates[2].group_id_set == -1

def replace(obj, **kwargs):
    from dataclasses import replace as dr
    return dr(obj, **kwargs)
