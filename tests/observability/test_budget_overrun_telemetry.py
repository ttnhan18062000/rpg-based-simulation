"""The tick-budget overrun signal is surfaced wherever dropped work is (TCK-20261006-PERF-BUDGET-OVERRUN-TELEMETRY-SURFACING).

The kernel records an overrun on RuntimeStatus (report only). Here a real engine manager shows it in its metrics snapshot, the live snapshot, the
Prometheus gauge and counter and the engine's own RuntimeSnapshot, and nothing that decides reads it.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from prometheus_client import generate_latest
from prometheus_client.parser import text_string_to_metric_families

from src.api.engine_manager import V2EngineManager
from src.config.profiles import HardwareClass, RuntimeProfile
from src.observability.live.snapshot_provider import LiveSnapshotProvider


@pytest.fixture(scope="module")
def manager():
    profile = RuntimeProfile(
        name="overrun_telemetry", hardware_class=HardwareClass.CLASS_B, max_ram_mb=512, max_cpu_percent=80.0, max_worker_count=0,
        max_queue_depth=10, max_tick_budget_ms=50, max_replay_buffer_kb=1024, max_observability_budget_percent=5.0,
    )
    m = V2EngineManager(profile, seed=42)
    try:
        yield m
    finally:
        m.stop()


def _samples(m) -> dict:
    text = generate_latest(m.metrics_registry).decode("utf-8")
    return {f.name: f.samples[0].value for f in text_string_to_metric_families(text) if f.name in ("sim_budget_overrun_ms", "sim_budget_overruns")}


class _RunningView:
    """The live provider reports IDLE for a manager that is not running; this view is the real manager's metrics and kernel on a running flag."""
    is_running, is_paused, is_stopped, is_stopping, errors_total = True, False, False, False, 0

    def __init__(self, m):
        self._m = m
        self.tick, self.started_at, self.kernel = m.tick, m.started_at if hasattr(m, "started_at") else 0.0, m._kernel

    def get_metrics_snapshot(self):
        return self._m.get_metrics_snapshot()

    def __getattr__(self, name):
        return getattr(self._m, name)


def _live(m) -> dict:
    return LiveSnapshotProvider.get_snapshot(_RunningView(m)).latest_runtime_status


def _refresh(m) -> None:
    m._update_latest_state(m._kernel.state)


def test_no_overrun_shows_zero_and_minus_one_on_every_surface(manager):
    _refresh(manager)
    snap = manager.get_metrics_snapshot()
    assert (snap["budget_overrun_ms"], snap["budget_overrun_tick"], snap["total_budget_overruns"]) == (0.0, -1, 0)
    live = _live(manager)
    assert (live["budget_overrun_ms"], live["budget_overrun_tick"], live["total_budget_overruns"]) == (0.0, -1, 0)
    assert _samples(manager) == {"sim_budget_overrun_ms": 0.0, "sim_budget_overruns": 0.0}
    assert manager._kernel._collector.get_snapshot(manager._kernel).total_budget_overruns == 0


def test_a_recorded_overrun_shows_on_every_surface_next_to_dropped_work(manager):
    manager._kernel.status.record_budget_overrun(7.5, 3)
    manager._kernel.status.record_budget_overrun(2.0, 4)
    _refresh(manager)
    snap = manager.get_metrics_snapshot()
    assert (snap["budget_overrun_ms"], snap["budget_overrun_tick"], snap["total_budget_overruns"]) == (2.0, 4, 2)
    assert snap["dropped_work_delta"] == 0
    live = _live(manager)
    assert (live["budget_overrun_ms"], live["budget_overrun_tick"], live["total_budget_overruns"]) == (2.0, 4, 2)
    assert "dropped_work_delta" in live
    assert _samples(manager) == {"sim_budget_overrun_ms": 2.0, "sim_budget_overruns": 2.0}
    runtime = manager._kernel._collector.get_snapshot(manager._kernel)
    assert (runtime.budget_overrun_ms, runtime.budget_overrun_tick, runtime.total_budget_overruns) == (2.0, 4, 2)


def test_only_the_recorder_and_the_four_surfaces_read_the_overrun_fields():
    """Telemetry only (PERF-D1 amendment A1): no governor, scheduler, state or game-system code reads these names."""
    allowed = {"src/engine/runtime_status.py", "src/engine/kernel.py", "src/engine/observability.py", "src/api/engine_manager.py",
               "src/observability/live/snapshot_provider.py", "src/observability/prometheus_collector.py"}
    names = ("budget_overrun_ms", "budget_overrun_tick", "total_budget_overruns")
    readers = {p.as_posix() for p in Path("src").rglob("*.py") if any(n in p.read_text(encoding="utf-8") for n in names)}
    assert readers <= allowed, sorted(readers - allowed)
