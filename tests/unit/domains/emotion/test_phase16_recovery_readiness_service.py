import pytest
from src.core.cognition import RecoveryState
from src.domains.emotion.recovery_service import RecoveryReadinessService

def test_recovery_readiness_service():
    state = RecoveryState(recent_near_death=True, retry_readiness=0.2)
    
    # Near death reduces readiness
    assert RecoveryReadinessService.is_ready_to_retry(state, current_tick=10) is False
    
    # Recovery complete
    state_recovered = RecoveryState(recent_near_death=False, retry_readiness=1.0)
    assert RecoveryReadinessService.is_ready_to_retry(state_recovered, current_tick=10) is True
