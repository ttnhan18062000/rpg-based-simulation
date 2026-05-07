import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState
from src.core.strategic import ContractState, ContractKind, ContractStatus
from src.social.appraisal import SocialAppraisalSystem
from src.core.enums import EntityRole

def create_mock_entity(eid: int, gold: int = 10, hp: int = 100):
    from src.core.builder import V2EntityBuilder
    from src.core.enums import Faction
    return (V2EntityBuilder(eid)
        .kind("hero")
        .location(0, 0)
        .identity(role=EntityRole.HERO)
        .identity(faction=Faction.HERO_GUILD)
        .combat(hp=hp, max_hp=100)
        .inventory(gold=gold)
        .combat(alive=True)
        .build())

def test_appraise_recruitment_low_trust_low_pay():
    entity = create_mock_entity(1)
    contract = ContractState(
        id="c1",
        kind=ContractKind.RECRUITMENT,
        source_id=2,
        target_id=1,
        terms={"daily_pay": 2} # Very low pay
    )
    state = AuthoritativeState(tick=100, seed=42)
    
    from src.core.enums import ReasonCode
    status, reason, counter = SocialAppraisalSystem.appraise_contract(entity, contract, state)
    assert status == ContractStatus.CANCELLED
    assert reason == ReasonCode.INSUFFICIENT_INCENTIVE

def test_appraise_recruitment_haggling():
    entity = create_mock_entity(1, gold=10) # Not desperate
    contract = ContractState(
        id="c1",
        kind=ContractKind.RECRUITMENT,
        source_id=2,
        target_id=1,
        terms={"daily_pay": 5} # Low but hagglable (utility 0.5, trust 0.5 -> score 0.4ish)
    )
    state = AuthoritativeState(tick=100, seed=42)
    
    from src.core.enums import ReasonCode
    status, reason, counter = SocialAppraisalSystem.appraise_contract(entity, contract, state)
    assert status == ContractStatus.COUNTERED
    assert reason == ReasonCode.HAGGLING_FOR_PAY
    assert counter["daily_pay"] == 10 # Should haggle for fair pay

def test_appraise_recruitment_high_trust():
    entity = create_mock_entity(1)
    from src.core.state import SocialBond
    new_social = replace(entity.social, bonds={2: SocialBond(target_id=2, sentiment=1.0)})
    entity = replace(entity, social=new_social)
    
    contract = ContractState(
        id="c1",
        kind=ContractKind.RECRUITMENT,
        source_id=2,
        target_id=1,
        terms={"daily_pay": 5} # Low pay but high trust
    )
    state = AuthoritativeState(tick=100, seed=42)
    
    from src.core.enums import ReasonCode
    status, reason, counter = SocialAppraisalSystem.appraise_contract(entity, contract, state)
    assert status == ContractStatus.ACCEPTED
    assert reason == ReasonCode.LOYALTY_ACCEPTANCE

def test_appraise_recruitment_danger_low_hp():
    entity = create_mock_entity(1, hp=40) # Low HP (40%)
    contract = ContractState(
        id="c1",
        kind=ContractKind.RECRUITMENT,
        source_id=2,
        target_id=1,
        terms={"daily_pay": 20, "risk_level": "HIGH"}
    )
    state = AuthoritativeState(tick=100, seed=42)
    
    from src.core.enums import ReasonCode
    status, reason, counter = SocialAppraisalSystem.appraise_contract(entity, contract, state)
    assert status == ContractStatus.FAILED
    assert reason == ReasonCode.LOW_HP_RETREAT
