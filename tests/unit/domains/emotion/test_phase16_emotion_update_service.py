import pytest
from src.core.cognition import EmotionalModel
from src.domains.emotion.emotion_service import EmotionUpdateService

def test_emotion_update_service():
    model = EmotionalModel(fear=0.2, confidence=0.5, frustration=0.1)
    
    # Near death updates fear and panic
    model_nd = EmotionUpdateService.update_on_event(model, "near_death")
    assert model_nd.fear > 0.5
    assert model_nd.panic >= 0.5
    
    # Easy win updates confidence
    model_ew = EmotionUpdateService.update_on_event(model, "easy_win")
    assert model_ew.confidence > 0.5
    
    # Repeated failure updates frustration
    model_rf = EmotionUpdateService.update_on_event(model, "repeated_failure")
    assert model_rf.frustration > 0.3
