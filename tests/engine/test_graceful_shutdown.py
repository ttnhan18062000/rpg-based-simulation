import pytest
import time
from pathlib import Path
from unittest.mock import MagicMock
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.state import AuthoritativeState
from src.platform.rng import DeterministicRNG

@pytest.fixture
def basic_profile():
    return RuntimeProfile(
        name="test_profile",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=512,
        max_cpu_percent=80,
        max_worker_count=4,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=10,
        max_tick_budget_ms=16.6
    )

def test_shutdown_sequence_suspension(basic_profile):
    """M7 Law: Shutdown must suspend new work arrival."""
    state = AuthoritativeState(tick=0, seed=42)
    rng = DeterministicRNG(42)
    kernel = Kernel(profile=basic_profile, state=state, rng=rng)
    
    kernel.shutdown()
    
    # Attempting to tick after shutdown should do nothing (return early)
    # We check if world_time stays same
    initial_time = state.world_time
    kernel.tick_once() 
    assert state.world_time == initial_time

def test_shutdown_timeout_logic(basic_profile, tmp_path):
    """M7 Law: Shutdown flush respects timeout."""
    state = AuthoritativeState(tick=0, seed=42)
    rng = DeterministicRNG(42)
    
    # Mock ReplayManager to simulate slow finalize
    mock_replay = MagicMock()
    
    kernel = Kernel(profile=basic_profile, state=state, rng=rng, replay=mock_replay)
    
    kernel.shutdown(timeout_s=0.1)
    
    # Verify mock_replay.finalize was called with timeout
    mock_replay.finalize.assert_called_once_with(timeout_s=0.1)

def test_final_hash_logged(basic_profile, caplog):
    """M7 Law: Final authoritative hash emitted at shutdown."""
    import logging
    caplog.set_level(logging.INFO)
    
    state = AuthoritativeState(tick=0, seed=42)
    rng = DeterministicRNG(42)
    kernel = Kernel(profile=basic_profile, state=state, rng=rng)
    
    kernel.shutdown()
    
    assert "Final Auth Hash:" in caplog.text
