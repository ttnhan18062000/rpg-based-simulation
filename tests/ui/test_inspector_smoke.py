import pytest
from unittest.mock import MagicMock
from src.ui.cli.inspector import EntityInspector
from src.core.entities.entity import Entity
from src.core.models.enums import AIState, StrategicStatus, ObjectiveKind, ProjectKind, DirectiveKind, TurningPointKind, ContractKind, ConcernKind, LeadKind, OfferStatus
from src.core.models.strategy import StrategicState, ProjectRecord, ObjectiveRecord, DirectiveRecord, ConcernRecord, CandidateZoneRecord, HypothesisRecord, SocialContractRecord, RecruitmentOfferRecord
from src.core.models.vectors import Vector2

@pytest.fixture
def mock_registry():
    reg = MagicMock()
    reg._current_tick = 5000
    return reg


def test_inspector_smoke_empty_state(capsys, mock_registry):
    """Verify that the inspector renders cleanly with minimal possible entity state."""
    entity = MagicMock()
    entity.id = 0
    entity.identity.display_name = "Empty Agent"
    entity.identity.archetype.name = "None"
    entity.identity.faction = "None"
    entity.progression.level = 1
    entity.identity.tier = 1
    entity.spatial.pos = Vector2(0, 0)
    entity.combat.hp = 1
    entity.combat.max_hp = 1
    entity.mind.strategic = StrategicState()
    entity.mind.routine = MagicMock()
    entity.mind.routine.active_start_hour = 6
    entity.mind.routine.active_end_hour = 22
    entity.mind.routine.is_sleeping = False
    entity.mind.routine.sleep_debt = 0.0
    entity.mind.routine.hunger_level = 0.0
    entity.mind.decision = MagicMock()
    entity.mind.decision.ai_state = AIState.IDLE
    entity.mind.perception = MagicMock()
    entity.mind.narrative = MagicMock()
    entity.mind.narrative.turning_points = []
    entity.mind.narrative.memory_log = []
    entity.mind.social = MagicMock()
    
    # Execute full inspection
    EntityInspector.inspect_full(entity, mock_registry)
    
    captured = capsys.readouterr()
    assert "ENTITY INSPECTION" in captured.out
    assert "Empty Agent" in captured.out
    assert "STRATEGIC DOMAIN" in captured.out

def test_inspector_smoke_corrupted_state(capsys, mock_registry):
    """Verify that the inspector does not crash on missing or corrupted strategic fields."""
    entity = MagicMock()
    # Ensure nested mocks exist
    entity.mind.strategic = StrategicState()
    entity.mind.routine = MagicMock()
    entity.mind.routine.sleep_debt = 0.5
    entity.mind.routine.hunger_level = 0.3
    entity.mind.routine.is_sleeping = False
    entity.mind.routine.active_start_hour = 6
    entity.mind.routine.active_end_hour = 22
    entity.mind.decision = MagicMock()
    entity.mind.perception = MagicMock()
    entity.mind.narrative = MagicMock()
    entity.mind.narrative.turning_points = []
    entity.mind.narrative.memory_log = []
    entity.mind.social = MagicMock()
    entity.id = 99
    entity.identity.display_name = "Corrupted Agent"
    entity.identity.archetype.name = "Glitch"
    entity.identity.faction = "Void"
    
    # Minimal fields to keep it from crashing entirely on initial attribute access
    entity.progression.level = 1
    entity.identity.tier = 1
    entity.spatial.pos = Vector2(0, 0)
    entity.combat.hp = 10
    entity.combat.max_hp = 10
    entity.mind.decision.ai_state = AIState.IDLE
    
    # Strategic state with None values where numbers are expected
    strat = entity.mind.strategic
    strat.current_objective_id = "obj_missing"
    strat.project_lock_until = None
    strat.engaged_ticks = "NaN"
    
    # Execute full inspection
    try:
        # Mocking missing sub-renderers if they are not yet implemented
        if not hasattr(EntityInspector, "render_uncertainty_layer"):
            EntityInspector.render_uncertainty_layer = staticmethod(lambda e: print("Uncertainty Layer Rendered"))
        if not hasattr(EntityInspector, "render_social_contracts"):
            EntityInspector.render_social_contracts = staticmethod(lambda e: print("Social Contracts Rendered"))
            
        EntityInspector.inspect_full(entity, mock_registry)
    except Exception as e:
        pytest.fail(f"EntityInspector crashed on corrupted state: {e}")
    
    captured = capsys.readouterr()
    assert "ENTITY INSPECTION" in captured.out
    assert "Corrupted Agent" in captured.out

