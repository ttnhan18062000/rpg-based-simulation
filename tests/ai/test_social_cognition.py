import pytest
from unittest.mock import MagicMock
from src.ai.states.base import AIContext
from src.ai.strategy.blocker_inference import BlockerInferenceService
from src.ai.strategy.social_candidate_selection import SocialCandidateSelectionService
from src.ai.cognition_capacity import CognitionCapacityProfile
from src.core.models.strategy import ObjectiveRecord, ObjectiveKind, BlockerKind
from src.core.models.enums import EnemyTier
from src.platform.rng import DeterministicRNG

@pytest.fixture
def mock_ctx():
    ctx = MagicMock(spec=AIContext)
    ctx.snapshot = MagicMock()
    ctx.snapshot.tick = 100
    ctx.snapshot.entities = {}
    
    ctx.actor = MagicMock()
    ctx.actor.id = 1
    ctx.actor.identity.faction = 1
    ctx.actor.identity.group_id = None # Solo
    ctx.actor.progression.level = 5
    ctx.actor.combat.hp = 100
    ctx.actor.combat.max_hp = 100
    ctx.actor.mind.social.known_bonds = {} # Real dict
    
    ctx.actor.spatial.pos = MagicMock()
    ctx.actor.spatial.pos.manhattan.return_value = 0
    
    ctx.rng = DeterministicRNG(seed=42)
    return ctx

def test_social_blocker_detection_solo(mock_ctx):
    # Setup Elite Target
    target = MagicMock()
    target.id = 99
    target.identity.tier = EnemyTier.ELITE
    target.identity.name = "Elite Boss"
    target.progression.level = 10
    target.combat.max_hp = 500
    mock_ctx.snapshot.entities[99] = target
    
    profile = CognitionCapacityProfile(
        planning_budget=5, judgment_stability=1.0, # Perfect judgment
        evidence_quality=0.8, social_bandwidth=5, detour_depth_limit=3,
        active_slice_limit=5, concern_intake_limit=3, lead_retention_limit=5,
        candidate_zone_limit=3, ally_evaluation_limit=5, blocker_resolution_patience=0.8,
        resume_reliability=0.8, interruption_resistance=0.8, abandonment_threshold_mod=1.0,
        contradiction_sensitivity=0.5, source_trust_learning_rate=0.5
    )
    
    obj = ObjectiveRecord(
        objective_id="obj_kill", project_id="prj_test",
        kind=ObjectiveKind.KILL, label="Kill Boss",
        target_id=99
    )
    
    blockers = BlockerInferenceService.infer_blockers(mock_ctx, obj, profile)
    
    # Assert SOCIAL blocker detected
    assert any(b.kind == BlockerKind.SOCIAL for b in blockers)
    social_blocker = next(b for b in blockers if b.kind == BlockerKind.SOCIAL)
    assert "Cannot solo" in social_blocker.label
    assert ObjectiveKind.INTERACT in social_blocker.suggested_detour_types

def test_social_misjudgment_low_stability(mock_ctx):
    # Setup Elite Target
    target = MagicMock()
    target.id = 99
    target.identity.tier = EnemyTier.ELITE
    mock_ctx.snapshot.entities[99] = target
    
    # Low stability -> will likely ignore the social need (thinks it can solo)
    profile = CognitionCapacityProfile(
        planning_budget=5, judgment_stability=0.0, # Zero stability
        evidence_quality=0.8, social_bandwidth=5, detour_depth_limit=3,
        active_slice_limit=5, concern_intake_limit=3, lead_retention_limit=5,
        candidate_zone_limit=3, ally_evaluation_limit=5, blocker_resolution_patience=0.8,
        resume_reliability=0.8, interruption_resistance=0.8, abandonment_threshold_mod=1.0,
        contradiction_sensitivity=0.5, source_trust_learning_rate=0.5
    )
    
    obj = ObjectiveRecord(
        objective_id="obj_kill", project_id="prj_test",
        kind=ObjectiveKind.KILL, label="Kill Boss",
        target_id=99
    )
    
    blockers = BlockerInferenceService.infer_blockers(mock_ctx, obj, profile)
    
    # Assert SOCIAL blocker IGNORED due to misjudgment
    assert not any(b.kind == BlockerKind.SOCIAL for b in blockers)

def test_social_bandwidth_pool_limiting(mock_ctx):
    # Setup 10 potential allies
    for i in range(10, 20):
        ent = MagicMock()
        ent.id = i
        ent.identity.faction = 1
        ent.identity.reputation.trustworthiness = 0.0
        ent.identity.reputation.heroism_score = 0.0
        ent.identity.reputation.cowardice_score = 0.0
        ent.identity.reputation.reputation_tags = []
        ent.combat.alive = True
        ent.mind.social.known_bonds = {}
        # AOA Phase 1 Recovery: Ensure bond attributes don't crash when formatted if accessed
        mock_ctx.actor.mind.social.known_bonds = {}
        
        ent.spatial.pos = MagicMock()
        ent.spatial.pos.manhattan.return_value = 5
        mock_ctx.snapshot.entities[i] = ent
        
    # Bandwidth = 3 -> should only evaluate 3 candidates
    profile = CognitionCapacityProfile(
        planning_budget=5, judgment_stability=1.0, evidence_quality=0.8,
        social_bandwidth=3, detour_depth_limit=3, active_slice_limit=5,
        concern_intake_limit=3, lead_retention_limit=5, candidate_zone_limit=3,
        ally_evaluation_limit=5, blocker_resolution_patience=0.8,
        resume_reliability=0.8, interruption_resistance=0.8, abandonment_threshold_mod=1.0,
        contradiction_sensitivity=0.5, source_trust_learning_rate=0.5
    )
    
    candidates = SocialCandidateSelectionService.find_candidates(mock_ctx, profile=profile)
    
    # Even if there are 10 allies, bandwidth caps evaluation at 3
    # Note: find_candidates currently returns up to 'limit' (active_slice_limit = 5)
    # But internal pool was capped at 3
    assert len(candidates) <= 3
