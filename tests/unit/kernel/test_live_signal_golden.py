"""Live signals are bit-identical after the signal-source move (PERF-D1; TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY, step 2).

``record_live_run`` drives a seeded Live kernel on a call-counting fake clock, so every cost is an exact number and the governor really changes
mode, and records for each tick the mode, the pressure signals the governor was given at the start of the tick and the signals recorded at the end.
``golden/live_signals_v1.json`` was recorded from the code *before* the construction moved out of ``Kernel`` into ``signal_source.py``
(``GOLDEN_RECORD=<path> pytest <this file>`` rewrites it; only do that when a Live behaviour change is intended and recorded as a divergence).
"""
from __future__ import annotations

import dataclasses
import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.config.profiles import HardwareClass, RuntimeProfile
from src.engine.kernel import Kernel
from src.perf.scenarios import build_movement_state
from src.platform.rng import DeterministicRNG

NEW_FIELDS = ("tick_cost", "tick_budget", "phase_cost")  # added after the fixture was recorded; a Live source must leave them None
GOLDEN = Path(__file__).parent / "golden" / "live_signals_v1.json"
TICKS = 16


class CountingClock:
    """Fake ``time.perf_counter_ns``: every read returns the previous value plus ``step_ns`` (the test changes it per tick)."""

    def __init__(self) -> None:
        self.now_ns = 0
        self.step_ns = 400_000

    def __call__(self) -> int:
        self.now_ns += self.step_ns
        return self.now_ns


def _profile() -> RuntimeProfile:
    return RuntimeProfile(
        name="live_signal_golden", hardware_class=HardwareClass.CLASS_B, max_ram_mb=100000, max_cpu_percent=90.0,
        max_worker_count=0, max_queue_depth=100, max_replay_buffer_kb=1024, max_observability_budget_percent=10.0,
        max_tick_budget_ms=60.0, sampling_interval_ticks=1, dwell_time_ticks=2, confidence_window_ticks=2,
    )


def _as_dict(signals) -> dict:
    values = dataclasses.asdict(signals)
    for name in NEW_FIELDS:
        assert values.pop(name, None) is None, f"a Live run must not set {name}"
    return values


def record_live_run(monkeypatch) -> list[dict]:
    clock = CountingClock()
    monkeypatch.setattr(time, "perf_counter_ns", clock)
    kernel = Kernel(_profile(), build_movement_state(entity_count=30), DeterministicRNG(7),
                    flags={"no_frame_pacing": True, "no_replay": True})
    kernel._collector._process.memory_info = MagicMock(return_value=MagicMock(rss=100 * 1024 * 1024))
    rows = []
    try:
        for tick in range(TICKS):
            clock.step_ns = 1_600_000 if 2 <= tick < 7 else 400_000  # a loaded stretch, so the governor escalates and then recovers
            kernel.tick_once()
            rows.append({
                "mode": kernel._status.current_mode.name,
                "start": _as_dict(kernel._current_signals),
                "end": _as_dict(kernel._status.signal_history[-1]),
            })
    finally:
        kernel.shutdown()
    return rows


def test_live_signals_are_bit_identical_after_the_move(monkeypatch):
    rows = json.loads(json.dumps(record_live_run(monkeypatch)))  # same float round trip as the stored fixture
    target = os.environ.get("GOLDEN_RECORD")
    if target:
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        Path(target).write_text(json.dumps(rows, indent=1, sort_keys=True) + "\n")
        pytest.skip(f"recorded {len(rows)} ticks to {target}")
    assert rows == json.loads(GOLDEN.read_text())
    assert len({row["mode"] for row in rows}) >= 2, "a run that never changes mode would prove little about the governor's inputs"
