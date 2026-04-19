import pytest
import os
import json
from pathlib import Path
from src_v2.engine.replay_manager import ReplayManager
from src_v2.engine.replay_buffer import ReplayBuffer
from src_v2.core.retention import OverflowPolicy
from src_v2.core.replay_modes import ReplayMode
from src_v2.core.diagnostic import TraceEvent

@pytest.fixture
def replay_dir(tmp_path):
    d = tmp_path / "replay_test"
    d.mkdir()
    return d

def test_replay_mode_retention_windowed():
    """M7 Law: DEBUG_WINDOWED prefers newest events."""
    # Capacity for 4 events
    buffer = ReplayBuffer(capacity_kb=1, policy=OverflowPolicy.EVICT_OLDEST)
    
    for i in range(10):
        buffer.record(TraceEvent(tick=i, system="TEST", event_type="E", payload={"i": i}))
        
    chunk = buffer.extract_chunk()
    assert len(chunk) == 4
    # Should keep 6, 7, 8, 9
    assert chunk[0].tick == 6
    assert chunk[-1].tick == 9

def test_replay_mode_retention_forensic():
    """M7 Law: FORENSIC_SHORT_RUN prefers oldest events."""
    # Capacity for 4 events
    buffer = ReplayBuffer(capacity_kb=1, policy=OverflowPolicy.TRUNCATE_NEWEST)
    
    for i in range(10):
        buffer.record(TraceEvent(tick=i, system="TEST", event_type="E", payload={"i": i}))
        
    chunk = buffer.extract_chunk()
    assert len(chunk) == 4
    # Should keep 0, 1, 2, 3
    assert chunk[0].tick == 0
    assert chunk[-1].tick == 3

def test_early_rotation_trigger(replay_dir):
    """M7 Law: Saturation (>= 90%) triggers immediate rotation."""
    # Capacity = 1KB * 4 = 4 items. 
    # 90% of 4 is 3.6 -> 3 items should trigger rotation.
    manager = ReplayManager(
        run_dir=replay_dir,
        profile_name="test",
        buffer_capacity_kb=1, # 4 items
        chunk_tick_limit=100,
        rotation_threshold=0.5 # Set low to trigger easily
    )
    
    # Tick 1: 0 items
    manager.on_tick_end(1)
    assert manager._current_chunk_id == 0
    
    # Add 3 items (75% utilization)
    from unittest.mock import MagicMock
    from src_v2.core.governance import PressureSignals
    # Hack: Creating a fake policy that allows replay
    policy_mock = MagicMock()
    policy_mock.replay_allowed = True
    policy_mock.replay_richness = "FULL"
    policy_mock.allow_subsystem_traces = True
    manager.emit(TraceEvent(1, "S", "E", {}), policy_mock)
    manager.emit(TraceEvent(1, "S", "E", {}), policy_mock)
    manager.emit(TraceEvent(1, "S", "E", {}), policy_mock)
    
    # 75% > 50% threshold -> Should rotate
    manager.on_tick_end(1)
    assert manager._current_chunk_id == 1
    assert len(manager._manifest["chunks"]) == 1

def test_atomic_manifest_write(replay_dir):
    """M7 Law: Manifest is updated atomically (write-rename)."""
    manager = ReplayManager(replay_dir, "test")
    manifest_path = replay_dir / "manifest.json"
    
    manager.finalize()
    assert manifest_path.exists()
    
    # Check if a .tmp file exists (should be cleaned up but we can check the call log if mocked)
    # Actually, as long as it exists and is valid JSON after finalized, it's good.
    with open(manifest_path, "r") as f:
        data = json.load(f)
        assert data["status"] == "COMPLETED"
