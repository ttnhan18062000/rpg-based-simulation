"""The CANONICAL signal contract: the governors' cost inputs are modelled from deterministic demand, never read from a clock or the host.

TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY, Phase A step 3 (PERF-D1). The first test is the hash-equality run PR #379 had to
remove: with ``audit_mode`` off, the same seed must give the same mode, the same phase budgets and the same state hash every time, whatever the
host's speed. Runs 6 to 10 patch ``time.perf_counter_ns`` with a jittering clock (some runs 50x slower, some 50x faster).
"""
from __future__ import annotations

import ast
import random
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.governance import PressureSignals, RuntimeMode
from src.engine import signal_source, work_units
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.engine.phase_governor import PhaseBudgetGovernor, PhaseBudgets
from src.engine.runtime_status import RuntimeStatus
from src.engine.signal_source import HostReadings, MeasuredCosts
from src.perf.scenarios import build_movement_state, build_strategic_state
from src.platform.rng import DeterministicRNG


def _profile(contract: str = "canonical", budget: float = 60.0, workers: int = 0, **extra) -> RuntimeProfile:
    return RuntimeProfile(
        name="canonical_contract", hardware_class=HardwareClass.CLASS_B, max_ram_mb=4096, max_cpu_percent=90.0,
        max_worker_count=workers, max_queue_depth=100, max_replay_buffer_kb=1024, max_observability_budget_percent=10.0,
        max_tick_budget_ms=budget, dwell_time_ticks=2, confidence_window_ticks=2, signal_contract=contract, **extra,
    )


class JitterClock:
    """``time.perf_counter_ns`` replacement whose step is drawn per read from a seeded generator, scaled to be much slower or faster."""

    def __init__(self, seed: int, scale: float) -> None:
        self._rng = random.Random(seed)
        self._scale = scale
        self._now = 0

    def __call__(self) -> int:
        self._now += int(self._rng.randint(1_000, 200_000) * self._scale)
        return self._now


def _run(monkeypatch, run: int, ticks: int = 8):
    """One Canonical, non-audit run; returns the per-tick (mode, phase budgets, state hash) sequence."""
    if run >= 5:
        monkeypatch.setattr(time, "perf_counter_ns", JitterClock(seed=run, scale=50.0 if run % 2 else 0.02))
    # Modelled cost is 20.4 + 7.42 * 30 = 243 reference-ms: just over this budget (DEGRADED), well under 1.5x (SURVIVAL), so a clock leak of
    # even a fraction of the cost would change the mode or the budgets.
    kernel = Kernel(_profile(budget=240.0), build_strategic_state(entity_count=30), DeterministicRNG(7),
                    flags={"no_frame_pacing": True, "no_replay": True})
    kernel._collector._process.memory_info = MagicMock(return_value=MagicMock(rss=(run + 1) * 100 * 1024 * 1024))
    sequence = []
    try:
        for _ in range(ticks):
            kernel.tick_once()
            sequence.append((kernel._status.current_mode.name, kernel._current_policy.phase_budgets,
                             CanonicalStateHasher.get_hash(kernel._state)))
    finally:
        kernel.shutdown()
        monkeypatch.undo()
    return sequence


def test_canonical_runs_are_hash_and_mode_identical(monkeypatch):
    runs = [_run(monkeypatch, run) for run in range(10)]
    assert all(sequence == runs[0] for sequence in runs[1:]), "a Canonical run changed with the clock or the host"
    modes = {mode for mode, _, _ in runs[0]}
    assert modes != {"NORMAL"}, "the run never left NORMAL, so the governor was not exercised"
    assert any(budgets != PhaseBudgets() for _, budgets, _ in runs[0]), "no tick changed the phase budgets"


