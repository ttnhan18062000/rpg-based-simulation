import pytest
from unittest.mock import MagicMock
from src_legacy.ai.states.base import AIContext
from src_legacy.ai.strategy.uncertainty_resolution import StrategicUncertaintyService
from src_legacy.core.logic.strategic_knowledge_ingestion import StrategicKnowledgeIngestionService
from src_legacy.ai.cognition_capacity import CognitionCapacityProfile
from src_legacy.core.models.strategy import (
    LeadRecord, LeadKind, StrategicState, CandidateZoneRecord, 
    ObjectiveRecord, ObjectiveKind, StrategicStatus, ProjectRecord
)
from src_legacy.core.models.vectors import Vector2
from src_legacy.platform.rng import DeterministicRNG

@pytest.fixture
def mock_ctx():
    ctx = MagicMock(spec=AIContext)
    ctx.snapshot = MagicMock()
    ctx.snapshot.tick = 200
    ctx.snapshot.resource_nodes = []
    ctx.snapshot.camps = []
    
    ctx.actor = MagicMock()
    ctx.actor.id = 1
    ctx.actor.spatial.pos = Vector2(x=10, y=10)
    
    # Initial Strategic State
    strat = StrategicState()
    ctx.actor.mind.strategic = strat
    ctx.strategic = strat
    
    # Setup some 'truth' in the world
    # A resource node at (55, 55)
    node = MagicMock()
    node.item_group = "iron_node_42"
    node.spatial.pos = Vector2(x=55, y=55)
    ctx.snapshot.resource_nodes = [node]
    
    ctx.rng = DeterministicRNG(seed=42)
    return ctx

def test_uncertainty_resolution_loop(mock_ctx):
    """Prove that proximity to a rumored zone resolves imprecise leads into precise targets."""
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
    
    # 1. Start with a Rumor (Trust = 0.5)
    rumor_text = "Iron reported at iron_node_42"
    ingest_up = StrategicKnowledgeIngestionService.ingest_inn_rumor(
        actor_id=mock_ctx.actor.id,
        tick=mock_ctx.snapshot.tick,
        rumor_text=rumor_text,
        danger_level=0.1,
        rng=mock_ctx.rng,
        source_trust={"inn": 0.5},
        subject="iron_node_42"
    )
    
    lead = ingest_up.leads_add_or_update[0]
    zone = ingest_up.candidate_zones_add_or_update[0]
    
    # Assert it has NO coords yet (Anti-Cheating)
    assert lead.target_coords is None
    assert lead.subject == "iron_node_42" # Mock text parsing not full, but simplified here
    assert zone.approx_coords is not None
    
    # 2. Setup an INVESTIGATE objective targeting this rumor
    obj = ObjectiveRecord(
        objective_id="obj_investigate_iron",
        project_id="prj_1",
        kind=ObjectiveKind.INVESTIGATE,
        label="Investigate Rumor",
        target_pos=zone.approx_coords, # Using approx coords for scouting
        evidence_refs=[lead.lead_id],
        status=StrategicStatus.ACTIVE
    )
    
    # Inject into state
    mock_ctx.strategic.leads = [lead]
    mock_ctx.strategic.candidate_zones = [zone]
    mock_ctx.current_objective = obj
    
    # 3. Resolve while FAR (10,10) vs Truth (55,55). approx_coords (66,35)
    up = StrategicUncertaintyService.resolve_uncertainty(mock_ctx, profile)
    assert not up.leads_add_or_update
    
    # 4. Move Near the TRUTH (55, 55). say (53, 53)
    mock_ctx.actor.spatial.pos = Vector2(x=53, y=53)
    
    # 5. Resolve while NEAR
    up_near = StrategicUncertaintyService.resolve_uncertainty(mock_ctx, profile)
    
    # Should be resolved!
    assert len(up_near.leads_add_or_update) == 1
    resolved_lead = up_near.leads_add_or_update[0]
    assert resolved_lead.target_coords == Vector2(x=55, y=55)
    assert resolved_lead.certainty == 1.0
    assert "resolved_evidence" in resolved_lead.semantic_tags
    
    # Objective should be updated to real coords
    assert up_near.current_objective_id == "obj_investigate_iron"
    
    print(f"Truth: (55,55)")
    print(f"Actor Pos: (53,53)")
    print(f"Resolved Lead Target: {resolved_lead.target_coords}")
