"""
memory_probe — lightweight importable helpers for before/after memory and resource assertions.

Does NOT import memray. Safe to use inside pytest tests without the [dev] optional dependency.
"""
from __future__ import annotations

import gc
import os
import threading
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MemorySnapshot:
    rss_bytes: int
    tracemalloc_snapshot: Optional[object]  # tracemalloc.Snapshot or None
    worker_thread_count: int
    event_recorder_count: int
    timestamp: float = field(default_factory=time.monotonic)


@dataclass
class MemoryReport:
    rss_delta_bytes: int
    top_allocations: List[str]
    worker_count_delta: int
    event_recorder_delta: int


def count_drain_workers() -> int:
    """Count active QueueDrainWorker background threads by name."""
    return sum(
        1 for t in threading.enumerate()
        if t.name == "observability-drain-worker"
    )


def count_event_recorders() -> int:
    """Count live EventRecorder instances via gc."""
    from src.observability.event_recorder import EventRecorder
    return sum(1 for o in gc.get_objects() if isinstance(o, EventRecorder))


def _get_rss() -> int:
    """Return current process RSS in bytes via psutil."""
    import psutil
    return psutil.Process(os.getpid()).memory_info().rss


def snapshot_start() -> MemorySnapshot:
    """
    Capture a baseline memory snapshot.

    Starts tracemalloc if it is not already running.
    Call snapshot_end() after the workload to compute deltas.
    """
    if not tracemalloc.is_tracing():
        tracemalloc.start()

    return MemorySnapshot(
        rss_bytes=_get_rss(),
        tracemalloc_snapshot=None,  # baseline: no snapshot needed before workload
        worker_thread_count=count_drain_workers(),
        event_recorder_count=count_event_recorders(),
    )


def snapshot_end(start: MemorySnapshot, top_n: int = 20) -> MemoryReport:
    """
    Compute deltas relative to the given baseline snapshot.

    Stops tracemalloc after capturing the end snapshot.
    Returns a MemoryReport with RSS delta, top allocation sites, and resource counts.
    """
    end_rss = _get_rss()

    top_allocs: List[str] = []
    if tracemalloc.is_tracing():
        snap = tracemalloc.take_snapshot()
        tracemalloc.stop()
        stats = snap.statistics("lineno")
        for stat in stats[:top_n]:
            top_allocs.append(str(stat))
    else:
        top_allocs = ["(tracemalloc not active — no allocation data)"]

    return MemoryReport(
        rss_delta_bytes=end_rss - start.rss_bytes,
        top_allocations=top_allocs,
        worker_count_delta=count_drain_workers() - start.worker_thread_count,
        event_recorder_delta=count_event_recorders() - start.event_recorder_count,
    )


def assert_no_worker_leak(before: int, after: int) -> None:
    """
    Assert that no QueueDrainWorker threads were leaked.

    Raises AssertionError with a clear message if after > before.
    """
    if after > before:
        raise AssertionError(
            f"QueueDrainWorker thread leak detected: "
            f"before={before}, after={after} "
            f"(delta=+{after - before}). "
            f"Call shutdown() on all EventRecorder / Kernel instances."
        )
