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


def test_event_recorder_shutdown_final_drain_still_calls_quality_fn():
    """Regression test for TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD.

    EventRecorder.shutdown()'s own final synchronous drain (step 2) handles any envelope
    pushed into the queue after the background QueueDrainWorker's last loop iteration but
    before .stop() took effect. Before this fix that final drain wrote to file/stream but
    never invoked quality_fn, so an event caught in that window would never reach quality
    scoring/persistence at all — a silent drop distinct from (but adjacent to) the
    Kernel-level ordering hazard. Reproduced deterministically (no sleep/race) by stopping
    the worker before the event is ever pushed, forcing it to only be picked up by
    shutdown()'s manual final drain.
    """
    received = []
    recorder = EventRecorder(enabled=True, quality_fn=lambda env: received.append(env))

    # Permanently halt the background worker before anything is queued, so the event
    # pushed below can only be handled by shutdown()'s own final drain, not the worker's
    # normal _run() loop.
    recorder._worker.stop()
    assert not recorder._worker.is_alive()

    recorder.record(_make_event(tick=1))
    assert recorder.queue.get_size() == 1, "event should still be sitting unprocessed in the queue"

    recorder.shutdown()

    assert len(received) == 1, (
        "quality_fn was not called for an event stranded in the queue when the worker "
        "already stopped — EventRecorder.shutdown()'s final manual drain must still route "
        "through quality_fn, not just file/stream writes"
    )
