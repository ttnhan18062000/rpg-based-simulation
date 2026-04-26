import pytest
from src.core.state import EntityState, SocialComponent, IdentityComponent
from src.systems.social import SocialAppraisalSystem

def test_recruitment_cost_scaling_with_level():
    """Verify that recruitment cost increases with candidate level."""
    recruiter = EntityState(id=1, kind="HERO", position=(0.0, 0.0))
    
    # Candidate Level 1
    cand1 = EntityState(id=2, kind="HERO", position=(1.0, 0.0),
                        identity=IdentityComponent(evolution_level=1))
    cost1 = SocialAppraisalSystem.calculate_recruitment_cost(recruiter, cand1)
    
    # Candidate Level 5
    cand5 = EntityState(id=3, kind="HERO", position=(2.0, 0.0),
                        identity=IdentityComponent(evolution_level=5))
    cost5 = SocialAppraisalSystem.calculate_recruitment_cost(recruiter, cand5)
    
    assert cost5 > cost1
    assert cost1 == 100 # base(100) * level(1) * trust_mult(1.0)
    assert cost5 == 500 # base(100) * level(5) * trust_mult(1.0)

def test_recruitment_cost_discount_with_trust():
    """Verify that high trust reduces recruitment cost."""
    recruiter = EntityState(id=1, kind="HERO", position=(0.0, 0.0))
    
    # Low trust (0.0) -> mult 1.5
    cand_low = EntityState(id=2, kind="HERO", position=(1.0, 0.0),
                           social=SocialComponent(trust_history={1: 0.0}))
    cost_low = SocialAppraisalSystem.calculate_recruitment_cost(recruiter, cand_low)
    
    # High trust (1.0) -> mult 0.5
    cand_high = EntityState(id=3, kind="HERO", position=(2.0, 0.0),
                            social=SocialComponent(trust_history={1: 1.0}))
    cost_high = SocialAppraisalSystem.calculate_recruitment_cost(recruiter, cand_high)
    
    assert cost_low == 150
    assert cost_high == 50

def test_recruitment_acceptance_logic():
    """Verify that recruitment acceptance considers payout and trust."""
    candidate = EntityState(id=1, kind="HERO", position=(0.0, 0.0),
                            social=SocialComponent(trust_history={2: 0.8}))
    
    # High payout, high trust -> Accept
    accepted = SocialAppraisalSystem.evaluate_recruitment_offer(
        candidate, recruiter_id=2, payout=150, risk=0.2
    )
    assert accepted is True
    
    # Low payout, low trust -> Reject
    candidate_low = EntityState(id=1, kind="HERO", position=(0.0, 0.0),
                                social=SocialComponent(trust_history={2: 0.2}))
    rejected = SocialAppraisalSystem.evaluate_recruitment_offer(
        candidate_low, recruiter_id=2, payout=20, risk=0.5
    )
    assert rejected is False
