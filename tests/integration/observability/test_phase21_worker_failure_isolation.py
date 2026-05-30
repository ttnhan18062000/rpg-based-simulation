import time
import pytest
from src.observability.events import SimulationEvent
from src.observability.event_recorder import EventRecorder

def test_worker_failure_isolation(tmpdir):
    run_dir = str(tmpdir.mkdir("test_run"))
    
    recorder = EventRecorder(run_dir=run_dir, max_events=10, enabled=True)
    
    # Intentionally corrupt the file handle or writer function to throw an exception on drain writes
    def bad_writer(env):
        raise IOError("Simulated Disk Outage / Write Failure")
        
    recorder._worker.file_write_fn = bad_writer
    
    # Record a new event - should push to queue successfully without throwing any exception in hot path
    event = SimulationEvent(
        event_type="movement",
        event_category="movement",
        tick=2,
        severity="WARNING",
        source_system="locomotion_system",
        message="A test movement event"
    )
    
    # Hot-path record does not fail
    recorder.record(event)
    
    # Give the background daemon thread time to attempt processing
    time.sleep(0.05)
    
    # Worker should have isolated the exception, remained active, and updated its health state to DEGRADED
    stats = recorder.get_stats()
    assert stats["worker_failures"] > 0
    assert stats["worker_health"] == "DEGRADED"
    
    # Shutdown handles failure gracefully
    recorder.shutdown()