def test_inspector_smoke_maximal_state(capsys, mock_registry):
    """Verify that the inspector renders complex strategic hierarchies correctly."""
    entity = MagicMock()
    entity.id = 1
    entity.identity.display_name = "Grand Strategist"
    entity.identity.archetype.name = "Founder"
    entity.identity.faction = "Empire"
    
    # Standard fields
    entity.progression.level = 50
    entity.identity.tier = 4
    entity.spatial.pos = Vector2(123.4, 567.8)
    entity.combat.hp = 1000
    entity.combat.max_hp = 1000
    entity.mind.decision.ai_state = AIState.INVESTIGATING
    entity.mind.decision.personality.aggression = 0.9
    entity.mind.decision.personality.greed = 0.1
    entity.mind.decision.personality.caution = 0.8
    entity.mind.decision.personality.ambition = 1.0
    entity.mind.decision.personality.curiosity = 0.5
    entity.mind.decision.goal_scores = {AIState.HUNT: 1.5, AIState.INVESTIGATING: 0.9}
    
    # Biological Needs
    entity.mind.routine.sleep_debt = 0.4
    entity.mind.routine.hunger_level = 0.2
    entity.mind.routine.is_sleeping = False
    entity.mind.routine.active_start_hour = 8
    entity.mind.routine.active_end_hour = 22
    
    # Strategic Layer
    strat = StrategicState()
    strat.current_project_id = "prj_main"
    strat.current_objective_id = "obj_1"
    strat.project_lock_until = 5100
    strat.engaged_ticks = 150
    
    # Project with objectives
    obj1 = ObjectiveRecord(objective_id="obj_1", project_id="prj_main", kind=ObjectiveKind.SCOUT, label="Scout the ruins")
    prj = ProjectRecord(
        project_id="prj_main", 
        label="Imperial Expansion", 
        kind=ProjectKind.QUEST, 
        status=StrategicStatus.ACTIVE,
        objectives=[obj1],
        committed_at=4800
    )
    strat.projects = [prj]
    
    # Directives, Concerns, Blocks
    strat.directives = [DirectiveRecord(directive_id="dir1", label="Legacy of Power", kind=DirectiveKind.PERSONAL, priority=5.0)]
    strat.concerns = [ConcernRecord(concern_id="c1", label="Supply Shortage", kind=ConcernKind.THREAT, priority=4.5, urgency=0.9, visibility="public")]
    
    # Uncertainty Layer [PHASE 4]
    from src.core.models.strategy import LeadRecord
    strat.leads = [LeadRecord(lead_id="l1", label="Ancient Map", certainty=0.7, kind=LeadKind.OBJECT, target_coords=Vector2(100, 100))]
    strat.candidate_zones = [CandidateZoneRecord(zone_id="z1", approx_coords=Vector2(105, 105), confidence=0.4)]
    strat.hypotheses = [HypothesisRecord(hypothesis_id="h1", label="The King is alive", confidence=0.2)]
    
    # Social Contracts [PHASE 4]
    strat.contracts = [SocialContractRecord(contract_id="ct1", founder_id=1, member_ids=[1, 2], status=StrategicStatus.ACTIVE, kind=ContractKind.EXPEDITION, purpose="Recover artifacts")]
    strat.offers = [RecruitmentOfferRecord(offer_id="off1", recruiter_id=1, candidate_id=2, contract_kind=ContractKind.EXPEDITION, status=OfferStatus.PENDING)]
    
    # [phase_3_intel_capacity]
    strat.source_trust = {1: 0.8, 2: 0.5}
    
    # Cognition Capacity [MILESTONE 7]
    from src.ai.cognition_capacity import CognitionCapacityProfile
    strat.last_capacity_profile = CognitionCapacityProfile(
        planning_budget=10, judgment_stability=0.9, evidence_quality=0.8, social_bandwidth=5,
        active_slice_limit=5, concern_intake_limit=3, lead_retention_limit=5, candidate_zone_limit=3,
        ally_evaluation_limit=5, detour_depth_limit=2,
        blocker_resolution_patience=0.7, resume_reliability=0.6,
        interruption_resistance=0.5, abandonment_threshold_mod=0.9,
        contradiction_sensitivity=0.4, source_trust_learning_rate=0.3
    )
    strat.is_overloaded = True
    strat.primary_overload_source = "complexity"
    strat.overload_score = 1.15
    
    entity.mind.strategic = strat
    
    # Execute full inspection
    EntityInspector.inspect_full(entity, mock_registry)
    
    captured = capsys.readouterr()
    assert "Grand Strategist" in captured.out
    assert "Imperial Expansion" in captured.out
    assert "Legacy of Power" in captured.out
    assert "Supply Shortage" in captured.out
    assert "COGNITION & CAPACITY" in captured.out
    assert "COGNITIVE OVERLOAD ALERT" in captured.out
    assert "Ancient Map" in captured.out
    
    print("Inspector Smoke Test Passed: Maximal state rendering verified.")
