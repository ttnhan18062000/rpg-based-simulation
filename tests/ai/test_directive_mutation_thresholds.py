import pytest
from unittest.mock import MagicMock
from src.ai.states.base import AIContext
from src.core.logic.directive_mutation_service import DirectiveMutationService
from src.core.models.strategy import StrategicState, DirectiveRecord, DirectiveKind
from src.core.models.life_events import TurningPointRecord
from src.core.models.enums import TurningPointKind
from src.actions.base import StrategicUpdate
from src.ai.cognition_capacity import CognitionCapacityProfile

@pytest.fixture
def base_ctx():
    ctx = MagicMock(spec=AIContext)
    ctx.snapshot = MagicMock()
    ctx.snapshot.tick = 400
    
    actor = MagicMock()
    actor.id = 1
    strat = StrategicState()
    actor.mind.strategic = strat
    actor.mind.narrative.turning_points = []
    
    ctx.actor = actor
    return ctx

def test_directive_mutation_thresholds(base_ctx):
    """Verify that directives only mutate after repeated thresholded events."""
    actor = base_ctx.actor
    strat = actor.mind.strategic
    updates = StrategicUpdate(target_id=actor.id)
    
    profile = CognitionCapacityProfile(
        planning_budget=5, judgment_stability=0.5, evidence_quality=0.8,
        social_bandwidth=5, detour_depth_limit=3, active_slice_limit=5,
        concern_intake_limit=3, lead_retention_limit=5, candidate_zone_limit=3,
        ally_evaluation_limit=5, blocker_resolution_patience=0.8,
        resume_reliability=0.8, interruption_resistance=0.8,
        abandonment_threshold_mod=1.0, 
        contradiction_sensitivity=0.5,
        source_trust_learning_rate=0.4
    )
    
    # 1. First Near Death (Threshold: 2)
    tp1 = TurningPointRecord(
        event_id="tp1", kind=TurningPointKind.NEAR_DEATH, tick=100, 
        salience_score=1.0 # Passes salience check
    )
    actor.mind.narrative.turning_points = [tp1]
    
    DirectiveMutationService.evaluate_mutation(base_ctx.snapshot, actor, tp1, updates, profile=profile)
    assert not updates.directives_add, "First Near Death should not trigger directive yet."
    
    # 2. Second Near Death
    # (Note: In reality, both would be in history when the second is processed)
    tp2 = TurningPointRecord(
        event_id="tp2", kind=TurningPointKind.NEAR_DEATH, tick=200, 
        salience_score=1.2
    )
    actor.mind.narrative.turning_points = [tp1, tp2]
    
    DirectiveMutationService.evaluate_mutation(base_ctx.snapshot, actor, tp2, updates, profile=profile)
    assert len(updates.directives_add) == 1
    dir_record = updates.directives_add[0]
    assert dir_record.label == "Safety & Self-Preservation"
    assert dir_record.priority == 3.5
    
    # 3. Third Near Death (Strengthen)
    # Mock existing state
    strat.directives = [dir_record]
    updates.directives_add = [] # Clear updates
    
    tp3 = TurningPointRecord(
        event_id="tp3", kind=TurningPointKind.NEAR_DEATH, tick=300, 
        salience_score=1.5
    )
    actor.mind.narrative.turning_points = [tp1, tp2, tp3]
    
    DirectiveMutationService.evaluate_mutation(base_ctx.snapshot, actor, tp3, updates, profile=profile)
    assert len(updates.directives_add) == 1
    assert updates.directives_add[0].priority == 4.0 # 3.5 + 0.5
    
    # 4. Immediate Betrayal (Threshold: 1)
    updates.directives_add = []
    tp_betrayal = TurningPointRecord(
        event_id="tp_b", kind=TurningPointKind.BETRAYAL, tick=350, 
        salience_score=2.0
    )
    actor.mind.narrative.turning_points.append(tp_betrayal)
    
    DirectiveMutationService.evaluate_mutation(base_ctx.snapshot, actor, tp_betrayal, updates, profile=profile)
    assert any(d.label == "Avenge Betrayal/Loss" for d in updates.directives_add)
    
    print("Directive Mutation Threshold Test Passed: Persistent identity shifts confirmed.")
