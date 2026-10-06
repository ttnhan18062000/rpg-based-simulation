"""Mutation probe (not collected by pytest): K extra perf_counter_ns calls per tick.

Run: python -m pytest tests/integration/kernel/probe_mb_extra_clock_calls.py -q -s -p no:cacheprovider
Reports, per K, the mode sequence of the DEGRADED leg, the last compute figure the
governor saw, the dropped-work delta (budget watchdog effect) and the new test's verdict.
"""
import logging
import time
from unittest.mock import MagicMock, patch

import pytest

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.governance import RuntimeMode
from src.core.state import AuthoritativeState
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.integration.kernel.test_milestone_b_closure import TickKeyedClock, _tick_with_clock


def _profile():
    return RuntimeProfile(
        name="mb_probe", hardware_class=HardwareClass.CLASS_A, max_ram_mb=1000,
        max_cpu_percent=100.0, max_worker_count=4, max_queue_depth=10, max_work_debt=100,
        max_replay_buffer_kb=1000, max_tick_budget_ms=100.0,
        max_observability_budget_percent=5.0, sampling_interval_ticks=1,
        dwell_time_ticks=5, confidence_window_ticks=3, recovery_watermark=0.8,
    )


@pytest.mark.parametrize("k", [0, 12, 50])
def test_probe(k, capsys):
    kernel = Kernel(_profile(), AuthoritativeState(tick=0, seed=1), DeterministicRNG(1))
    try:
        kernel._collector._process.memory_info = MagicMock(return_value=MagicMock(rss=100 * 1024 * 1024))
        original = Kernel._phase_persistence

        def noisy_phase(self):
            for _ in range(k):
                time.perf_counter_ns()
            original(self)

        patcher = patch.object(Kernel, "_phase_persistence", noisy_phase)
        patcher.start()
        for _ in range(5):
            kernel.tick_once()
        clock = TickKeyedClock(compute_ms=120.0)
        modes, dropped = [], []
        with patch("time.perf_counter_ns", side_effect=clock):
            for _ in range(10):
                _tick_with_clock(kernel, clock)
                modes.append(kernel.status.current_mode.name)
                dropped.append(kernel.status.dropped_work_delta)
                if kernel.status.current_mode == RuntimeMode.DEGRADED:
                    break
        last = kernel.status.signal_history[-1]
        print(f"PROBE K={k} modes={modes} compute_ms={last.tick_compute_ms} "
              f"phase_cost_sum={sum(last.phase_costs_ms.values()):.1f} dropped={dropped}")
        assert kernel.status.current_mode == RuntimeMode.DEGRADED
    finally:
        patch.stopall()
        kernel.shutdown()
