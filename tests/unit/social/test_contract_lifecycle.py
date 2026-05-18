"""
Contract lifecycle and social evaluation tests.
- RPG-0054: social_contracts_explicit
- RPG-0055: social_contract_consequences
- RPG-0059: social_recruitment_evaluation
"""

import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, SocialComponent, SocialBond
from src.core.builder import V2EntityBuilder
from src.core.strategic import ContractState, ContractKind, ContractStatus
from src.systems.social_systems.appraisal import SocialAppraisalSystem
from src.systems.social_systems.contracts import ContractService

def create_mock_entity(id, gold=10, sentiment=0.0):
    from src.core.builder import V2EntityBuilder
    from src.core.state import SocialBond
    return (V2EntityBuilder(id)
        .kind("ACTOR")
        .location(0, 0)
        .inventory(gold=gold)
        .social(bonds={99: SocialBond(target_id=99, sentiment=sentiment, familiarity=0.5)})
        .combat(alive=True)
        .build())

def test_contract_appraisal_trust():
    # Scenario: Trusted friend offers a low-pay recruitment
    friend = create_mock_entity(1, sentiment=0.9)
    contract = ContractService.create_recruitment_contract("c1", 99, 1, daily_pay=6, tick=100) # Pay 6 to ensure acceptance with trust
    
    state = AuthoritativeState(entities={1: friend}, tick=100, seed=1)
    
    from src.core.enums import ReasonCode
    status, reason, _ = SocialAppraisalSystem.appraise_contract(friend, contract, state)
    assert status == ContractStatus.ACCEPTED
    assert reason == ReasonCode.LOYALTY_ACCEPTANCE

def test_contract_appraisal_greed():
    # Scenario: Desperate for gold, accepts high pay recruitment from stranger
    desperate = create_mock_entity(1, gold=0, sentiment=0.0)
    contract = ContractService.create_recruitment_contract("c2", 99, 1, daily_pay=20, tick=100)
    
    state = AuthoritativeState(entities={1: desperate}, tick=100, seed=1)
    
    from src.core.enums import ReasonCode
    status, reason, _ = SocialAppraisalSystem.appraise_contract(desperate, contract, state)
    assert status == ContractStatus.ACCEPTED
    assert reason == ReasonCode.FAIR_COMPENSATION

def test_contract_appraisal_rejection():
    # Scenario: Low trust stranger offers low pay
    enemy = create_mock_entity(1, sentiment=-0.9)
    contract = ContractService.create_recruitment_contract("c3", 99, 1, daily_pay=5, tick=100)
    
    state = AuthoritativeState(entities={1: enemy}, tick=100, seed=1)
    
    from src.core.enums import ReasonCode
    status, reason, _ = SocialAppraisalSystem.appraise_contract(enemy, contract, state)
    assert status == ContractStatus.CANCELLED
    assert reason == ReasonCode.TOTAL_DISTRUST

def test_contract_lifecycle_acceptance():
    contract = ContractService.create_recruitment_contract("c4", 99, 1, tick=100)
    
    # Accept
    entity = create_mock_entity(1)
    # The entity must have the contract in its strategic component to accept it
    entity = (V2EntityBuilder(1)
        .kind("ACTOR")
        .location(0, 0)
        .strategic(contracts={contract.id: contract})
        .build())
    
    update = ContractService.accept_contract(entity, contract.id, tick=100)
    assert len(update.contracts_add_or_update) == 1
    new_contract = update.contracts_add_or_update[0]
    assert new_contract.status == ContractStatus.ACTIVE
    assert new_contract.expiry_tick == 200 # 100 + 100 duration

def test_contract_lifecycle_resolution():
    contract = ContractService.create_recruitment_contract("c5", 99, 1, tick=100)
    contract = replace(contract, status=ContractStatus.ACTIVE)
    
    # Create entity that owns the contract
    entity = V2EntityBuilder(1).kind("ACTOR").location(0, 0).strategic(contracts={contract.id: contract}).build()
    
    # Success
    s_upd, b_upds = ContractService.resolve_contract_outcome(entity, contract.id, success=True)
    assert s_upd.contracts_add_or_update[0].status == ContractStatus.FULFILLED
    assert b_upds[0].bond_updates[0].sentiment_delta == 0.2
    
    # Betrayal
    s_upd, b_upds = ContractService.resolve_contract_outcome(entity, contract.id, success=False, betrayal=True, betrayer_id=99)
    assert s_upd.contracts_add_or_update[0].status == ContractStatus.BETRAYED
    assert b_upds[0].bond_updates[0].sentiment_delta == -1.0
