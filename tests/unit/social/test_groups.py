# Compliance IDs: SOC-191, SOC-225
"""
Group coordination tests.
- RPG-0058: social_party_cooperation
"""
import pytest
from src.core.state import AuthoritativeState, GroupRecord
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath
from src.core.builder import V2EntityBuilder

def test_group_formation():
    """Logic ID: SOC-166 (Contract party has founder/leader)"""
    # Create two heroes
    h1 = V2EntityBuilder(entity_id=1).identity(role=0).build()
    h2 = V2EntityBuilder(entity_id=2).identity(role=0).build()
    
    state = AuthoritativeState(tick=0, seed=1, entities={1: h1, 2: h2})
    
    # Form a group
    group = GroupRecord(
        id=100,
        leader_id=1,
        member_ids={1, 2},
        anchor=(10.0, 10.0),
        roles={1: "TANK", 2: "HEALER"}
    )
    # Logic ID: SOC-167 (Contract party has member roles)
    
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


def test_group_system_retains_dissolved_groups_with_terminal_marker_not_deleted():
    """TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED: GroupSystem.update_groups() itself
    now marks a dissolved group's own dissolution_tick in place (mirroring
    ClanState.dissolved_tick/CampState.active) rather than deleting it via groups_remove."""
    from src.systems.world_systems.groups import GroupSystem

    leader = V2EntityBuilder(1).identity(role=0).build()
    group = GroupRecord(id=100, leader_id=1, member_ids={1}, anchor=(0, 0))
    state = AuthoritativeState(tick=7, seed=1, entities={1: leader}, groups={100: group})

    # Single-member group (len(member_ids) < 2) dissolves on the very first pass.
    update = GroupSystem.update_groups(state)

    assert update.groups_remove == []
    dissolved = next(g for g in update.groups_add_or_update if g.id == 100)
    assert dissolved.dissolution_tick == 7

    final_state = ApplyPath.apply_generation(state, update)
    assert 100 in final_state.groups
    assert final_state.groups[100].dissolution_tick == 7


def test_group_system_skips_already_dissolved_groups_under_force_full_scan():
    """TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED: get_relevant_group_ids() falls back
    to ALL of state.groups.keys() on a force_full_scan tick (or when no dirty_set exists) --
    since dissolved groups are now retained forever, update_groups() must skip any group whose
    dissolution_tick is already set, or a full-scan tick would re-run dissolution/cohesion logic
    against every already-dissolved group, forever."""
    from src.systems.world_systems.groups import GroupSystem

    already_dissolved = GroupRecord(
        id=200, leader_id=1, member_ids={1}, anchor=(0, 0), dissolution_tick=3,
    )
    state = AuthoritativeState(tick=50, seed=1, entities={}, groups={200: already_dissolved})

    update = GroupSystem.update_groups(state, StateUpdate(force_full_scan=True))

    # Not touched at all -- no re-write, no re-dissolution, no entity updates for its (now
    # nonexistent) members.
    assert update.groups_add_or_update == []
    assert update.entity_updates == {}

def test_group_cohesion():
    """Logic ID: SOC-173 (Party cohesion is updated from member positions)"""
    from src.systems.social_systems.group_service import GroupService
    # h1 is inside (10, 10), h2 is outside (50, 50)
    h1 = V2EntityBuilder(entity_id=1).identity(role=0).location(10.0, 10.0).build()
    h2 = V2EntityBuilder(entity_id=2).identity(role=0).location(50.0, 50.0).build()
    
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
