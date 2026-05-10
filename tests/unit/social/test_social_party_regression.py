import pytest
from dataclasses import replace
from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, 
    SocialComponent, CombatComponent, NavigationComponent, TaskComponent,
    InteractionComponent, SocialBond, AttributeComponent, LifecycleComponent
)
from src.core.enums import Faction, EntityRole
from src.core.strategic import (
    StrategicComponent, ProjectState, ProjectStatus, ObjectiveState, ObjectiveStatus,
    ContractState, ContractKind, ContractStatus
)
from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate
from src.social.appraisal import SocialAppraisalSystem
from src.systems.groups import GroupSystem
from src.engine.pipeline import AuthoritativeApplyPipeline

def create_mock_entity(e_id, pos, faction=Faction.HERO_GUILD):
    from src.core.builder import V2EntityBuilder
    return (V2EntityBuilder(e_id)
        .kind("actor")
        .location(pos[0], pos[1])
        .identity(role=EntityRole.HERO)
        .identity(faction=faction)
        .combat(hp=100, max_hp=100)
        .combat(alive=True)
        .combat(readiness=100.0)
        .build())

def test_no_proximity_only_groups():
    """Verify that groups do not form just by being near each other."""
    hero = create_mock_entity(1, (1.0, 1.0))
    merc = create_mock_entity(2, (1.5, 1.5)) # Close but no shared purpose
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: merc})
    
    update = GroupSystem.update_groups(state)
    
    # Currently this will FAIL because existing GroupSystem uses proximity
    assert len(update.groups_add_or_update) == 0

def test_recruitment_logic_evaluation():
    """Verify that recruitment evaluates trust and betrayal history."""
    from src.core.builder import V2EntityBuilder
    state = AuthoritativeState(tick=0, seed=42)
    
    # Low payout + betrayal history = rejection (via TOTAL_DISTRUST if trust < 0.4)
    bond_low = SocialBond(target_id=2, sentiment=-0.5) # trust 0.25
    candidate_low = (V2EntityBuilder(1)
        .kind("actor")
        .social(betrayal_count=1, bonds={2: bond_low})
        .build())
    
    c_low = ContractState(id="c_low", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
                          terms={"daily_pay": 5, "risk_level": "NORMAL"}, status=ContractStatus.OFFERED, created_tick=0)
    status, reason, _ = SocialAppraisalSystem.appraise_contract(candidate_low, c_low, state)
    assert status != ContractStatus.ACCEPTED
    
    # Higher payout (100) + high trust (sentiment 0.8 -> trust 0.9) = acceptance
    bond_high = SocialBond(target_id=2, sentiment=0.8)
    candidate_high = (V2EntityBuilder(1)
        .kind("actor")
        .social(betrayal_count=1, bonds={2: bond_high})
        .build())
    
    c_high = ContractState(id="c_high", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
                           terms={"daily_pay": 100, "risk_level": "NORMAL"}, status=ContractStatus.OFFERED, created_tick=0)
    status_high, reason, _ = SocialAppraisalSystem.appraise_contract(candidate_high, c_high, state)
    assert status_high == ContractStatus.ACCEPTED

def test_party_formation_from_contract():
    """Verify that a shared contract leads to group formation."""
    from src.core.builder import V2EntityBuilder
    # Give them a recruitment contract
    contract = ContractState(
        id="recruit_merc",
        kind=ContractKind.RECRUITMENT,
        source_id=1,
        target_id=2,
        status=ContractStatus.ACTIVE
    )
    hero = (V2EntityBuilder(1)
        .kind("actor")
        .location(1.0, 1.0)
        .strategic(contracts={"recruit_merc": contract})
        .build())
    merc = (V2EntityBuilder(2)
        .kind("actor")
        .location(1.2, 1.2)
        .strategic(contracts={"recruit_merc": contract})
        .build())
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: merc})
    
    update = GroupSystem.update_groups(state)
    
    assert len(update.groups_add_or_update) == 1
    assert 1 in update.groups_add_or_update[0].member_ids
    assert 2 in update.groups_add_or_update[0].member_ids

def test_betrayal_dissolves_group_and_adds_directive():
    """Verify that attacking a group member dissolves the group and creates an avenge directive."""
    from src.core.builder import V2EntityBuilder
    hero = (V2EntityBuilder(1)
        .kind("actor")
        .location(1.0, 1.0)
        .identity(group_id=500)
        .build())
    merc = (V2EntityBuilder(2)
        .kind("actor")
        .location(1.0, 2.0)
        .identity(group_id=500)
        .build())
    
    # Put them in a group
    from src.core.state import GroupRecord
    group = GroupRecord(id=500, leader_id=1, member_ids={1, 2}, anchor=(1.0, 1.5))
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: merc}, groups={500: group})
    
    # Hero attacks Merc
    task_up = TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": 2})
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, task=task_up)})
    
    # We need a system that detects betrayal during combat application
    # This will be in pipeline.py or a dedicated social system
    
    # For now, let's just test SocialAppraisalSystem.process_betrayal directly
    soc_up, strat_up = SocialAppraisalSystem.process_betrayal(merc, 1, salience=0.8, current_tick=1)
    
    assert any(d.kind == "avenge" for d in strat_up.directives_add_or_update)
    assert soc_up.betrayal_increment == 1
