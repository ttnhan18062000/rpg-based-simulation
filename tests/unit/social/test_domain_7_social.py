
import pytest
from dataclasses import replace
from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, CombatComponent,
    SocialComponent, SocialBond, TaskComponent, NavigationComponent,
    GroupRecord, StrategicComponent
)
from src.core.strategic import ContractState, ContractKind, ContractStatus, ProjectState, DirectiveState, ProjectStatus
from src.core.updates import StateUpdate, EntityUpdate, SocialUpdate
from src.social.appraisal import SocialAppraisalSystem
from src.systems.groups import GroupSystem
from src.engine.tactical import TacticalDecisionSystem
from src.engine.domain_logic import SimulationDomainLogic
from src.core.builder import V2EntityBuilder

def test_appraisal_traits():
    # Base candidate (neutral)
    c_neutral = (V2EntityBuilder(1)
        .kind("human")
        .location(0, 0)
        .identity(traits=set())
        .combat(hp=100, readiness=100.0)
        .build()
    )
    
    # Recruiter
    recruiter = V2EntityBuilder(10).kind("human").location(1, 1).combat(readiness=100.0).build()
    
    state = AuthoritativeState(tick=1, seed=1, entities={1: c_neutral, 10: recruiter})
    
    contract = ContractState(
        id="test_rec",
        kind=ContractKind.RECRUITMENT,
        source_id=10,
        target_id=1,
        terms={"daily_pay": 10}, # Fair pay for level 1
        status=ContractStatus.OFFERED
    )
    
    # 1. Neutral appraisal
    status, reason, _ = SocialAppraisalSystem.appraise_contract(c_neutral, contract, state)
    assert status == ContractStatus.ACCEPTED
    
    # 2. GREEDY trait (requires higher pay)
    c_greedy = replace(c_neutral, identity=replace(c_neutral.identity, traits={"GREEDY"}))
    status, reason, _ = SocialAppraisalSystem.appraise_contract(c_greedy, contract, state)
    assert status == ContractStatus.CANCELLED # 10 is enough for neutral but greedy wants more (utility < 1.0)
    
    contract_high = replace(contract, terms={"daily_pay": 20})
    status, reason, _ = SocialAppraisalSystem.appraise_contract(c_greedy, contract_high, state)
    assert status == ContractStatus.ACCEPTED

    # 3. LOYAL trait with high trust
    c_loyal = replace(c_neutral, identity=replace(c_neutral.identity, traits={"LOYAL"}),
                      social=replace(c_neutral.social, bonds={10: SocialBond(target_id=10, sentiment=0.5)})) # trust = 0.75
    contract_low = replace(contract, terms={"daily_pay": 5}) # Low pay
    status, reason, _ = SocialAppraisalSystem.appraise_contract(c_loyal, contract_low, state)
    assert status == ContractStatus.ACCEPTED # Accepted due to loyalty bonus

def test_social_fatigue():
    candidate = (V2EntityBuilder(1)
        .kind("human")
        .location(0, 0)
        .social(rejection_count={10: 3})
        .combat(readiness=100.0)
        .build()
    )
    recruiter = V2EntityBuilder(10).kind("human").location(1, 1).combat(readiness=100.0).build()
    state = AuthoritativeState(tick=1, seed=1, entities={1: candidate, 10: recruiter})
    
    contract = ContractState(
        id="test_rec",
        kind=ContractKind.RECRUITMENT,
        source_id=10,
        target_id=1,
        terms={"daily_pay": 10}, # Fair pay without fatigue
        status=ContractStatus.OFFERED
    )
    
    status, reason, _ = SocialAppraisalSystem.appraise_contract(candidate, contract, state)
    assert status == ContractStatus.CANCELLED

def test_group_directive_propagation():
    leader = (V2EntityBuilder(10).kind("human")
        .location(0, 0)
        .strategic(projects={"p1": ProjectState(id="p1", kind="EXPLORE", status=ProjectStatus.ACTIVE)},
                  current_project_id="p1")
        .combat(readiness=100.0)
        .build()
    )
    member = V2EntityBuilder(1).kind("human").location(1, 1).combat(readiness=100.0).build()
    group = GroupRecord(id=100, leader_id=10, member_ids={1, 10}, anchor=(0,0))
    state = AuthoritativeState(tick=1, seed=1, entities={1: member, 10: leader}, groups={100: group})
    
    update = GroupSystem.update_groups(state)
    
    # Member should have a new directive
    m_upd = update.entity_updates[1]
    directives = m_upd.strategic.directives_add_or_update
    assert any(d.kind == "GROUP_OBJECTIVE" and d.target == "EXPLORE" for d in directives)

def test_tactical_trust_obedience():
    # Leader and Member
    leader = (V2EntityBuilder(10).kind("human")
        .location(10, 10)
        .identity(faction="A")
        .task(work_kind="ENTITY_ACT", payload={"target_id": 99})
        .combat(readiness=100.0)
        .build()
    )
    # Member with TOTAL DISTRUST in leader
    member = (V2EntityBuilder(1)
        .kind("human")
        .location(1, 1)
        .identity(faction="A")
        .social(bonds={10: SocialBond(target_id=10, sentiment=-1.0)})
        .combat(readiness=100.0, tactical_role="VANGUARD")
        .build()
    )
    hostile = V2EntityBuilder(99).kind("monster").location(2, 2).identity(faction="B").combat(hp=100).combat(readiness=100.0).build()
    hostile_close = V2EntityBuilder(98).kind("monster").location(1.5, 1.5).identity(faction="B").combat(hp=100).combat(readiness=100.0).build()
    
    group = GroupRecord(id=100, leader_id=10, member_ids={1, 10}, shared_target_id=99, anchor=(5,5))
    state = AuthoritativeState(tick=1, seed=1, entities={1: member, 10: leader, 99: hostile, 98: hostile_close}, groups={100: group})
    
    # Tactical evaluation for member
    update = TacticalDecisionSystem.evaluate_entity_intent(state, member)
    # Should target 98 (distance 1.0) over 99 (distance 2.0) despite group target being 99
    assert update.task.payload_set["target_id"] == 98

def test_protector_guarding():
    leader = (V2EntityBuilder(10).kind("human")
        .location(10, 10)
        .task(work_kind="ENTITY_ACT", payload={"action": "INTERACT", "target_id": 50})
        .combat(readiness=100.0)
        .build()
    )
    protector = (V2EntityBuilder(1)
        .kind("human")
        .location(1, 1)
        .identity(group_id=100)
        .combat(readiness=100.0, tactical_role="PROTECTOR")
        .build()
    )
    group = GroupRecord(id=100, leader_id=10, member_ids={1, 10}, anchor=(10,10), roles={1: "PROTECTOR"})
    state = AuthoritativeState(tick=1, seed=1, entities={1: protector, 10: leader}, groups={100: group})
    
    # No hostiles
    update = TacticalDecisionSystem.evaluate_entity_intent(state, protector)
    
    # Protector should move to guard leader
    assert update.task.payload_set["reason"] == "CONTRACT_OBLIGATION_GUARD"
    assert update.task.payload_set["target_id"] == 10
