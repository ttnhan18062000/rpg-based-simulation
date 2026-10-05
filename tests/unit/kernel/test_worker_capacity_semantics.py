"""
Specification tests for zero-capacity worker and queue signals.

Written from PERF-D1 ("Zero-capacity semantics", docs/architecture/performance_optimization_decisions.md,
conflict C-03), not from the previous output of ``WorkerManager.get_stats()``:

- zero workers means synchronous execution; utilization does not apply and reports 0.0;
- zero queue depth with zero workers means no queue exists; queue utilization reports 0.0;
- zero queue depth with one or more workers is a configuration error rejected at construction;
- idle is 0.0, saturated is 1.0, and "unavailable" is never encoded as a utilization value.

TCK-20261005-PERF-M1-ZERO-CAPACITY-SIGNAL.
"""
import time
from unittest.mock import MagicMock

import pytest

from src.core.work import WorkClass
from src.core.worker_protocol import WorkerPacket, WorkerResult
from src.engine.worker_manager import WorkerManager


def _packets(count: int) -> list[WorkerPacket]:
    return [
        WorkerPacket(
            packet_id=f"cap:{i}",
            work_id=f"w:{i}",
            tick=0,
            world_time=0,
            seed=i,
            work_class=WorkClass.CRITICAL,
            subject=MagicMock(id=i),
            neighbor_view=[],
            work_kind="ACT",
            payload={},
        )
        for i in range(count)
    ]


def _ok(packet: WorkerPacket) -> WorkerResult:
    return WorkerResult(
        source_packet_id=packet.packet_id,
        work_id=packet.work_id,
        entity_id=packet.subject.id,
        work_class=packet.work_class,
        update=MagicMock(),
    )


def _set_peaks(manager: WorkerManager, *, active: int, queued: int) -> None:
    with manager._stats_lock:
        manager._peak_active = active
        manager._peak_queued = queued


# --- configured-zero -------------------------------------------------------


@pytest.mark.parametrize("workers", [1, 4])
@pytest.mark.parametrize("queue_depth", [0, -1])
def test_queue_without_capacity_is_rejected_when_workers_exist(workers, queue_depth):
    """PERF-D1: zero queue depth with one or more workers is a configuration error at construction."""
    with pytest.raises(ValueError) as excinfo:
        WorkerManager(max_workers=workers, max_queue_depth=queue_depth)
    message = str(excinfo.value)
    assert str(workers) in message
    assert str(queue_depth) in message


@pytest.mark.parametrize("workers,queue_depth", [(-1, 100), (-1, 0), (0, -1)])
def test_negative_capacity_is_rejected(workers, queue_depth):
    """PERF-D1: negative capacities are not a disabled signal; they are rejected, never clamped."""
    with pytest.raises(ValueError):
        WorkerManager(max_workers=workers, max_queue_depth=queue_depth)


def test_zero_workers_and_zero_queue_means_no_queue_exists():
    """PERF-D1: zero workers with zero queue depth constructs, and reports 0.0 for both utilizations."""
    manager = WorkerManager(max_workers=0, max_queue_depth=0)
    stats = manager.get_stats()
    assert stats["worker_utilization"] == 0.0
    assert stats["queue_utilization"] == 0.0
    manager.shutdown()


# --- disabled (synchronous) ------------------------------------------------


def test_zero_workers_runs_synchronously_and_reports_idle():
    """PERF-D1: zero workers is synchronous execution; utilization does not apply (0.0)."""
    manager = WorkerManager(max_workers=0, max_queue_depth=100)
    results = manager.execute_batch(_packets(10), _ok)
    assert len(results) == 10
    stats = manager.get_stats()
    assert stats["worker_utilization"] == 0.0
    assert stats["queue_utilization"] == 0.0
    manager.shutdown()


# --- idle / busy / saturated -----------------------------------------------


def test_idle_manager_reports_zero():
    """PERF-D1: idle is 0.0."""
    manager = WorkerManager(max_workers=4, max_queue_depth=100)
    stats = manager.get_stats()
    assert stats["worker_utilization"] == 0.0
    assert stats["queue_utilization"] == 0.0
    manager.shutdown()


def test_busy_manager_reports_between_zero_and_one():
    """PERF-D1: a partially used manager reports peak usage over its limit, strictly between 0.0 and 1.0."""
    manager = WorkerManager(max_workers=4, max_queue_depth=100)
    _set_peaks(manager, active=2, queued=50)
    stats = manager.get_stats()
    assert stats["worker_utilization"] == 0.5
    assert stats["queue_utilization"] == 0.5
    manager.shutdown()


def test_saturated_manager_reports_one():
    """PERF-D1: saturated is 1.0."""
    manager = WorkerManager(max_workers=4, max_queue_depth=100)
    _set_peaks(manager, active=4, queued=100)
    stats = manager.get_stats()
    assert stats["worker_utilization"] == 1.0
    assert stats["queue_utilization"] == 1.0
    manager.shutdown()


# --- local (queue at its limit forces local execution) ---------------------


def test_queue_at_limit_forces_local_execution_without_losing_work():
    """PERF-D1: a full queue falls back to synchronous execution; no work is dropped."""

    def slow(packet: WorkerPacket) -> WorkerResult:
        time.sleep(0.05)
        return _ok(packet)

    manager = WorkerManager(max_workers=1, max_queue_depth=1)
    results = manager.execute_batch(_packets(200), slow)
    assert len(results) == 200
    assert 0.0 <= manager.get_stats()["queue_utilization"] <= 1.0
    manager.shutdown()


def test_local_fallback_never_reports_more_than_saturated():
    """PERF-D1: saturated is 1.0, so no utilization value exceeds it."""

    def slow(packet: WorkerPacket) -> WorkerResult:
        time.sleep(0.05)
        return _ok(packet)

    manager = WorkerManager(max_workers=1, max_queue_depth=1)
    manager.execute_batch(_packets(200), slow)
    stats = manager.get_stats()
    assert stats["peak_workers"] == 1
    assert stats["worker_utilization"] == 1.0
    manager.shutdown()


# --- unavailable -----------------------------------------------------------


def test_unavailable_is_not_encoded_as_a_utilization_value():
    """
    PERF-D1: "unavailable" is never a utilization value. No unavailable state exists today: after
    shutdown the manager still reports numeric stats and executes locally, and does not report
    saturation; local execution is not pool capacity, so both utilizations are 0.0.
    """
    manager = WorkerManager(max_workers=4, max_queue_depth=100)
    manager.shutdown()
    results = manager.execute_batch(_packets(5), _ok)
    assert len(results) == 5
    stats = manager.get_stats()
    assert stats["worker_utilization"] == 0.0
    assert stats["queue_utilization"] == 0.0
