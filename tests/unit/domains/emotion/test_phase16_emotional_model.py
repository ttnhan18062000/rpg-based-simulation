import pytest
from src.core.cognition import EmotionalModel

def test_emotional_model_initialization():
    model = EmotionalModel()
    assert model.fear == 0.0
    assert model.confidence == 0.5
    assert model.frustration == 0.0
    assert model.curiosity == 0.0
    assert model.satisfaction == 0.0
    assert model.panic == 0.0
    assert model.boredom == 0.0
