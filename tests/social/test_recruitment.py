import pytest
from src.core.builder import V2EntityBuilder
from src.social.appraisal import SocialAppraisalSystem

def test_recruitment_cost_scaling_with_level():
    """Verify that recruitment cost increases with candidate level."""
    recruiter = V2EntityBuilder(1).kind("HERO").position(0.0, 0.0).build()
    
    # Candidate Level 1
    cand1 = (V2EntityBuilder(2)
        .kind("HERO")
        .position(1.0, 0.0)
        .with_identity(evolution_level=1)
        .build())
    cost1 = SocialAppraisalSystem.calculate_recruitment_cost(recruiter, cand1)
    
    # Candidate Level 5
    cand5 = (V2EntityBuilder(3)
        .kind("HERO")
        .position(2.0, 0.0)
        .with_identity(evolution_level=5)
        .build())
    cost5 = SocialAppraisalSystem.calculate_recruitment_cost(recruiter, cand5)
    
    assert cost5 > cost1
    assert cost1 == 100 # base(100) * level(1) * trust_mult(1.0)
    assert cost5 == 500 # base(100) * level(5) * trust_mult(1.0)

def test_recruitment_cost_discount_with_trust():
    """Verify that high trust reduces recruitment cost."""
    recruiter = V2EntityBuilder(1).kind("HERO").position(0.0, 0.0).build()
    
    # Low trust (0.0) -> mult 1.5
    cand_low = (V2EntityBuilder(2)
        .kind("HERO")
        .position(1.0, 0.0)
        .trust(1, 0.0)
        .build())
    cost_low = SocialAppraisalSystem.calculate_recruitment_cost(recruiter, cand_low)
    
    # High trust (1.0) -> mult 0.5
    cand_high = (V2EntityBuilder(3)
        .kind("HERO")
        .position(2.0, 0.0)
        .trust(1, 1.0)
        .build())
    cost_high = SocialAppraisalSystem.calculate_recruitment_cost(recruiter, cand_high)
    
    assert cost_low == 150
    assert cost_high == 50

def test_recruitment_acceptance_logic():
    """Verify that recruitment acceptance considers payout and trust."""
    from src.core.strategic import ContractState, ContractKind, ContractStatus
    from src.core.state import AuthoritativeState
    
    candidate = (V2EntityBuilder(1)
        .kind("HERO")
        .position(0.0, 0.0)
        .trust(2, 0.8)
        .build())
    
    state = AuthoritativeState(tick=0, seed=42)
    
    # High payout, high trust -> Accept
    contract = ContractState(
        id="c1", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
        terms={"daily_pay": 15, "risk_level": "LOW"}, # daily_pay 15 > 10 base
        status=ContractStatus.OFFERED, created_tick=0
    )
    status, reason, _ = SocialAppraisalSystem.appraise_contract(candidate, contract, state)
    assert status == ContractStatus.ACCEPTED
    
    # Low payout, low trust -> Reject
    candidate_low = (V2EntityBuilder(1)
        .kind("HERO")
        .position(0.0, 0.0)
        .trust(2, 0.2)
        .build())
    contract_low = ContractState(
        id="c2", kind=ContractKind.RECRUITMENT, source_id=2, target_id=1,
        terms={"daily_pay": 2, "risk_level": "HIGH"},
        status=ContractStatus.OFFERED, created_tick=0
    )
    status, reason, _ = SocialAppraisalSystem.appraise_contract(candidate_low, contract_low, state)
    assert status == ContractStatus.CANCELLED
