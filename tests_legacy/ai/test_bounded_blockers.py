import pytest
from unittest.mock import MagicMock
from src_legacy.ai.states.base import AIContext
from src_legacy.ai.strategy.blocker_inference import BlockerInferenceService
from src_legacy.ai.cognition_capacity import CognitionCapacityProfile, CognitionCapacityBuilder
from src_legacy.core.models.strategy import ObjectiveRecord, ObjectiveKind, BlockerKind
from src_legacy.platform.rng import DeterministicRNG

@pytest.fixture
def mock_ctx():
    ctx = MagicMock(spec=AIContext)
    ctx.snapshot = MagicMock()
    ctx.snapshot.tick = 100
    ctx.actor = MagicMock()
    ctx.actor.id = 1
    ctx.actor.combat.hp = 100
    ctx.actor.combat.max_hp = 100
    ctx.actor.progression.gold = 50
    ctx.rng = DeterministicRNG(seed=42)
    return ctx

def test_accurate_diagnosis_high_wisdom(mock_ctx):
    # High wisdom -> high judgment_stability (e.g. 0.8)
    profile = CognitionCapacityProfile(
        planning_budget=5,
        judgment_stability=0.9, # Very high
        evidence_quality=0.8,
        social_bandwidth=5,
        detour_depth_limit=3,
        active_slice_limit=5,
        concern_intake_limit=3,
        lead_retention_limit=5,
        candidate_zone_limit=3,
        ally_evaluation_limit=5,
        blocker_resolution_patience=0.8,
        resume_reliability=0.8,
        interruption_resistance=0.8,
        abandonment_threshold_mod=1.0,
        contradiction_sensitivity=0.5,
        source_trust_learning_rate=0.5
    )
    
    obj = ObjectiveRecord(
        objective_id="obj_test", project_id="prj_test",
        kind=ObjectiveKind.VISIT, label="Visit Town",
        target_pos=None # Missing target pos -> Knowledge blocker
    )
    
    blockers = BlockerInferenceService.infer_blockers(mock_ctx, obj, profile)
    
    assert len(blockers) == 1
    assert blockers[0].kind == BlockerKind.KNOWLEDGE
    assert "Location unknown" in blockers[0].label

def test_misdiagnosis_low_wisdom(mock_ctx):
    # Low stability -> 0.1
    profile = CognitionCapacityProfile(
        planning_budget=3,
        judgment_stability=0.0, # Forces misdiagnosis
        evidence_quality=0.1,
        social_bandwidth=2,
        detour_depth_limit=1,
        active_slice_limit=3,
        concern_intake_limit=2,
        lead_retention_limit=2,
        candidate_zone_limit=1,
        ally_evaluation_limit=2,
        blocker_resolution_patience=0.1,
        resume_reliability=0.1,
        interruption_resistance=0.1,
        abandonment_threshold_mod=0.8,
        contradiction_sensitivity=0.1,
        source_trust_learning_rate=0.1
    )
    
    obj = ObjectiveRecord(
        objective_id="obj_test", project_id="prj_test",
        kind=ObjectiveKind.VISIT, label="Visit Town",
        target_pos=None # Should be Knowledge
    )
    
    blockers = BlockerInferenceService.infer_blockers(mock_ctx, obj, profile)
    
    assert len(blockers) == 1
    # Misdiagnosis logic shifts kind randomly. 
    # With seed 42, let's see what it picks.
    assert blockers[0].kind != BlockerKind.KNOWLEDGE or "Misfocused" in blockers[0].label
    assert "Misfocused" in blockers[0].label
