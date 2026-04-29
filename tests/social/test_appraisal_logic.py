import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState
from src.core.strategic import ContractState, ContractKind, ContractStatus
from src.social.appraisal import SocialAppraisalSystem
from src.core.enums import EntityRole

def create_mock_entity(eid: int, gold: int = 10, hp: int = 100):
    from src.core.state import EntityState, CombatComponent, InventoryComponent, SocialComponent, IdentityComponent, BiologicalComponent, LifecycleComponent, StrategicComponent
    return EntityState(
        id=eid,
        kind="hero",
        active=True,
        position=(0, 0),
        identity=IdentityComponent(role=EntityRole.HERO, faction="player"),
        combat=CombatComponent(hp=hp, max_hp=100, atk=10, def_stat=5, alive=True),
        inventory=InventoryComponent(gold=gold),
        social=SocialComponent(),
        biological=BiologicalComponent(),
        lifecycle=LifecycleComponent(),
        strategic=StrategicComponent()
    )

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
    
    status, reason, counter = SocialAppraisalSystem.appraise_contract(entity, contract, state)
    assert status == ContractStatus.CANCELLED
    assert reason == "INSUFFICIENT_INCENTIVE"

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
    
    status, reason, counter = SocialAppraisalSystem.appraise_contract(entity, contract, state)
    assert status == ContractStatus.COUNTERED
    assert reason == "HAGGLING_FOR_PAY"
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
    
    status, reason, counter = SocialAppraisalSystem.appraise_contract(entity, contract, state)
    assert status == ContractStatus.ACCEPTED
    assert reason == "LOYALTY_ACCEPTANCE"

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
    
    status, reason, counter = SocialAppraisalSystem.appraise_contract(entity, contract, state)
    assert status == ContractStatus.FAILED
    assert reason == "TOO_DANGEROUS"
