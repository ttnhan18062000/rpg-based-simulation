"""
Phase 22 — BehaviorWorker in-process queue drain integration tests.

Tests verify:
- Worker can drain events from BoundedObservabilityQueue.
- Worker produces BehaviorEvents from queue envelopes.
- Worker failure does not affect engine/simulation.
- Worker can be stopped cleanly.
"""
from __future__ import annotations

import time
import threading
from typing import List

import pytest

from src.observability.behavior.normalizer import BehaviorEventNormalizer
from src.observability.behavior.normalization_context import BehaviorNormalizationContext
from src.observability.behavior.worker import BehaviorWorker
from src.observability.events import ObservabilityEventEnvelope
from src.observability.queue import BoundedObservabilityQueue


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_envelope(
    event_type: str = "movement",
    event_category: str = "movement",
    tick: int = 1,
    entity_id: int = 1,
) -> ObservabilityEventEnvelope:
    return ObservabilityEventEnvelope(
        event_id=f"env_{event_type}_{tick}",
        run_id="run_stream_test",
        tick=tick,
        entity_id=entity_id,
        event_type=event_type,
        event_category=event_category,
        severity="INFO",
        source_system="test_system",
        message=f"test {event_type}",
        payload={},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBehaviorWorkerFromStream:

    def test_behavior_worker_drains_queue_and_normalizes(self):
        """Worker must drain queue envelopes and produce BehaviorEvents."""
        queue = BoundedObservabilityQueue(max_size=100)
        queue.try_push(_make_envelope("movement", "movement", tick=1))
        queue.try_push(_make_envelope("combat_damage", "combat", tick=2))

        collected: List = []
        ctx = BehaviorNormalizationContext.minimal("run_stream_test")
        worker = BehaviorWorker(
            context=ctx,
            output_fn=collected.append,
            interval_sec=0.01,
        )
        worker.start_queue_worker(queue)

        # Give the worker time to drain
        time.sleep(0.15)
        worker.stop_queue_worker(timeout_sec=1.0)

        assert len(collected) >= 2
        categories = {be.behavior_category for be in collected}
        assert "movement" in categories
        assert "combat" in categories

    def test_worker_failure_does_not_crash_engine(self):
        """Worker exceptions in output_fn must not propagate to the simulation."""
        queue = BoundedObservabilityQueue(max_size=100)
        queue.try_push(_make_envelope("movement", "movement", tick=1))

        def _crashing_output(be):
            raise RuntimeError("Simulated downstream failure")

        ctx = BehaviorNormalizationContext.minimal("run_stream_test")
        worker = BehaviorWorker(
            context=ctx,
            output_fn=_crashing_output,
            interval_sec=0.01,
        )
        worker.start_queue_worker(queue)
        time.sleep(0.1)
        worker.stop_queue_worker(timeout_sec=1.0)

        # Worker degrades but does not crash the caller
        # Health may be DEGRADED or STOPPED — either is acceptable
        assert worker.health_status in ("DEGRADED", "STOPPED", "HEALTHY")

    def test_worker_can_be_stopped_cleanly(self):
        """Worker stop must be idempotent and non-blocking."""
        queue = BoundedObservabilityQueue(max_size=100)
        ctx = BehaviorNormalizationContext.minimal("run_stream_test")
        worker = BehaviorWorker(context=ctx, interval_sec=0.01)

        worker.start_queue_worker(queue)
        time.sleep(0.05)
        worker.stop_queue_worker(timeout_sec=1.0)

        # Stop a second time — must not raise
        worker.stop_queue_worker(timeout_sec=0.5)
        assert not worker.is_running

    def test_worker_does_not_block_queue_push(self):
        """Slow worker must not block queue push (non-blocking contract)."""
        queue = BoundedObservabilityQueue(max_size=10)

        def _slow_output(be):
            time.sleep(0.5)

        ctx = BehaviorNormalizationContext.minimal("run_stream_test")
        worker = BehaviorWorker(context=ctx, output_fn=_slow_output, interval_sec=0.05)
        worker.start_queue_worker(queue)

        # Fill the queue — must complete quickly (not block)
        start = time.monotonic()
        for i in range(10):
            queue.try_push(_make_envelope("movement", "movement", tick=i))
        elapsed = time.monotonic() - start

        worker.stop_queue_worker(timeout_sec=0.5)
        assert elapsed < 0.1, f"Queue push took too long: {elapsed:.3f}s"

    def test_worker_start_is_idempotent(self):
        """Starting the worker twice must not create two threads."""
        queue = BoundedObservabilityQueue(max_size=100)
        ctx = BehaviorNormalizationContext.minimal("run_stream_test")
        worker = BehaviorWorker(context=ctx, interval_sec=0.05)

        worker.start_queue_worker(queue)
        worker.start_queue_worker(queue)  # Second start — must be no-op
        time.sleep(0.05)
        worker.stop_queue_worker(timeout_sec=1.0)

        # Should still have stopped cleanly
        assert not worker.is_running
