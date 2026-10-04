"""`state.work_debt` stays empty in ordinary runs, even when work is dropped
(TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION, investigation).

Finding recorded by these tests: nothing in `src/` increases `AuthoritativeState.work_debt`. The only
producer of a debt update is the executor's `DRAIN_DEBT` branch, which only drains debt that already
exists, and dropped work is counted in `RuntimeStatus`, not in `state.work_debt`. So every quantity
derived from the debt total (governor thresholds, the kernel's `debt_ratio`) is constant zero.

The runs use a tight tick budget (the smallest the profile validator accepts) with `audit_mode` off, so
the governor really degrades and the kernel really sheds work. They measure counters, never timings, and
are not a determinism claim. Scenarios are non-combat.
"""
from __future__ import annotations

from typing import Dict, List

import pytest

from src.certification.scenarios import PressureInjector
from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.governance import RuntimeMode
from src.engine.kernel import Kernel
from src.perf.scenarios import (
    build_idle_state, build_movement_state, build_resource_state, build_strategic_state,
)
from src.platform.rng import DeterministicRNG

TICKS = 12
ENTITIES = 120
FLAGS = {"no_frame_pacing": True, "no_replay": True}  # audit_mode off: the real, wall-clock-driven degradation path

SCENARIOS = {
    "idle": lambda: build_idle_state(entity_count=ENTITIES),
    "movement": lambda: build_movement_state(entity_count=ENTITIES),
    "resource": lambda: build_resource_state(entity_count=ENTITIES, node_count=10),
    "strategic": lambda: build_strategic_state(entity_count=ENTITIES),
}


def _tight_profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="tight_budget", hardware_class=HardwareClass.CLASS_B, max_ram_mb=512, max_cpu_percent=80.0,
        max_worker_count=0, max_queue_depth=500, max_replay_buffer_kb=4096, max_observability_budget_percent=10.0,
        max_tick_budget_ms=1.0,  # the validator rejects anything below 1 ms
    )


class _RecordingKernel(Kernel):
    """Records `work_debt`, the governor's debt signal and the mode after every tick."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.debt_by_tick: List[Dict[str, int]] = []
        self.debt_signal_by_tick: List[int] = []
        self.modes: List[RuntimeMode] = []

    def tick_once(self) -> None:
        super().tick_once()
        self.debt_by_tick.append(dict(self.state.work_debt))
        signals = self._current_signals
        self.debt_signal_by_tick.append(signals.work_debt_total if signals is not None else 0)
        self.modes.append(self.status.current_mode)


def _run(state, ticks: int = TICKS) -> _RecordingKernel:
    kernel = _RecordingKernel(_tight_profile(), state, DeterministicRNG(7), flags=dict(FLAGS))
    try:
        for _ in range(ticks):
            kernel.tick_once()
    finally:
        kernel.shutdown()
    return kernel


@pytest.mark.parametrize("scenario", list(SCENARIOS))
def test_work_debt_stays_empty_while_work_is_dropped(scenario: str):
    kernel = _run(SCENARIOS[scenario]())

    # Precondition: the run really shed work and the governor really left NORMAL.
    assert kernel.status.total_dropped_work > 0, "no work was dropped; the run does not test the claim"
    assert any(mode is not RuntimeMode.NORMAL for mode in kernel.modes)

    # The claim: debt never appears, so every debt-derived quantity is constant zero.
    assert all(debt == {} for debt in kernel.debt_by_tick)
    assert set(kernel.debt_signal_by_tick) == {0}


def test_the_instrument_sees_debt_when_it_is_seeded():
    """Control: an empty result above is not a blind spot of the recorder.

    With `max_worker_count` 0 the drain is 0, so seeded debt stays at its seeded value, and the governor's
    debt signal follows it.
    """
    state = PressureInjector.inject_work_debt(SCENARIOS["idle"](), "SYS_A", 5)
    kernel = _run(state, ticks=4)
    assert kernel.debt_by_tick == [{"SYS_A": 5}] * 4
    assert kernel.debt_signal_by_tick[-1] == 5
