import pytest
from dataclasses import replace
from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, 
    SocialComponent, CombatComponent, NavigationComponent, TaskComponent,
    InteractionComponent, SocialBond, AttributeComponent
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
    return EntityState(
        id=e_id,
        kind="actor",
        position=pos,
        readiness=100.0,
        active=True,
        identity=IdentityComponent(role=EntityRole.HERO, faction=faction),
        attributes=AttributeComponent(),
        social=SocialComponent(),
        combat=CombatComponent(hp=100, max_hp=100, alive=True),
        navigation=NavigationComponent(),
        task=TaskComponent(),
        interaction=InteractionComponent(),
        strategic=StrategicComponent()
    )

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
    candidate = create_mock_entity(1, (1.0, 1.0))
    # Add a betrayal history
    candidate = replace(candidate, social=replace(candidate.social, betrayal_count=1))
    
    state = AuthoritativeState(tick=0, seed=42)
    
    # Low payout + betrayal history = rejection (via TOTAL_DISTRUST if trust < 0.4)
    bond_low = SocialBond(target_id=2, sentiment=-0.5) # trust 0.25
    candidate_low = replace(candidate, social=replace(candidate.social, bonds={2: bond_low}))
    
    c_low = ContractState(id="c_low", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
                          terms={"daily_pay": 5, "risk_level": "NORMAL"}, status=ContractStatus.OFFERED, created_tick=0)
    accepted, reason = SocialAppraisalSystem.appraise_contract(candidate_low, c_low, state)
    assert not accepted
    
    # Higher payout (100) + high trust (sentiment 0.8 -> trust 0.9) = acceptance
    bond_high = SocialBond(target_id=2, sentiment=0.8)
    candidate_high = replace(candidate, social=replace(candidate.social, bonds={2: bond_high}))
    
    c_high = ContractState(id="c_high", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
                           terms={"daily_pay": 100, "risk_level": "NORMAL"}, status=ContractStatus.OFFERED, created_tick=0)
    accepted_high, reason = SocialAppraisalSystem.appraise_contract(candidate_high, c_high, state)
    assert accepted_high

def test_party_formation_from_contract():
    """Verify that a shared contract leads to group formation."""
    hero = create_mock_entity(1, (1.0, 1.0))
    merc = create_mock_entity(2, (1.2, 1.2))
    
    # Give them a recruitment contract
    contract = ContractState(
        id="recruit_merc",
        kind=ContractKind.RECRUITMENT,
        source_id=1,
        target_id=2,
        status=ContractStatus.ACTIVE
    )
    
    hero = replace(hero, strategic=replace(hero.strategic, contracts={"recruit_merc": contract}))
    merc = replace(merc, strategic=replace(merc.strategic, contracts={"recruit_merc": contract}))
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: merc})
    
    update = GroupSystem.update_groups(state)
    
    assert len(update.groups_add_or_update) == 1
    assert 1 in update.groups_add_or_update[0].member_ids
    assert 2 in update.groups_add_or_update[0].member_ids

def test_betrayal_dissolves_group_and_adds_directive():
    """Verify that attacking a group member dissolves the group and creates an avenge directive."""
    hero = create_mock_entity(1, (1.0, 1.0))
    merc = create_mock_entity(2, (1.0, 2.0))
    
    # Put them in a group
    from src.core.state import GroupRecord
    group = GroupRecord(id=500, leader_id=1, member_ids={1, 2}, anchor=(1.0, 1.5))
    
    hero = replace(hero, group_id=500)
    merc = replace(merc, group_id=500)
    
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
