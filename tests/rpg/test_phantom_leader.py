import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, GroupRecord, InventoryComponent, CombatComponent
from src.core.updates import StateUpdate, EntityUpdate, CombatUpdate
from src.systems.groups import GroupSystem
from src.engine.pipeline import AuthoritativeApplyPipeline

@pytest.fixture
def group_state():
    # Setup a leader and a member in a group
    from src.core.builder import V2EntityBuilder
    leader = (V2EntityBuilder(1)
        .kind("hero")
        .at((0.0, 0.0))
        .with_combat(hp=10, alive=True)
        .group_id(101)
        .build()
    )
    member = (V2EntityBuilder(2)
        .kind("hero")
        .at((1.0, 1.0))
        .with_combat(hp=20, alive=True)
        .group_id(101)
        .build()
    )
    group = GroupRecord(
        id=101, leader_id=1, member_ids={1, 2}, anchor=(0.5, 0.5)
    )
    
    return AuthoritativeState(
        tick=1, seed=42,
        entities={1: leader, 2: member},
        groups={101: group}
    )

def test_phantom_leader_bug(group_state):
    """
    Verify that if a leader dies in the same tick, the group is dissolved.
    Currently, GroupSystem only looks at the start-of-tick state, so it will fail this.
    """
    # 1. Propose an update where the leader dies
    leader_death_upd = EntityUpdate(
        entity_id=1,
        combat=CombatUpdate(alive_set=False, outcome_kind="DEFEAT")
    )
    update = StateUpdate(entity_updates={1: leader_death_upd})
    
    # 2. Run GroupSystem.update_groups (simulating the pipeline call)
    group_upd = GroupSystem.update_groups(group_state, update)
    
    assert 101 in group_upd.groups_remove, "Group should be removed if leader is dead in the same tick"

def test_phantom_member_removal(group_state):
    """
    Verify that if a member dies in the same tick, they are removed from the group.
    """
    # 1. Propose an update where the member dies
    member_death_upd = EntityUpdate(
        entity_id=2,
        combat=CombatUpdate(alive_set=False, outcome_kind="DEFEAT")
    )
    update = StateUpdate(entity_updates={2: member_death_upd})
    
    # 2. Run GroupSystem.update_groups
    group_upd = GroupSystem.update_groups(group_state, update)
    
    # Member 2 should have group_id_set=-1
    assert 2 in group_upd.entity_updates
    assert group_upd.entity_updates[2].group_id_set == -1
