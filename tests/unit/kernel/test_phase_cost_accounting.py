"""The kernel's per-phase costs add up to the tick, with no sub-phase counted twice.

TCK-20261008-PERF-KERNEL-RESOLUTION-OVERHEAD-DOUBLE-COUNTS-SUB-PHASES. ``_final_compute_ms`` is ``sum(_phase_costs.values())`` and it becomes
``tick_compute_ms``, the governor's cost input (PERF-D1). ``resolution_overhead`` used to subtract a hand-kept whitelist of sub-phase keys, so
any refine sub-phase left off the list (``combat_engagement``, ``cooperation``, the ``faction_*`` phases) was counted under its own key and
again inside ``resolution_overhead``.

The clock is a call counter that moves one millisecond per read, never real time, so every interval is an exact integer.
"""
from __future__ import annotations

import time

import pytest

from src.config.profiles import HardwareClass, RuntimeProfile
from src.engine.kernel import Kernel
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.perf.scenarios import build_movement_state
from src.platform.rng import DeterministicRNG

STEP_MS = 1.0
TICK_LEVEL_KEYS = ("init", "scheduling", "collection", "cleanup", "advancement", "persistence")


class CountingClock:
    """Fake ``time.perf_counter_ns``: every read returns the previous value plus one step."""

    def __init__(self) -> None:
        self.now_ns = 0

    def __call__(self) -> int:
        self.now_ns += int(STEP_MS * 1_000_000)
        return self.now_ns


@pytest.fixture
def kernel():
    profile = RuntimeProfile(
        name="phase_cost_accounting", hardware_class=HardwareClass.CLASS_B, max_ram_mb=4096, max_cpu_percent=90.0,
        max_worker_count=0, max_queue_depth=100, max_replay_buffer_kb=1024, max_observability_budget_percent=10.0,
        max_tick_budget_ms=100000.0,
    )
    k = Kernel(profile, build_movement_state(entity_count=40), DeterministicRNG(7),
               flags={"no_frame_pacing": True, "no_replay": True})
    try:
        yield k
    finally:
        k.shutdown()


def _tick_and_measure(kernel, monkeypatch):
    """Run one tick on the counting clock; return (resolution wall ms, sub-phase costs the pipeline recorded)."""
    clock = CountingClock()
    monkeypatch.setattr(time, "perf_counter_ns", clock)
    seen = {}
    real_resolution = Kernel._phase_resolution

    def timed_resolution(self):
        start = clock()
        real_resolution(self)
        end = clock()
        # The kernel's own reads sit one step outside these two: t3 just before ``start``, t4 just after ``end``.
        seen["resolution_ms"] = (end - start) / 1e6 + 2 * STEP_MS
        seen["sub_phase_costs"] = dict(self._current_update.sub_phase_costs)

    monkeypatch.setattr(Kernel, "_phase_resolution", timed_resolution)
    kernel.tick_once()
    return seen["resolution_ms"], seen["sub_phase_costs"]


def test_phase_costs_sum_to_the_tick_without_double_counting(kernel, monkeypatch):
    kernel.tick_once()  # a first tick fills _phase_costs, so a stale or repeated key would show in the second
    resolution_ms, _ = _tick_and_measure(kernel, monkeypatch)
    costs = kernel._phase_costs
    expected = sum(costs[key] for key in TICK_LEVEL_KEYS) + resolution_ms
    assert sum(costs.values()) == pytest.approx(expected, abs=1e-6)
    assert kernel._final_compute_ms == pytest.approx(expected, abs=1e-6)


def test_resolution_time_is_overhead_plus_each_sub_phase_once(kernel, monkeypatch):
    kernel.tick_once()
    resolution_ms, sub_phase_costs = _tick_and_measure(kernel, monkeypatch)
    costs = kernel._phase_costs
    assert sub_phase_costs, "the refine pipeline recorded no sub-phase costs, so this test would prove nothing"
    assert "combat_engagement" in sub_phase_costs, "a sub-phase the old whitelist left out must be among those checked"
    in_resolution = costs["resolution_overhead"] + sum(costs[key] for key in sub_phase_costs)
    assert in_resolution == pytest.approx(resolution_ms, abs=1e-6)


def test_a_sub_phase_the_pipeline_skips_this_tick_keeps_no_stale_cost(kernel, monkeypatch):
    kernel.tick_once()
    assert "cooperation" in kernel._phase_costs, "tick 1 must record the key this test then drops"

    real_refine = AuthoritativeApplyPipeline.refine

    def refine_without_cooperation(*args, **kwargs):
        refined = real_refine(*args, **kwargs)
        return refined.replace(sub_phase_costs={k: v for k, v in refined.sub_phase_costs.items() if k != "cooperation"})

    monkeypatch.setattr(AuthoritativeApplyPipeline, "refine", staticmethod(refine_without_cooperation))
    resolution_ms, _ = _tick_and_measure(kernel, monkeypatch)
    costs = kernel._phase_costs
    assert "cooperation" not in costs
    assert sum(costs.values()) == pytest.approx(sum(costs[key] for key in TICK_LEVEL_KEYS) + resolution_ms, abs=1e-6)
