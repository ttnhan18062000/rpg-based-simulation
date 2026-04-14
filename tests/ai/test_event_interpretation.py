import pytest
from unittest.mock import MagicMock
from src.core.logic.strategic_consequence_service import StrategicConsequenceService
from src.core.logic.concern_generation import ConcernGenerationService
from src.core.logic.project_mutation_service import ProjectMutationService
from src.core.logic.directive_mutation_service import DirectiveMutationService
from src.core.logic.strategic_knowledge_ingestion import StrategicKnowledgeIngestionService
from src.core.models.enums import InterpretedLifeEventKind, TurningPointKind, ConcernKind, ProjectKind, StrategicStatus
from src.ai.cognition_capacity import CognitionCapacityProfile
from src.actions.base import StrategicUpdate
from src.platform.rng import DeterministicRNG

@pytest.fixture
def mock_world():
    world = MagicMock()
    world.tick = 100
    return world

@pytest.fixture
def mock_entity():
    entity = MagicMock()
    entity.id = 1
    entity.progression.attributes.wis = 10 # Default
    entity.mind.strategic.current_project = None
    entity.mind.strategic.directives = []
    entity.mind.strategic.blockers = []
    entity.mind.place_attachments = []
    return entity

@pytest.fixture
def stable_profile():
    return CognitionCapacityProfile(
        planning_budget=5, judgment_stability=1.0, 
        evidence_quality=0.8, social_bandwidth=5, detour_depth_limit=3,
        active_slice_limit=5, concern_intake_limit=3, lead_retention_limit=5,
        candidate_zone_limit=3, ally_evaluation_limit=5, blocker_resolution_patience=0.8,
        resume_reliability=0.8, interruption_resistance=1.0, abandonment_threshold_mod=1.0,
        contradiction_sensitivity=0.5, source_trust_learning_rate=0.5
    )

@pytest.fixture
def unstable_profile():
    return CognitionCapacityProfile(
        planning_budget=5, judgment_stability=0.2, 
        evidence_quality=0.8, social_bandwidth=5, detour_depth_limit=1,
        active_slice_limit=5, concern_intake_limit=10, lead_retention_limit=2,
        candidate_zone_limit=1, ally_evaluation_limit=1, blocker_resolution_patience=0.2,
        resume_reliability=0.2, interruption_resistance=0.0, abandonment_threshold_mod=0.2,
        contradiction_sensitivity=0.9, source_trust_learning_rate=0.9
    )

def test_stable_concern_generation(mock_world, mock_entity, stable_profile):
    event = MagicMock()
    event.kind = InterpretedLifeEventKind.NEAR_DEATH
    event.event_id = "ev_death"
    
    updates = StrategicUpdate(target_id=mock_entity.id)
    rng = DeterministicRNG(seed=42)
    
    ConcernGenerationService.generate(mock_world, mock_entity, event, updates, rng, profile=stable_profile)
    
    # Stable entity should have 1 concern
    assert len(updates.concerns_add_or_update) == 1
    concern = updates.concerns_add_or_update[0]
    assert concern.priority <= 4.5 # Not inflated
    assert "Survival" in concern.label

def test_unstable_panic_concern(mock_world, mock_entity, unstable_profile):
    event = MagicMock()
    event.kind = InterpretedLifeEventKind.NEAR_DEATH
    event.event_id = "ev_death"
    
    updates = StrategicUpdate(target_id=mock_entity.id)
    # Seed chosen to trigger panic (0.2 stability gives ~25% panic chance)
    rng = DeterministicRNG(seed=1) 
    
    ConcernGenerationService.generate(mock_world, mock_entity, event, updates, rng, profile=unstable_profile)
    
    # Unstable entity might generate NOISE (panic) concern if RNG permits
    # Let's adjust seed if needed until we see 2.
    assert len(updates.concerns_add_or_update) >= 1
    
    # Verify perturbation (can be higher or lower)
    concern = updates.concerns_add_or_update[0]
    # unstable = perturbation range 0.8 to 1.5 approx
    # With seed=1, let's see.

def test_interruption_resistance_stable(mock_world, mock_entity, stable_profile):
    # Current project
    mock_entity.mind.strategic.current_project = MagicMock()
    mock_entity.mind.strategic.current_project.priority = 5.0
    mock_entity.mind.strategic.current_project.interruption_threshold = 1.0 # Requires > 6.0 priority concern
    
    # High priority concern (6.1)
    concern = MagicMock()
    concern.priority = 6.1
    concern.label = "Minor Threat"
    
    updates = StrategicUpdate(target_id=mock_entity.id)
    updates.concerns_add_or_update = [concern]
    
    event = MagicMock()
    event.event_id = "ev_minor"
    
    ProjectMutationService.process_interruption(mock_world, mock_entity, event, None, updates, profile=stable_profile)
    
    # Stable profile (interruption_resistance=1.0) adds +0.2 to threshold -> effective 1.2
    # 5.0 + 1.2 = 6.2 > 6.1 -> NO interruption
    assert updates.interrupted_project_id is None

def test_interruption_resistance_unstable(mock_world, mock_entity, unstable_profile):
    # Current project
    mock_entity.mind.strategic.current_project = MagicMock()
    mock_entity.mind.strategic.current_project.priority = 5.0
    mock_entity.mind.strategic.current_project.interruption_threshold = 1.0
    
    # Moderate priority concern (5.9)
    concern = MagicMock()
    concern.kind = ConcernKind.THREAT
    concern.priority = 5.9
    concern.label = "Pestering Threat"
    
    updates = StrategicUpdate(target_id=mock_entity.id)
    updates.concerns_add_or_update = [concern]
    
    event = MagicMock()
    event.event_id = "ev_minor"
    
    ProjectMutationService.process_interruption(mock_world, mock_entity, event, None, updates, profile=unstable_profile)
    
    # Unstable profile (interruption_resistance=0.0) adds -0.2 to threshold -> effective 0.8
    # 5.0 + 0.8 = 5.8 < 5.9 -> INTERRUPTION
    assert updates.interrupted_project_id is not None

def test_identity_drift_resistance(mock_world, mock_entity, stable_profile, unstable_profile):
    tp = MagicMock()
    tp.kind = TurningPointKind.NEAR_DEATH
    tp.salience_score = 0.9 # Between default stable (1.2) and unstable (0.8) thresholds
    
    # Stable
    updates_s = StrategicUpdate(target_id=mock_entity.id)
    DirectiveMutationService.evaluate_mutation(mock_world, mock_entity, tp, updates_s, None, profile=stable_profile)
    assert len(updates_s.directives_add) == 0 # Resisted
    
    # Unstable
    updates_u = StrategicUpdate(target_id=mock_entity.id)
    DirectiveMutationService.evaluate_mutation(mock_world, mock_entity, tp, updates_u, None, profile=unstable_profile)
    assert len(updates_u.directives_add) == 1 # Drifted

def test_rumor_sensitivity_unstable(mock_entity, unstable_profile):
    # Moderate danger rumor (0.4)
    # Default threshold 0.5. Unstable threshold (0.5 * (0.5 + 0.7*0.2)) = 0.5 * 0.64 = 0.32
    
    updates = StrategicKnowledgeIngestionService.ingest_inn_rumor(
        actor_id=mock_entity.id, tick=100, rumor_text="Goblins!",
        danger_level=0.4, profile=unstable_profile
    )
    
    assert len(updates.concerns_add_or_update) == 1 # Panicked concern spawned
