
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, SocialComponent, SocialBond
from src.core.builder import V2EntityBuilder
from src.core.strategic import ContractState, ContractKind, ContractStatus, StrategicComponent
from src.social.appraisal import SocialAppraisalSystem
from src.social.contracts import ContractService

def create_mock_entity(id, gold=10, hp=100, sentiment=0.0):
    from src.core.builder import V2EntityBuilder
    from src.core.state import SocialBond
    return (V2EntityBuilder(id)
        .kind("ACTOR")
        .location(0, 0)
        .combat(hp=hp, max_hp=100)
        .inventory(gold=gold)
        .social(bonds={99: SocialBond(target_id=99, sentiment=sentiment, familiarity=0.5)})
        .combat(alive=True)
        .build())

def test_appraisal_betrayal_rejection():
    """Verify that a previous betrayal prevents contract acceptance regardless of payout."""
    # Scenario: Recruiter betrayed the candidate in the past
    from src.core.state import SocialBond
    candidate = (V2EntityBuilder(1)
        .kind("ACTOR")
        .location(0, 0)
        .inventory(gold=0)
        .social(betrayal_count=1, bonds={99: SocialBond(target_id=99, sentiment=-1.0)})
        .combat(alive=True)
        .build())
    
    # High-pay offer
    contract = ContractService.create_recruitment_contract("c_betrayal", 99, 1, daily_pay=100, tick=100)
    
    state = AuthoritativeState(entities={1: candidate}, tick=100, seed=42)
    
    status, reason, _ = SocialAppraisalSystem.appraise_contract(candidate, contract, state)
    assert status == ContractStatus.CANCELLED
    from src.core.enums import ReasonCode
    assert reason in (ReasonCode.TOTAL_DISTRUST, ReasonCode.BETRAYAL_HISTORY, "TOTAL_DISTRUST", "BETRAYAL_HISTORY")

def test_appraisal_risk_vs_hp():
    """Verify that low HP actors reject high-risk contracts."""
    low_hp_actor = create_mock_entity(1, hp=20)
    contract = ContractService.create_recruitment_contract("c_risk", 99, 1, risk_level="HIGH", daily_pay=50, tick=100)
    
    state = AuthoritativeState(entities={1: low_hp_actor}, tick=100, seed=42)
    
    status, reason, _ = SocialAppraisalSystem.appraise_contract(low_hp_actor, contract, state)
    assert status == ContractStatus.FAILED
    from src.core.enums import ReasonCode
    assert reason in (ReasonCode.LOW_HP_RETREAT, "TOO_DANGEROUS")

def test_offer_expiration_logic():
    """
    Verify that expired contract offers are marked EXPIRED.

    Important:
        This is a SocialContractSystem lifecycle test, not a pipeline test.

        AuthoritativeApplyPipeline.refine(StateUpdate()) does not currently
        perform a global sweep over every entity's contracts.

    Law:
        OFFERED / ACTIVE / COUNTERED contracts with expiry_tick <= current_tick
        must transition to EXPIRED.
    """
    from src.systems.social_contract import SocialContractSystem
    from src.core.strategic import ContractStatus

    entity = create_mock_entity(1)

    contract = ContractService.create_recruitment_contract(
        "c_expired",
        source_id=99,
        target_id=1,
        tick=100,
    )

    # create_recruitment_contract expires offers at tick + 10.
    assert contract.expiry_tick == 110
    assert contract.status == ContractStatus.OFFERED

    entity = replace(
        entity,
        strategic=replace(
            entity.strategic,
            contracts={
                contract.id: contract,
            },
        ),
    )

    strategic_update = SocialContractSystem.check_expirations(
        entity,
        current_tick=111,
    )

    assert strategic_update is not None
    assert any(
        c.id == "c_expired" and c.status == ContractStatus.EXPIRED
        for c in strategic_update.contracts_add_or_update
    )
    
def test_offer_not_expired_before_expiry_tick():
    """
    Verify that a contract offer is not expired before its expiry tick.
    """
    from src.systems.social_contract import SocialContractSystem

    entity = create_mock_entity(1)

    contract = ContractService.create_recruitment_contract(
        "c_active_offer",
        source_id=99,
        target_id=1,
        tick=100,
    )

    entity = replace(
        entity,
        strategic=replace(
            entity.strategic,
            contracts={
                contract.id: contract,
            },
        ),
    )

    strategic_update = SocialContractSystem.check_expirations(
        entity,
        current_tick=109,
    )

    assert strategic_update.contracts_add_or_update == []

def test_contract_driven_party_cohesion():
    """Verify that an ACTIVE contract prevents accidental party dissolution."""
    # This test will be implemented after Task 7.5 integration
    pass

def test_resolution_reputation_impact():
    """Verify that completing a contract boosts reputation."""
    contract = ContractService.create_recruitment_contract("c_rep", 99, 1, tick=100)
    contract = replace(contract, status=ContractStatus.ACTIVE)
    
    e1 = (V2EntityBuilder(1)
        .kind("ACTOR")
        .location(0, 0)
        .strategic(contracts={contract.id: contract})
        .combat(alive=True)
        .build())
    
    s_upd, b_upds = ContractService.resolve_contract_outcome(e1, "c_rep", success=True)
    
    # Check for reputation or turning point in s_upd
    # Phase 7 requirement: success improves trust/reputation
    assert any(upd.sentiment_delta > 0 for upd in b_upds[0].bond_updates)
