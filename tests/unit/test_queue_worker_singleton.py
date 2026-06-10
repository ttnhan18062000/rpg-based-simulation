"""
Unit tests for the global QueueDrainWorker singleton guard.

Verifies:
- get_or_start_global_worker() returns the same worker on repeated calls.
- A second call does not start a second thread.
- A dead worker is replaced on the next call.
- get_active_global_worker_count() returns 0 / 1 correctly.
"""
from __future__ import annotations

import time
import pytest
import src.observability.queue as queue_module
from src.observability.queue import (
    BoundedObservabilityQueue,
    get_or_start_global_worker,
    get_active_global_worker_count,
)


@pytest.fixture(autouse=True)
def reset_global_worker():
    """Reset module-level _global_worker before and after each test."""
    original = queue_module._global_worker
    queue_module._global_worker = None
    yield
    # Stop any worker started by the test
    w = queue_module._global_worker
    if w is not None and w.is_alive():
        w.stop()
    queue_module._global_worker = original


def _fresh_queue() -> BoundedObservabilityQueue:
    return BoundedObservabilityQueue(max_size=100)


class TestGetOrStartGlobalWorker:

    def test_global_worker_singleton(self):
        """Two calls return the same worker; only one thread is active."""
        queue = _fresh_queue()

        w1 = get_or_start_global_worker(queue)
        w2 = get_or_start_global_worker(queue)

        assert w1 is w2, "Expected the same worker object on both calls"
        assert get_active_global_worker_count() == 1, (
            f"Expected 1 active worker, got {get_active_global_worker_count()}"
        )

    def test_global_worker_reused_on_second_start(self):
        """Calling get_or_start_global_worker() twice returns the identical object."""
        queue = _fresh_queue()

        first = get_or_start_global_worker(queue)
        second = get_or_start_global_worker(queue)

        assert first is second

    def test_global_worker_restarted_when_dead(self):
        """A stopped (dead) worker is replaced by a fresh one."""
        queue = _fresh_queue()

        first = get_or_start_global_worker(queue)
        first.stop()

        # Brief pause so the thread reaches DEAD state
        time.sleep(0.05)

        assert not first.is_alive(), "Worker should be dead after stop()"

        second = get_or_start_global_worker(queue)

        assert second is not first, "Expected a new worker after the old one died"
        assert second.is_alive(), "New worker must be alive"
        assert get_active_global_worker_count() == 1


class TestGetActiveGlobalWorkerCount:

    def test_zero_when_no_worker(self):
        """Count must be 0 when _global_worker is None."""
        assert queue_module._global_worker is None
        assert get_active_global_worker_count() == 0

    def test_one_when_worker_alive(self):
        """Count must be 1 when a worker is running."""
        queue = _fresh_queue()
        get_or_start_global_worker(queue)

        assert get_active_global_worker_count() == 1
