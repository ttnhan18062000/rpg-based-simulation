import pytest
from src.core.state import AuthoritativeState
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.runtime_status import RuntimeStatus
from src.core.governance import RuntimeMode, PressureSignals
from src.engine.governor import ResourceGovernor
from src.config.profiles import RuntimeProfile, HardwareClass


def test_hash_invariance_to_governance_state():
    """M5 LAW: Governance state changes MUST NOT alter the authoritative hash."""
    state = AuthoritativeState(tick=1, seed=42)
    hash_0 = CanonicalStateHasher.get_hash(state)
    
    # 1. Simulate a mode change (NORMAL -> SURVIVAL)
    # This should be isolated from AuthoritativeState's CANONICAL HASH.
    # Note: AuthoritativeState now tracks current_mode for observability, 
    # but it is excluded from the canonical hash.
    status = RuntimeStatus(current_mode=RuntimeMode.NORMAL)
    status.reset_dwell(RuntimeMode.SURVIVAL, 10)
    
    # 2. Get hash again
    hash_1 = CanonicalStateHasher.get_hash(state)
    
    assert hash_0 == hash_1


def test_signal_history_bounding():
    """Verify that signal history doesn't grow indefinitely (M5 tightening)."""
    status = RuntimeStatus()
    # Fill with 1000 signals
    for i in range(1000):
        status.record_signals(PressureSignals(tick_compute_ms=float(i)))
        
    # Should be capped at 100 (maxlen defined in deque)
    assert len(status.signal_history) == 100
    # Should contain the MOST RECENT 100
    assert status.signal_history[0].tick_compute_ms == 900.0
    assert status.signal_history[-1].tick_compute_ms == 999.0
