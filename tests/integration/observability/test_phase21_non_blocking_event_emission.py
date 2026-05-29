import time
import pytest
from src.observability.events import SimulationEvent
from src.observability.event_recorder import EventRecorder

def test_event_recorder_non_blocking_async_writes(tmpdir):
    run_dir = str(tmpdir.mkdir("test_run"))
    
    # Initialize EventRecorder with small buffer limit
    recorder = EventRecorder(run_dir=run_dir, max_events=10, enabled=True)
    
    # Simulate hot-path record - this should return instantly without blocking on file handle flushing in main thread
    event = SimulationEvent(
        event_type="combat_damage",
        event_category="combat",
        tick=1,
        severity="INFO",
        source_system="combat_system",
        message="A test damage event"
    )
    
    start = time.perf_counter()
    recorder.record(event)
    duration = time.perf_counter() - start
    
    # Recording in hot path must be extremely cheap (e.g. sub-milliseconds)
    assert duration < 0.05
    
    # Allow background daemon worker thread to drain and execute I/O
    time.sleep(0.05)
    
    # Stats should indicate queue was successfully drained by worker thread
    stats = recorder.get_stats()
    assert stats["queue_size"] == 0
    assert stats["worker_health"] == "HEALTHY"
    
    recorder.shutdown()
