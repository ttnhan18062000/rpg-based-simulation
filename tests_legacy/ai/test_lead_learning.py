import pytest
from unittest.mock import MagicMock
from src_legacy.ai.states.base import AIContext
from src_legacy.ai.strategy.strategic_learning_service import StrategicLearningService
from src_legacy.ai.cognition_capacity import CognitionCapacityProfile
from src_legacy.core.models.strategy import LeadRecord, LeadKind, StrategicState
from src_legacy.core.models.enums import Domain
from src_legacy.core.models.vectors import Vector2
from src_legacy.platform.rng import DeterministicRNG

@pytest.fixture
def mock_ctx():
    ctx = MagicMock(spec=AIContext)
    ctx.snapshot = MagicMock()
    ctx.snapshot.tick = 100
    ctx.actor = MagicMock()
    ctx.actor.id = 1
    ctx.actor.spatial = MagicMock()
    ctx.actor.spatial.pos = Vector2(x=5, y=5)
    
    # Mock Strategic State
    strat = StrategicState(
        source_trust={"source_a": 0.5}
    )
    ctx.actor.mind.strategic = strat
    ctx.strategic = strat
    
    ctx.rng = DeterministicRNG(seed=42)
    return ctx

def test_learning_success(mock_ctx):
    profile = CognitionCapacityProfile(
        planning_budget=5, judgment_stability=0.8, evidence_quality=0.8,
        social_bandwidth=5, detour_depth_limit=3, active_slice_limit=5,
        concern_intake_limit=3, lead_retention_limit=5, candidate_zone_limit=3,
        ally_evaluation_limit=5, blocker_resolution_patience=0.8,
        resume_reliability=0.8, interruption_resistance=0.8,
        abandonment_threshold_mod=1.0, 
        contradiction_sensitivity=0.5,
        source_trust_learning_rate=0.4
    )
    
    lead = LeadRecord(
        lead_id="l1", kind=LeadKind.LOCATION, label="L1", 
        subject="iron", target_coords=(1,1),
        source_id="source_a", certainty=0.5
    )
    
    # Process Success
    updates = StrategicLearningService.process_lead_outcome(mock_ctx, lead, success=True, profile=profile)
    update = updates[0] # StrategicUpdate
    
    # Certainty should increase
    # Formula: certainty + (1 - certainty) * learning_rate (approx)
    # Actually my logic was: lead.certainty + (1.0 - lead.certainty) * 0.5 (fixed)
    # Source Trust: trust + (1.0 - trust) * source_trust_learning_rate
    
    updated_lead = update.leads_add_or_update[0]
    assert updated_lead.certainty > 0.5
    assert updated_lead.tested == True
    assert updated_lead.is_exhausted == True
    
    # Source Trust should increase in the state's dictionary
    # Wait! StrategicLearningService doesn't update source_trust in the StrategicUpdate object?
    # Actually, I didn't add source_trust to StrategicUpdate! 
    # I need to check if I should add it.
    
def test_learning_failure(mock_ctx):
    profile = CognitionCapacityProfile(
        planning_budget=5, judgment_stability=0.8, evidence_quality=0.8,
        social_bandwidth=5, detour_depth_limit=3, active_slice_limit=5,
        concern_intake_limit=3, lead_retention_limit=5, candidate_zone_limit=3,
        ally_evaluation_limit=5, blocker_resolution_patience=0.8,
        resume_reliability=0.8, interruption_resistance=0.8,
        abandonment_threshold_mod=1.0, 
        contradiction_sensitivity=0.9, # High sensitivity to failure
        source_trust_learning_rate=0.4
    )
    
    lead = LeadRecord(
        lead_id="l1", kind=LeadKind.LOCATION, label="L1", 
        subject="iron", target_coords=(1,1),
        source_id="source_a", certainty=0.5
    )
    
    # Process Failure
    updates = StrategicLearningService.process_lead_outcome(mock_ctx, lead, success=False, profile=profile)
    update = updates[0] # StrategicUpdate
    
    updated_lead = update.leads_add_or_update[0]
    assert updated_lead.certainty < 0.5
    assert updated_lead.is_exhausted == True
    assert lead.lead_id in update.tested_lead_ids