def test_canonical_signals_and_decisions_ignore_the_clock_and_the_host(monkeypatch):
    state = build_strategic_state(entity_count=30)
    profile = _profile(budget=240.0, workers=2)
    source = signal_source.select_signal_source(profile, audit_mode=False)
    results = []
    for clock_scale, rss_mb, backlog_kb, measured_ms in ((0.0, 10.0, 0, 1.0), (1.0, 500.0, 10, 50.0), (1000.0, 1.0e6, 10**9, 1.0e6)):
        monkeypatch.setattr(time, "perf_counter_ns", JitterClock(seed=3, scale=clock_scale))
        status = RuntimeStatus()
        host = HostReadings({"worker_utilization": 1.0, "queue_utilization": 1.0, "active_workers": 99},
                            {"backlog_kb": backlog_kb}, {"rss_mb": rss_mb}, {})
        start = source.tick_start_signals(state=state, profile=profile, status=status, host=host)
        end = source.tick_end_signals(state=state, profile=profile, status=status,
                                      measured=MeasuredCosts(measured_ms, {"locomotion": measured_ms}), host=host)
        status.record_signals(end)
        policy = ResourceGovernor().evaluate(profile, start, status, current_tick=3)
        results.append((start.tick_cost, start.phase_cost, start.worker_utilization, start.queue_utilization,
                        start.memory_estimate_mb, start.replay_backlog_kb, end.tick_cost, policy.mode, policy.phase_budgets))
    assert results[0] == results[1] == results[2]
    assert results[0][7] is not RuntimeMode.NORMAL, "the modelled cost never crossed a threshold, so equality proves little"


def test_canonical_tick_cost_is_the_work_model_applied_to_the_state():
    state = build_strategic_state(entity_count=25)
    demand = work_units.count_demand(state)
    profile = _profile()
    start = signal_source.select_signal_source(profile, False).tick_start_signals(
        state=state, profile=profile, status=RuntimeStatus(), host=HostReadings({}, {}, {}, {}))
    assert start.tick_cost == pytest.approx(work_units.tick_cost_ref_ms(demand))
    assert start.tick_compute_ms == 0.0 and start.phase_cost == {}


def test_canonical_modules_import_no_clock_or_host_module():
    forbidden = {"time", "psutil", "os", "threading", "datetime", "random"}
    for module in (work_units, signal_source):
        source = Path(module.__file__).read_text()
        tree = ast.parse(source)
        imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        imported |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        assert not imported & forbidden, f"{module.__name__} imports {imported & forbidden}"
        assert "perf_counter" not in source and "psutil" not in source, f"{module.__name__} reads a clock"


class _Pinned(ResourceGovernor):
    def __init__(self, mode: RuntimeMode) -> None:
        super().__init__()
        self._pinned = mode

    def _get_indicated_mode(self, profile, signals):
        return self._pinned


def test_cost_is_demand_not_work_done():
    """The governor is pinned to NORMAL and then to SURVIVAL on the same state; the modelled inputs for the next tick must not move."""
    seen = {}
    for mode in (RuntimeMode.NORMAL, RuntimeMode.SURVIVAL):
        kernel = Kernel(_profile(workers=2), build_movement_state(entity_count=60), DeterministicRNG(7),
                        governor=_Pinned(mode), flags={"no_frame_pacing": True, "no_replay": True})
        try:
            kernel.tick_once()
            recorded = kernel._status.signal_history[-1]
            seen[mode] = (kernel._current_signals.tick_cost, recorded.tick_cost, recorded.worker_utilization, recorded.queue_utilization)
        finally:
            kernel.shutdown()
    assert seen[RuntimeMode.NORMAL] == seen[RuntimeMode.SURVIVAL]


def test_modelled_cost_is_identical_across_executors():
    costs = {}
    for workers in (0, 2):
        kernel = Kernel(_profile(workers=workers), build_movement_state(entity_count=60), DeterministicRNG(7),
                        flags={"no_frame_pacing": True, "no_replay": True})
        try:
            for _ in range(4):
                kernel.tick_once()
            costs[workers] = [(s.tick_cost, s.phase_cost) for s in kernel._status.signal_history]
        finally:
            kernel.shutdown()
    assert costs[0] == costs[2]


def test_audit_mode_still_zeroes_the_signals_under_the_canonical_contract():
    kernel = Kernel(_profile(), build_strategic_state(entity_count=20), DeterministicRNG(7),
                    flags={"audit_mode": True, "no_frame_pacing": True, "no_replay": True})
    try:
        kernel.tick_once()
        assert kernel._current_signals == PressureSignals(metrics=kernel._current_signals.metrics)
        assert kernel._status.current_mode is RuntimeMode.NORMAL
    finally:
        kernel.shutdown()
