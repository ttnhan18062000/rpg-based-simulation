import pytest
from unittest.mock import MagicMock
from src.ai.states.base import AIContext
from src.ai.strategy.strategic_learning_service import StrategicLearningService
from src.core.logic.strategic_knowledge_ingestion import StrategicKnowledgeIngestionService
from src.ai.cognition_capacity import CognitionCapacityProfile
from src.core.models.strategy import LeadRecord, LeadKind, StrategicState
from src.platform.rng import DeterministicRNG

@pytest.fixture
def mock_ctx():
    ctx = MagicMock(spec=AIContext)
    ctx.snapshot = MagicMock()
    ctx.snapshot.tick = 100
    ctx.actor = MagicMock()
    ctx.actor.id = 1
    
    from src.core.models.vectors import Vector2
    ctx.actor.spatial.pos = Vector2(x=10, y=10)
    
    # Initial Strategic State with neutral trust
    strat = StrategicState(
        source_trust={"guild": 0.5, "inn": 0.5}
    )
    ctx.actor.mind.strategic = strat
    ctx.strategic = strat
    
    ctx.rng = DeterministicRNG(seed=42)
    return ctx

def test_source_trust_learning_loop(mock_ctx):
    """Prove that future weighting is affected by source trust after a learning event."""
    profile = CognitionCapacityProfile(
        planning_budget=5, judgment_stability=0.8, evidence_quality=0.8,
        social_bandwidth=5, detour_depth_limit=3, active_slice_limit=5,
        concern_intake_limit=3, lead_retention_limit=5, candidate_zone_limit=3,
        ally_evaluation_limit=5, blocker_resolution_patience=0.8,
        resume_reliability=0.8, interruption_resistance=0.8,
        abandonment_threshold_mod=1.0, 
        contradiction_sensitivity=1.0, # MAX sensitivity
        source_trust_learning_rate=0.5
    )
    
    # 1. Ingest initial intel (Trust = 0.5)
    material_hints = {"iron": "Found near the caves"}
    initial_up = StrategicKnowledgeIngestionService.ingest_guild_intel(
        actor_id=mock_ctx.actor.id,
        tick=mock_ctx.snapshot.tick,
        material_hints=material_hints,
        camps_found=[],
        resources_found=[],
        source_trust=mock_ctx.strategic.source_trust
    )
    
    initial_lead = initial_up.leads_add_or_update[0]
    # source_confidence should be 0.8 (base) * (0.5 * 2.0) = 0.8
    assert initial_lead.source_confidence == pytest.approx(0.8)
    
    # 2. Process Failure (Refutation)
    # This should penalize "guild" trust
    updates = StrategicLearningService.process_lead_outcome(mock_ctx, initial_lead, success=False, profile=profile)
    strat_up = updates[0]
    
    new_trust = strat_up.source_trust_updates["guild"]
    assert new_trust < 0.5
    
    # 3. Apply Update Authoritatively (Milestone 3)
    from src.systems.gameplay.action_system import ActionSystem
    ActionSystem.apply_strategic_update(mock_ctx.actor, strat_up)
    
    # Verify persistence in state
    assert mock_ctx.strategic.source_trust["guild"] == new_trust
    
    # 4. Ingest NEW intel from the same source (Trust < 0.5)
    new_hints = {"gold": "Buried in the sand"}
    secondary_up = StrategicKnowledgeIngestionService.ingest_guild_intel(
        actor_id=mock_ctx.actor.id,
        tick=mock_ctx.snapshot.tick + 1,
        material_hints=new_hints,
        camps_found=[],
        resources_found=[],
        source_trust=mock_ctx.strategic.source_trust
    )
    
    secondary_lead = secondary_up.leads_add_or_update[0]
    # source_confidence should now be capped or discounted
    # Formula: 0.8 * (new_trust * 2.0)
    assert secondary_lead.source_confidence < 0.8
    assert secondary_lead.source_confidence == pytest.approx(0.8 * (new_trust * 2.0))
    
    print(f"Initial Confidence: {initial_lead.source_confidence}")
    print(f"New Trust: {new_trust}")
    print(f"Secondary Confidence: {secondary_lead.source_confidence}")
