import pytest
import time
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.engine.replay_manager import ReplayManager
from src.core.replay_modes import ReplayMode

def test_shutdown_skips_rotation_on_low_budget(tmp_path):
    """
    M7 Law: Shutdown must be bounded. Skip non-authoritative work if near timeout.
    """
    # Initialize manager with a small buffer and a mock sink
    rm = ReplayManager(
        run_dir=tmp_path,
        profile_name="test_profile",
        buffer_capacity_kb=1024,
        replay_mode=ReplayMode.DEBUG_WINDOWED
    )
    
    # Mock the sink's rotate method to verify if it's called
    rm._rotate_chunk = MagicMock()
    
    # We will simulate a situation where 4.6 seconds have already passed
    # out of a 5.0 second budget. The safety margin is 0.5s.
    # 5.0 - 4.6 = 0.4s remains. 0.4s < 0.5s safety margin. 
    # Therefore, rotation should be SKIPPED.
    
    start_time = time.perf_counter()
    with patch('time.perf_counter', side_effect=[start_time, start_time + 4.6, start_time + 4.65]):
        rm.finalize(timeout_s=5.0)
        
    # Assertions
    rm._rotate_chunk.assert_not_called()
    assert rm._manifest["status"] == "SKIPPED_TIMEOUT"

def test_shutdown_performs_rotation_on_ample_budget(tmp_path):
    """Verify that rotation IS performed if budget allows."""
    rm = ReplayManager(run_dir=tmp_path, profile_name="test")
    rm._rotate_chunk = MagicMock()
    
    # 0.1s elapsed, 4.9s remain. Plenty of budget.
    start_time = time.perf_counter()
    with patch('time.perf_counter', side_effect=[start_time, start_time + 0.1, start_time + 0.15]):
        rm.finalize(timeout_s=5.0)
        
    rm._rotate_chunk.assert_called_once()
    assert rm._manifest["status"] == "COMPLETED"
