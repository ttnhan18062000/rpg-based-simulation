"""
Phase 28 initial guard — Observability degradation integration tests.

These tests verify the core safety properties from Phase 28:
1. Queue full does not block the simulation tick.
2. Worker failure degrades observability (not the engine).
3. Critical/CRITICAL-severity events are protected.
4. Dropped event count is tracked.
"""
from __future__ import annotations

import time
import threading

import pytest

from src.observability.events import ObservabilityEventEnvelope
from src.observability.queue import BoundedObservabilityQueue, PushStatus
from src.observability.behavior.worker import BehaviorWorker
from src.observability.behavior.normalization_context import BehaviorNormalizationContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_env(severity: str = "INFO", tick: int = 1) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=f"env_{severity}_{tick}",
        run_id="run_phase28",
        tick=tick,
        entity_id=1,
        event_type="movement",
        event_category="movement",
        severity=severity,
        source_system="test",
        message="phase28 test event",
    )


# ---------------------------------------------------------------------------
# Queue safety tests
# ---------------------------------------------------------------------------

class TestQueueFullDoesNotBlockTick:

    def test_queue_full_does_not_block_tick(self):
        """
        When the queue is full, try_push must return immediately
        without blocking the simulation tick thread.
        """
        queue = BoundedObservabilityQueue(max_size=5)

        # Fill the queue
        for i in range(5):
            queue.try_push(_make_env("INFO", tick=i))

        # Now push to a full queue — must complete without blocking
        start = time.monotonic()
        result = queue.try_push(_make_env("INFO", tick=99))
        elapsed = time.monotonic() - start

        # Should return in microseconds, not milliseconds
        assert elapsed < 0.01, f"Queue push blocked: {elapsed:.4f}s"
        assert result in (PushStatus.DROPPED, PushStatus.REJECTED)

    def test_critical_event_survives_full_queue(self):
        """
        CRITICAL severity events must be kept even when queue is full,
        by evicting a lower-priority event.
        """
        queue = BoundedObservabilityQueue(max_size=5)

        # Fill with low-priority events
        for i in range(5):
            queue.try_push(_make_env("INFO", tick=i))

        # Push a critical event — it should succeed by evicting an INFO event
        result = queue.try_push(_make_env("CRITICAL", tick=99))
        assert result == PushStatus.SUCCESS
        assert queue.get_size() == 5  # Size remains at capacity

    def test_low_priority_events_are_dropped_when_full(self):
        """
        Low-priority (INFO) events must be dropped when the queue is
        full of low-priority events and a new low-priority event arrives.
        """
        queue = BoundedObservabilityQueue(max_size=3)
        for i in range(3):
            queue.try_push(_make_env("INFO", tick=i))

        result = queue.try_push(_make_env("INFO", tick=99))
        assert result == PushStatus.DROPPED
        assert queue.dropped_count >= 1

    def test_dropped_event_count_is_recorded(self):
        """Dropped event count must be tracked correctly."""
        queue = BoundedObservabilityQueue(max_size=2)
        queue.try_push(_make_env("INFO", tick=1))
        queue.try_push(_make_env("INFO", tick=2))
        queue.try_push(_make_env("INFO", tick=3))  # dropped
        queue.try_push(_make_env("INFO", tick=4))  # dropped

        assert queue.dropped_count >= 2


# ---------------------------------------------------------------------------
# Worker failure isolation tests
# ---------------------------------------------------------------------------

class TestWorkerFailureIsolation:

    def test_worker_exception_does_not_crash_engine(self):
        """
        A crashing output_fn must not propagate exceptions to the engine.
        The worker degrades gracefully.
        """
        from pathlib import Path
        import tempfile
        import json

        def _crashing_output(be):
            raise RuntimeError("Simulated downstream failure")

        ctx = BehaviorNormalizationContext.minimal("run_phase28")
        worker = BehaviorWorker(context=ctx, output_fn=_crashing_output)

        # Write a minimal JSONL event file to process
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            json.dump({
                "event_id": "evt_phase28",
                "event_type": "movement",
                "event_category": "movement",
                "tick": 1,
                "severity": "INFO",
                "source_system": "test",
                "message": "test",
                "entity_id": 1,
                "run_id": "run_phase28",
                "start_pos": [0.0, 0.0],
                "end_pos": [1.0, 1.0],
                "payload": {},
            }, f)
            f.write("\n")
            tmp_path = Path(f.name)

        # Must not raise
        result = worker.process_jsonl(tmp_path)

        # Worker degrades — health is DEGRADED after failure
        assert worker.health_status == "DEGRADED"

        tmp_path.unlink(missing_ok=True)

    def test_queue_worker_exception_does_not_crash_caller(self):
        """
        Exceptions inside the queue drain loop must be caught;
        the simulation loop that pushes to queue must never see them.
        """
        queue = BoundedObservabilityQueue(max_size=50)

        def _crashing_output(be):
            raise OSError("Disk full simulation")

        ctx = BehaviorNormalizationContext.minimal("run_phase28")
        worker = BehaviorWorker(
            context=ctx,
            output_fn=_crashing_output,
            interval_sec=0.01,
        )
        worker.start_queue_worker(queue)

        # Simulate engine pushing events
        engine_exceptions: list[Exception] = []
        def _simulate_engine():
            for i in range(20):
                try:
                    queue.try_push(_make_env("INFO", tick=i))
                except Exception as e:
                    engine_exceptions.append(e)
                time.sleep(0.01)

        engine_thread = threading.Thread(target=_simulate_engine)
        engine_thread.start()
        engine_thread.join(timeout=2.0)

        worker.stop_queue_worker(timeout_sec=1.0)

        # Engine thread must not have seen any exceptions
        assert engine_exceptions == [], (
            f"Engine thread received exceptions: {engine_exceptions}"
        )
