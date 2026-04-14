import pytest
from unittest.mock import MagicMock
from src.ai.states.base import AIContext
from src.ai.strategy.strategic_evaluator import StrategicDecision
from src.ai.strategy.detour_suggestion import DetourSuggestionService
from src.ai.strategy.objective_derivation import ObjectiveDerivationService
from src.ai.strategy.blocker_inference import BlockerInferenceService
from src.ai.cognition_capacity import CognitionCapacityProfile
from src.core.models.strategy import (
    ProjectRecord, ObjectiveRecord, BlockerRecord, 
    BlockerKind, ObjectiveKind, StrategicStatus, ProjectKind, LeadRecord, LeadKind
)
from src.platform.rng import DeterministicRNG

@pytest.fixture
def mock_ctx():
    ctx = MagicMock(spec=AIContext)
    ctx.snapshot = MagicMock()
    ctx.snapshot.tick = 100
    ctx.actor = MagicMock()
    ctx.actor.id = 1
    ctx.actor.combat.hp = 100
    ctx.actor.combat.max_hp = 100
    ctx.actor.progression.gold = 100
    
    # Mock Strategic State
    strat = MagicMock()
    strat.projects = []
    strat.concerns = []
    strat.leads = []
    strat.tested_lead_ids = []
    ctx.actor.mind.strategic = strat
    ctx.strategic = strat
    
    # Mock AIContext properties
    from unittest.mock import PropertyMock
    type(ctx).active_leads = PropertyMock(return_value=[])
    
    ctx.rng = DeterministicRNG(seed=42)
    return ctx

def test_detour_breadth_limit(mock_ctx):
    profile = CognitionCapacityProfile(
        planning_budget=5, judgment_stability=0.8, evidence_quality=0.8,
        social_bandwidth=5, detour_depth_limit=3,
        active_slice_limit=1, # BREADTH LIMIT = 1
        concern_intake_limit=3, lead_retention_limit=5, candidate_zone_limit=3,
        ally_evaluation_limit=5, blocker_resolution_patience=0.8,
        resume_reliability=0.8, interruption_resistance=0.8,
        abandonment_threshold_mod=1.0, contradiction_sensitivity=0.5,
        source_trust_learning_rate=0.5
    )
    
    # Create multiple leads for the same subject
    lead1 = LeadRecord(lead_id="l1", kind=LeadKind.LOCATION, label="L1", subject="iron", target_coords=(1,1))
    lead2 = LeadRecord(lead_id="l2", kind=LeadKind.LOCATION, label="L2", subject="iron", target_coords=(2,2))
    
    from unittest.mock import PropertyMock
    type(mock_ctx).active_leads = PropertyMock(return_value=[lead1, lead2])
    
    blocker = BlockerRecord(
        blocker_id="b1", kind=BlockerKind.KNOWLEDGE, label="Need Iron", 
        subject_ref="iron"
    )
    
    detours = DetourSuggestionService.suggest_detours(mock_ctx, blocker, "prj_1", profile)
    
    # Should be limited to 1 detour
    assert len(detours) == 1
    assert detours[0].target_pos == (1,1)

def test_detour_depth_limit_fallback(mock_ctx):
    profile = CognitionCapacityProfile(
        planning_budget=5, judgment_stability=0.8, evidence_quality=0.8,
        social_bandwidth=5, 
        detour_depth_limit=1, # DEPTH LIMIT = 1
        active_slice_limit=5, 
        concern_intake_limit=3, lead_retention_limit=5, candidate_zone_limit=3,
        ally_evaluation_limit=5, blocker_resolution_patience=0.8,
        resume_reliability=0.8, interruption_resistance=0.8,
        abandonment_threshold_mod=1.0, contradiction_sensitivity=0.5,
        source_trust_learning_rate=0.5
    )
    
    # Project with an objective at depth 1
    obj1 = ObjectiveRecord(
        objective_id="obj1", project_id="prj1", 
        kind=ObjectiveKind.VISIT, label="Step 1",
        detour_depth=1
    )
    prj = ProjectRecord(
        project_id="prj1", kind=ProjectKind.EXPLORATION, label="Prj 1",
        objectives=[obj1], active_objective_id="obj1"
    )
    mock_ctx.strategic.projects = [prj]
    mock_ctx.strategic.current_project_id = "prj1"
    
    # Blocker for obj1
    blocker = BlockerRecord(
        blocker_id="b1", kind=BlockerKind.KNOWLEDGE, label="Need Info", 
        subject_ref="info", spawned_from_id="obj1"
    )
    obj1.blockers = [blocker]
    
    # Attempt derivation
    decision = StrategicDecision(selected_id="prj1", selected_kind="project", reason="Test")
    obj_service = ObjectiveDerivationService(BlockerInferenceService(), DetourSuggestionService())
    
    obj_service.apply_derivation(mock_ctx, prj, decision, profile)
    
    # Decision should contain a project update marking it as SUSPENDED
    updated_prj = next((p for p in decision.updates.projects_add_or_update if p.project_id == "prj1"), None)
    assert updated_prj is not None
    assert updated_prj.status == StrategicStatus.SUSPENDED
    assert "Complexity Depth Exceeded" in updated_prj.suspension_reason

def test_retry_suppression(mock_ctx):
    profile = CognitionCapacityProfile(
        planning_budget=5, judgment_stability=0.8, evidence_quality=0.8,
        social_bandwidth=5, detour_depth_limit=3, active_slice_limit=5,
        concern_intake_limit=3, lead_retention_limit=5, candidate_zone_limit=3,
        ally_evaluation_limit=5, blocker_resolution_patience=0.8,
        resume_reliability=0.8, interruption_resistance=0.8,
        abandonment_threshold_mod=1.0, contradiction_sensitivity=0.5,
        source_trust_learning_rate=0.5
    )
    
    # Lead that was already tested
    lead1 = LeadRecord(lead_id="l1", kind=LeadKind.LOCATION, label="L1", subject="iron", target_coords=(1,1), tested=True)
    from unittest.mock import PropertyMock
    type(mock_ctx).active_leads = PropertyMock(return_value=[lead1])
    mock_ctx.strategic.tested_lead_ids = ["l1"]
    
    blocker = BlockerRecord(
        blocker_id="b1", kind=BlockerKind.KNOWLEDGE, label="Need Iron", 
        subject_ref="iron"
    )
    
    detours = DetourSuggestionService.suggest_detours(mock_ctx, blocker, "prj_1", profile)
    
    # Should find 1 detour (general fallack) but with NO target_pos because lead1 is suppressed
    assert len(detours) == 1
    assert detours[0].target_pos is None
