import pytest
from unittest.mock import MagicMock
from src_legacy.ai.strategy.recruitment_negotiation import RecruitmentNegotiationService
from src_legacy.ai.cognition_capacity import CognitionCapacityProfile
from src_legacy.core.models.strategy import ProjectRecord, ProjectKind
from src_legacy.platform.rng import DeterministicRNG

@pytest.fixture
def mock_ctx():
    ctx = MagicMock()
    ctx.snapshot.tick = 100
    ctx.rng = DeterministicRNG(seed=42)
    ctx.actor.id = 1
    ctx.actor.mind.decision.personality.greed = 0.5
    return ctx

@pytest.fixture
def mock_project():
    return ProjectRecord(
        project_id="p1",
        kind=ProjectKind.EXPLORATION,
        label="Test Project",
        priority=1.0,
        metadata={"risk": 0.1}
    )

def test_recruitment_offer_bounding_stable(mock_ctx, mock_project):
    """Stable entities produce consistent offers without noise."""
    stable_profile = CognitionCapacityProfile(
        planning_budget=5, judgment_stability=1.0, # High stability
        evidence_quality=0.8, social_bandwidth=5, detour_depth_limit=3,
        active_slice_limit=5, concern_intake_limit=3, lead_retention_limit=5,
        candidate_zone_limit=3, ally_evaluation_limit=5, blocker_resolution_patience=0.8,
        resume_reliability=0.8, interruption_resistance=1.0, abandonment_threshold_mod=1.0,
        contradiction_sensitivity=0.5, source_trust_learning_rate=0.5
    )
    
    # Base share for greed 0.5 is 0.5 - (0.5 * 0.4) = 0.3
    offer = RecruitmentNegotiationService.create_offer(
        mock_ctx, candidate_id=2, project=mock_project, profile=stable_profile
    )
    
    payout_term = next(t for t in offer.proposed_terms if t.term_type == "payout")
    assert payout_term.params["value"] == 0.3 # Exact base share

def test_recruitment_offer_bounding_unstable(mock_ctx, mock_project):
    """Unstable entities produce noisy/perturbed offers."""
    unstable_profile = CognitionCapacityProfile(
        planning_budget=5, judgment_stability=0.2, # Very low stability
        evidence_quality=0.8, social_bandwidth=5, detour_depth_limit=3,
        active_slice_limit=5, concern_intake_limit=3, lead_retention_limit=5,
        candidate_zone_limit=3, ally_evaluation_limit=5, blocker_resolution_patience=0.2,
        resume_reliability=0.2, interruption_resistance=0.0, abandonment_threshold_mod=0.2,
        contradiction_sensitivity=0.9, source_trust_learning_rate=0.9
    )
    
    # Change tick to ensure noise is non-zero for this seed
    mock_ctx.snapshot.tick = 101
    offer = RecruitmentNegotiationService.create_offer(
        mock_ctx, candidate_id=2, project=mock_project, profile=unstable_profile
    )
    
    payout_term = next(t for t in offer.proposed_terms if t.term_type == "payout")
    # Base share is 0.3, but noise should have added/removed something
    assert payout_term.params["value"] != 0.3
    assert 0.05 <= payout_term.params["value"] <= 0.6
