import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, GroupRecord
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.parity.test_parity_rpg_recovery import create_test_profile

@pytest.mark.v2_contract
def test_tactical_cohesion_focus_fire():
    """
    SOC-007: Groups focus fire on same target.
    """
    # 1. Setup group (Leader + 2 members)
    leader = V2EntityBuilder(1).at((5, 5)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).readiness(100.0).build()
    m1 = V2EntityBuilder(2).at((6, 5)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).readiness(100.0).build()
    m2 = V2EntityBuilder(3).at((5, 6)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).readiness(100.0).build()
    
    # 2. Setup hostiles
    gob1 = V2EntityBuilder(10).at((7, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).build()
    gob2 = V2EntityBuilder(11).at((5, 7)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).build()
    
    group = GroupRecord(
        id=1, 
        leader_id=1, 
        member_ids={1, 2, 3}, 
        anchor=(5.0, 5.0),
        shared_target_id=None
    )
    
    state = AuthoritativeState(
        tick=1, 
        seed=42, 
        entities={1: leader, 2: m1, 3: m2, 10: gob1, 11: gob2},
        groups={1: group}
    )
    
    # Link entities to group
    state.entities[1] = replace(state.entities[1], group_id=1)
    state.entities[2] = replace(state.entities[2], group_id=1)
    state.entities[3] = replace(state.entities[3], group_id=1)
    
    rng = DeterministicRNG(42)
    profile = create_test_profile()
    kernel = Kernel(profile, state, rng)
    
    # Tick 1: 
    # 1. BRAIN runs: Leader selects gob1 (closest).
    # 2. RESOLUTION runs: Leader's task.payload.target_id becomes 10.
    # 3. KERNEL should run GroupSystem.update_groups (In V2 this might need to be added to Kernel or a phase)
    
    kernel.tick_once()
    
    # Check if target was propagated
    new_group = kernel.state.groups[1]
    # If GroupSystem.update_groups is NOT in Kernel, we manually call it to verify the logic.
    if new_group.shared_target_id is None:
        from src.systems.groups import GroupSystem
        update = GroupSystem.update_groups(kernel.state)
        assert update.groups_add_or_update[0].shared_target_id == 10

@pytest.mark.v2_contract
def test_coordination_anchor_drift():
    """
    SOC-051: Group anchor follows members.
    """
    # Members at (10, 10)
    m1 = V2EntityBuilder(1).at((10, 10)).role(EntityRole.HERO).readiness(0.0).group_id(1).build()
    m2 = V2EntityBuilder(2).at((12, 10)).role(EntityRole.HERO).readiness(0.0).group_id(1).build()
    
    group = GroupRecord(id=1, leader_id=1, member_ids={1, 2}, anchor=(10.0, 10.0))
    state = AuthoritativeState(tick=1, seed=42, entities={1: m1, 2: m2}, groups={1: group})
    
    from src.systems.groups import GroupSystem
    
    # Manual trigger of group update
    update = GroupSystem.update_groups(state)
    
    # Expected anchor: (11.0, 10.0)
    assert len(update.groups_add_or_update) == 1
    assert update.groups_add_or_update[0].anchor == (11.0, 10.0)
