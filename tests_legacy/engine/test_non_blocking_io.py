import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src_legacy.engine.replay_manager import ReplayManager
from src_legacy.core.replay_modes import ReplayMode

def test_on_tick_end_is_non_blocking_on_io(tmp_path):
    """
    M7 Law: Replay persistence MUST NOT block the kernel heart-beat.
    """
    # Setup
    rm = ReplayManager(
        run_dir=tmp_path,
        profile_name="test_profile",
        buffer_capacity_kb=1024,
        replay_mode=ReplayMode.DEBUG_WINDOWED
    )
    
    # Mock the sink's persist_chunk to be SLOW
    original_persist = rm._sink.persist_chunk
    
    def slow_persist(chunk_id, events):
        time.sleep(0.5) # 500ms delay
        return original_persist(chunk_id, events)
        
    rm._sink.persist_chunk = MagicMock(side_effect=slow_persist)
    
    # Fill buffer slightly so there's something to rotate
    from src_legacy.core.diagnostic import TraceEvent
    from src_legacy.engine.policy import GovernorPolicy
    rm.emit(TraceEvent(tick=1, system="K", event_type="T"), GovernorPolicy())
    
    # Measure time for on_tick_end (with chunk rotation)
    # Since rotation trigger is 100 ticks or 0.9 saturation, 
    # we manually trigger by setting chunk_tick_limit to 1 or just calling _rotate_chunk
    
    start_time = time.perf_counter()
    rm._rotate_chunk(end_tick=1)
    duration = time.perf_counter() - start_time
    
    # Assertion: on_tick_end/rotate_chunk should return almost immediately (<10ms)
    # despite the 500ms sleep in the sink.
    assert duration < 0.1, f"Rotation blocked for {duration:.4f}s"
    
    # Wait a bit for the background thread to finish
    time.sleep(0.7)
    
    # Verify the chunk was eventually persisted
    assert rm._sink.persist_chunk.called
    assert len(rm._manifest["chunks"]) == 1
    
    # Cleanup
    rm.finalize()
