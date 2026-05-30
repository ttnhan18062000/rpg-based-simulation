import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.core.cognition import CognitionModel, SubjectiveModel, EmotionalModel
from src.domains.perception.salience import WorldSignal, SignalSalienceEvaluator

def test_nearby_threat_has_high_salience():
    entity = EntityState(id=1, kind="HERO")
    # Position at (0, 0)
    entity = replace(entity, navigation=replace(entity.navigation, position=(0.0, 0.0)))
    # Setup high fear emotional state
    emotion = EmotionalModel(fear=0.8)
    subjective = SubjectiveModel(emotion=emotion)
    entity = replace(entity, cognition=CognitionModel(subjective=subjective))

    threat = WorldSignal(
        signal_id="mob_1",
        kind="threat",
        position=(1.0, 1.0),
        base_relevance=0.5,
        danger_level=0.6
    )

    salience = SignalSalienceEvaluator.evaluate(entity, threat, ("threat",))
    # Base (0.5) + Attention bonus (0.3) + Danger level (0.6 * 1.8 = 1.08) - distance penalty (1.41 * 0.01 = 0.0141) = ~1.86
    assert salience > 1.5

def test_far_irrelevant_signal_has_low_salience():
    entity = EntityState(id=1, kind="HERO")
    # Far away at (100, 100)
    entity = replace(entity, navigation=replace(entity.navigation, position=(0.0, 0.0)))

    signal = WorldSignal(
        signal_id="herb_1",
        kind="healing_resource",
        position=(100.0, 100.0),
        base_relevance=0.1
    )

    salience = SignalSalienceEvaluator.evaluate(entity, signal, ())
    # Base (0.1) - distance penalty (141.4 * 0.01 = 1.414) -> clamped to 0.0
    assert salience == 0.0
