import pytest
from src.core.models.strategy import LeadRecord, LeadKind, CognitionCapacityProfile
from src.ai.strategy.uncertainty_resolution import StrategicUncertaintyService
from unittest.mock import MagicMock

def create_test_profile(**kwargs):
    base = {
        "planning_budget": 5, "judgment_stability": 0.5,
        "evidence_quality": 0.5, "social_bandwidth": 5, "detour_depth_limit": 3,
        "active_slice_limit": 5, "concern_intake_limit": 3, "lead_retention_limit": 5,
        "candidate_zone_limit": 3, "ally_evaluation_limit": 5, "blocker_resolution_patience": 0.5,
        "resume_reliability": 0.5, "interruption_resistance": 0.5, "abandonment_threshold_mod": 1.0,
        "contradiction_sensitivity": 1.0, "source_trust_learning_rate": 0.5
    }
    base.update(kwargs)
    return CognitionCapacityProfile(**base)

def test_contradiction_degrades_certainty():
    """Verify that leads with contradictions lose certainty based on profile sensitivity. [MILESTONE 5]"""
    # 1. Setup
    ctx = MagicMock()
    # Pydantic models need real data or dicts for mock_copy etc
    lead = LeadRecord(
        lead_id="L1", kind=LeadKind.LOCATION, label="Hidden Cave",
        certainty=0.8, contradiction_count=2
    )
    ctx.actor.mind.strategic.leads = [lead]
    ctx.current_objective = None
    
    profile = create_test_profile(contradiction_sensitivity=1.0)
    
    # 2. Execute
    # We'll need to call a new method 'handle_contradictions' which we're about to implement.
    # For now, resolve_uncertainty might include it or we call it separately.
    # The plan says "Implement contradiction-driven uncertainty degradation".
    up = StrategicUncertaintyService.handle_contradictions(ctx, profile)
    
    # 3. Verify
    assert len(up.leads_add_or_update) == 1
    updated = up.leads_add_or_update[0]
    assert updated.certainty < 0.8
    # Formula check: 0.8 - (2 * 0.1 * 1.0) = 0.6
    assert updated.certainty == 0.6

def test_hypothesis_impacted_by_contradiction():
    """Verify that hypotheses lose confidence when supporting leads are contradicted. [MILESTONE 5]"""
    from src.core.models.strategy import HypothesisRecord
    ctx = MagicMock()
    
    lead = LeadRecord(lead_id="L1", kind=LeadKind.LOCATION, label="L1", certainty=0.5, contradiction_count=1)
    hypo = HypothesisRecord(hypothesis_id="H1", label="Cave exists", confidence=0.8, supporting_lead_ids=["L1"])
    
    ctx.actor.mind.strategic.leads = [lead]
    ctx.actor.mind.strategic.hypotheses = [hypo]
    
    profile = create_test_profile(contradiction_sensitivity=1.0)
    
    up = StrategicUncertaintyService.handle_contradictions(ctx, profile)
    
    assert len(up.hypotheses_add_or_update) == 1
    updated_hypo = up.hypotheses_add_or_update[0]
    assert updated_hypo.confidence < 0.8
