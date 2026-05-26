from __future__ import annotations
import os
import shutil
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

    # Shutdown to close file handles
    recorder.shutdown()
    
    # Assert JSONL file exists and is populated
    jsonl_path = os.path.join(run_dir, "simulation_events.jsonl")
    assert os.path.exists(jsonl_path)
    with open(jsonl_path, "r") as f:
        lines = f.readlines()
        assert len(lines) == 5  # All recorded events were written to JSONL regardless of in-memory evictions!
