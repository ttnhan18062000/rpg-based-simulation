import pytest
import logging
from src_v2.config.profiles import RuntimeProfile, HardwareClass
from src_v2.core.state import AuthoritativeState
from src_v2.engine.kernel import Kernel
from unittest.mock import MagicMock, patch


def test_graceful_shutdown_sequence(tmp_path, caplog):
    """
    M7 Law: Shutdown must preserve authoritative integrity and 
    emit a final checkpoint hash.
    """
    profile = RuntimeProfile(
        name="SHUTDOWN_TEST",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=50.0,
        max_worker_count=4,
        max_queue_depth=1000,
        max_work_debt=100,
        max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=10.0
    )
    state = AuthoritativeState(tick=42, seed=42)
    
    # Mock replay so we can see finalize call
    mock_replay = MagicMock()
    
    kernel = Kernel(
        profile=profile, state=state, rng=MagicMock(), replay=mock_replay
    )
    
    with caplog.at_level(logging.INFO):
        kernel.shutdown()
        
    # 1. Verify Auth Hash emission
    assert "Final Auth Hash" in caplog.text
    
    # 2. Verify Replay Finalization
    assert mock_replay.finalize.called


def test_shutdown_resilience_to_stalled_io(tmp_path):
    """
    M7 Law: Implementation of a hard timeout check in finalize is not 
    possible in a single-threaded mock, but we verify error handling.
    """
    profile = RuntimeProfile(
        name="RESILIENT_SHUTDOWN",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=50.0,
        max_worker_count=4,
        max_queue_depth=1000,
        max_work_debt=100,
        max_replay_buffer_kb=64,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=10.0
    )
    state = AuthoritativeState(tick=0, seed=42)
    
    from src_v2.engine.replay_manager import ReplayManager
    run_dir = tmp_path / "stalled_run"
    replay = ReplayManager(run_dir=run_dir, profile_name="TEST")
    
    # Mocking _rotate_chunk to fail
    with patch.object(replay, "_rotate_chunk", side_effect=IOError("Stalled IO")):
        kernel = Kernel(profile=profile, state=state, rng=MagicMock(), replay=replay)
        
        # Shutdown should NOT raise even if rotate fails
        kernel.shutdown()
        
    # Manifest should still be marked as completed
    assert replay._manifest["status"] == "COMPLETED"
