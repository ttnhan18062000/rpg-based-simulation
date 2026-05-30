import pytest
from src.core.cognition import RecoveryState

def test_recovery_state_model():
    state = RecoveryState()
    assert state.recent_near_death is False
    assert state.confidence_loss == 0.0
    assert state.retry_readiness == 1.0
    assert state.recovery_until_tick is None
    assert state.trauma_tags == ()
