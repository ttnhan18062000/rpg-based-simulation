from __future__ import annotations
import os
import shutil
import time
import pytest
from src.observability.events import SimulationEvent
from src.observability.event_recorder import EventRecorder

@pytest.fixture
def run_dir(tmp_path):
    path = tmp_path / "test_run"
    yield str(path)
    if path.exists():
        shutil.rmtree(path)

def test_event_recorder_disabled():
    recorder = EventRecorder(enabled=False)
    ev = SimulationEvent(
        event_type="test_event",
        event_category="combat",
        tick=1,
        severity="INFO",
        source_system="test",
        message="test message",
        entity_id=1
    )
    recorder.record(ev)
    assert len(recorder.events) == 0
    assert recorder.dropped_event_count == 0

def test_event_recorder_bounds_and_eviction(run_dir):
    # Setup event recorder with capacity limit of 3
    recorder = EventRecorder(run_dir=run_dir, max_events=3, enabled=True)
    # Ensure queue capacity is high enough so it doesn't drop low priority events under queue pressure,
    # allowing the test to verify in-memory buffer bounds and file writing independently.
    recorder.queue.max_size = 100

    ev_info1 = SimulationEvent(
        event_type="info_event", event_category="combat", tick=1, severity="INFO",
        source_system="test", message="info 1", entity_id=1
    )
    ev_info2 = SimulationEvent(
        event_type="info_event", event_category="combat", tick=2, severity="INFO",
        source_system="test", message="info 2", entity_id=2
    )
    ev_debug = SimulationEvent(
        event_type="debug_event", event_category="movement", tick=3, severity="DEBUG",
        source_system="test", message="debug 1", entity_id=3
    )

    recorder.record(ev_info1)
    recorder.record(ev_info2)
    recorder.record(ev_debug)

    assert len(recorder.events) == 3
    assert recorder.dropped_event_count == 0

    # Record another INFO event. Capacity is full.
    # The oldest event of the lowest severity is the DEBUG event (severity=DEBUG, index=2).
    # Eviction should evict the DEBUG event.
    ev_info3 = SimulationEvent(
        event_type="info_event", event_category="combat", tick=4, severity="INFO",
        source_system="test", message="info 3", entity_id=4
    )
    recorder.record(ev_info3)

    assert len(recorder.events) == 3
    assert recorder.dropped_event_count == 1
    # Check that ev_debug is evicted
    assert ev_debug not in recorder.events
    assert ev_info1 in recorder.events
    assert ev_info2 in recorder.events
    assert ev_info3 in recorder.events

    # Now let's record a CRITICAL event.
    # The lowest severity events left are INFO events. The oldest is ev_info1.
    # It should evict ev_info1.
    ev_crit = SimulationEvent(
        event_type="crit_event", event_category="hard_law", tick=5, severity="CRITICAL",
        source_system="test", message="critical", entity_id=5
    )
    recorder.record(ev_crit)

    assert len(recorder.events) == 3
    assert recorder.dropped_event_count == 2
    assert ev_info1 not in recorder.events
    assert ev_crit in recorder.events

    # Shutdown to close file handles, which stops the worker and drains all remaining events synchronously
    recorder.shutdown()
    
    # Assert JSONL file exists and is populated
    jsonl_path = os.path.join(run_dir, "simulation_events.jsonl")
    assert os.path.exists(jsonl_path)
    with open(jsonl_path, "r") as f:
        lines = f.readlines()
        assert len(lines) == 5  # All recorded events were written to JSONL regardless of in-memory evictions!


def test_event_recorder_write_envelope_does_not_flush_directly(run_dir):
    """_write_envelope_to_file() (called per-record by QueueDrainWorker inside a drain cycle)
    never flushes on its own — flushing is the drain cycle's own responsibility (once per
    non-empty cycle, via QueueDrainWorker's flush_fn), not tied to a per-record counter.
    TCK-20260830 (post-merge regression fix): the earlier every-50-records counter deferred
    visibility of low-volume writers (e.g. a single injected test event) past any real drain
    cycle, breaking any consumer that reads simulation_events.jsonl mid-run without a shutdown."""
    recorder = EventRecorder(run_dir=run_dir, max_events=1000, enabled=True)
    recorder.queue.max_size = 1000
    try:
        flush_calls = {"count": 0}
        real_flush = recorder._file_handle.flush

        def _spy_flush():
            flush_calls["count"] += 1
            real_flush()

        recorder._file_handle.flush = _spy_flush

        from src.observability.events import ObservabilityEventEnvelope

        for i in range(5):
            ev = SimulationEvent(
                event_type="info_event", event_category="combat", tick=i, severity="INFO",
                source_system="test", message=f"info {i}", entity_id=i,
            )
            recorder._write_envelope_to_file(ObservabilityEventEnvelope.from_simulation_event(ev))

        assert flush_calls["count"] == 0
    finally:
        recorder.shutdown()


def test_event_recorder_drain_worker_flushes_once_per_nonempty_cycle(run_dir):
    """A single low-volume event enqueued via the real record()/queue/worker path becomes
    visible in simulation_events.jsonl after one drain-worker cycle (~_worker.interval_sec),
    without needing 50 accumulated records or a shutdown() call."""
    recorder = EventRecorder(run_dir=run_dir, max_events=1000, enabled=True)
    recorder.queue.max_size = 1000
    try:
        ev = SimulationEvent(
            event_type="info_event", event_category="combat", tick=1, severity="INFO",
            source_system="test", message="single low-volume event", entity_id=1,
        )
        recorder.record(ev)
        deadline = time.monotonic() + 2.0
        lines = []
        while time.monotonic() < deadline:
            with open(recorder.filepath, "r", encoding="utf-8") as f:
                lines = [ln for ln in f if ln.strip()]
            if lines:
                break
            time.sleep(0.02)
        assert lines, "single event never became visible on disk within 2s of a real drain cycle"
    finally:
        recorder.shutdown()


def test_event_recorder_shutdown_flushes_remaining_writes(run_dir):
    recorder = EventRecorder(run_dir=run_dir, max_events=1000, enabled=True)
    recorder.queue.max_size = 1000
    flush_calls = {"count": 0}
    real_flush = recorder._file_handle.flush

    def _spy_flush():
        flush_calls["count"] += 1
        real_flush()

    recorder._file_handle.flush = _spy_flush

    from src.observability.events import ObservabilityEventEnvelope
    ev = SimulationEvent(
        event_type="info_event", event_category="combat", tick=1, severity="INFO",
        source_system="test", message="info 1", entity_id=1,
    )
    recorder._write_envelope_to_file(ObservabilityEventEnvelope.from_simulation_event(ev))
    assert flush_calls["count"] == 0

    recorder.shutdown()
    assert flush_calls["count"] >= 1
