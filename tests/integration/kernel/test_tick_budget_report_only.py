"""The kernel's wall-clock tick-budget checks report overruns; they never change outcomes
(TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY, PERF-D1 inputs 2 and 3).

Before this ticket, with `audit_mode` off, the mid-tick throttle dropped the remaining results once the
tick ran past `max_tick_budget_ms`, forced the governor to DEGRADED, and the end-of-tick check recorded a
`9999` sentinel as dropped work. What a run computed then depended on how fast the host was.

These runs use the smallest budget the profile validator accepts (1 ms) so the overrun is certain, and a
governor that never leaves NORMAL, so the only thing that could drop work or change the mode is the
throttle itself. They assert counters and calls, never timings.
"""
from __future__ import annotations

from typing import List

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.governance import RuntimeMode
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.perf.scenarios import build_movement_state
from src.platform.rng import DeterministicRNG

TICKS = 8
ENTITIES = 120
FLAGS = {"no_frame_pacing": True, "no_replay": True}  # audit_mode off: the real, wall-clock-driven path


def _tight_profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="tight_budget", hardware_class=HardwareClass.CLASS_B, max_ram_mb=512, max_cpu_percent=80.0,
        max_worker_count=0, max_queue_depth=500, max_replay_buffer_kb=4096, max_observability_budget_percent=10.0,
        max_tick_budget_ms=1.0,
    )


class _NormalOnlyGovernor(ResourceGovernor):
    """Keeps the indicated mode at NORMAL and records every `force_mode` call."""

    def __init__(self) -> None:
        super().__init__()
        self.forced: List[RuntimeMode] = []

    def _get_indicated_mode(self, profile, signals):
        return RuntimeMode.NORMAL

    def force_mode(self, mode, status, current_tick) -> None:
        self.forced.append(mode)
        super().force_mode(mode, status, current_tick)


def _run() -> tuple[Kernel, _NormalOnlyGovernor]:
    governor = _NormalOnlyGovernor()
    kernel = Kernel(
        _tight_profile(), build_movement_state(entity_count=ENTITIES), DeterministicRNG(7),
        governor=governor, flags=dict(FLAGS),
    )
    try:
        for _ in range(TICKS):
            kernel.tick_once()
    finally:
        kernel.shutdown()
    return kernel, governor


def test_overrun_never_drops_results_or_forces_a_mode():
    kernel, governor = _run()
    status = kernel._status

    assert governor.forced == [], "the mid-tick throttle must not call force_mode"
    assert status.current_mode is RuntimeMode.NORMAL
    assert status.total_dropped_work == 0, "no result may be dropped by the wall clock, and no 9999 sentinel"


def test_overrun_is_recorded_as_typed_telemetry():
    kernel, _ = _run()
    status = kernel._status

    assert status.total_budget_overruns > 0, "the 1 ms budget is overrun every tick; the run must say so"
    assert status.budget_overrun_ms > 0.0


def test_nothing_in_the_governor_or_the_signals_reads_the_overrun():
    """PERF-D1 amendment A1: the overrun is telemetry, not an input."""
    import inspect

    from src.core import governance
    from src.engine import governor as governor_module

    assert "budget_overrun" not in inspect.getsource(governor_module)
    assert "budget_overrun" not in inspect.getsource(governance)


def test_authoritative_state_does_not_carry_the_overrun():
    import inspect

    from src.core import state

    assert "budget_overrun" not in inspect.getsource(state)

