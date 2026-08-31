import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.core.cognition import CognitionModel, EmotionalModel, RecoveryState, HabitMemory, MemoryModel
from src.domains.emotion.emotion_service import EmotionUpdateService
from src.domains.emotion.recovery_service import RecoveryReadinessService
from src.domains.emotion.habit_service import HabitBiasService
from src.domains.emotion.opportunity_cost import OpportunityCostEvaluator

def test_near_death_prevents_immediate_retry():
    # Setup near_death recovery state
    recovery = RecoveryState(recent_near_death=True, retry_readiness=0.1)

    # Check retry readiness
    assert RecoveryReadinessService.is_ready_to_retry(recovery, current_tick=10) is False

def test_repeated_failure_causes_route_switch():
    # Base frustration increases
    emotion = EmotionalModel(frustration=0.8)
    cognition = CognitionModel(subjective=replace(CognitionModel().subjective, emotion=emotion))
    entity = replace(EntityState(id=1, kind="HERO"), cognition=cognition)

    # Emotion update on repeated failure raises frustration further
    updated_emotion = EmotionUpdateService.update_on_event(entity.cognition.subjective.emotion, "repeated_failure")
    assert updated_emotion.frustration > 0.9

def test_opportunity_cost_prevents_selling_needed_material():
    # Evaluate selling a material needed for strategic upgrade
    cost = OpportunityCostEvaluator.evaluate_cost(
        action_kind="sell_material",
        is_needed_for_upgrade=True,
        has_alternative=False
    )
    assert cost > 0.8
