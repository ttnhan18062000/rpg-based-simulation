"""Unit tests for EventRecorder.quality_fn wiring (TCK-20260630-SIMQ-WIRE-KERNEL)."""
from __future__ import annotations

import time
import pytest

from src.observability.event_recorder import EventRecorder
from src.observability.events import SimulationEvent


def _make_event(tick: int = 1, event_type: str = "test_event") -> SimulationEvent:
    return SimulationEvent(
        event_type=event_type,
        event_category="combat",
        tick=tick,
        severity="INFO",
        source_system="test",
        message="unit test event",
        entity_id=1,
    )


def test_event_recorder_quality_fn_none_by_default():
    recorder = EventRecorder(enabled=True)
    assert recorder._worker.quality_fn is None
    recorder.shutdown()


def test_event_recorder_passes_quality_fn_to_worker():
    called = []
    recorder = EventRecorder(enabled=True, quality_fn=lambda env: called.append(env))
    assert recorder._worker.quality_fn is not None
    recorder.shutdown()


def test_event_recorder_quality_fn_called_on_drain():
    received = []
    recorder = EventRecorder(enabled=True, quality_fn=lambda env: received.append(env))
    recorder.record(_make_event(tick=1))
    recorder.record(_make_event(tick=2))

    # Give drain worker time to process
    time.sleep(0.1)

    recorder.shutdown()
    assert len(received) >= 2, f"Expected ≥2 calls to quality_fn, got {len(received)}"


def test_event_recorder_quality_fn_exception_does_not_crash_worker():
    """An exception inside quality_fn must not kill the drain worker thread."""
    good_calls = []

    def bad_fn(env):
        raise RuntimeError("scorer exploded")

    recorder = EventRecorder(enabled=True, quality_fn=bad_fn)
    for i in range(3):
        recorder.record(_make_event(tick=i))

    time.sleep(0.1)

    assert recorder._worker.is_alive(), "Drain worker crashed after quality_fn exception"
    recorder.shutdown()
