import pytest
from dataclasses import replace
from src.core.state import EntityState
from src.core.cognition import CognitionModel, SubjectiveModel, EmotionalModel
from src.core.self_model import SelfModelBundle, NeedInterpretationComponent
from src.domains.perception.service import AttentionFocusService

def test_low_health_focuses_on_healing_and_safety():
    entity = EntityState(id=1, kind="HERO")
    # Set dominant need to healing
    needs = NeedInterpretationComponent(dominant_need="healing")
    self_model = replace(SelfModelBundle(), needs=needs)
    entity = replace(entity, self_model=self_model)

    focus = AttentionFocusService.get_attention_focus(entity)
    assert "healing_resource" in focus
    assert "healer" in focus
    assert "safe_place" in focus

def test_fear_focuses_on_threats_and_escape():
    entity = EntityState(id=1, kind="HERO")
    # Set fear emotional state high
    emotion = EmotionalModel(fear=0.8)
    subjective = SubjectiveModel(emotion=emotion)
    cognition = CognitionModel(subjective=subjective)
    entity = replace(entity, cognition=cognition)

    focus = AttentionFocusService.get_attention_focus(entity)
    assert "threat" in focus
    assert "escape_route" in focus
    assert "ally" in focus
