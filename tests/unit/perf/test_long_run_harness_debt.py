"""Work-debt accounting of the long-run harness (TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS, PA-02).

`work_debt` is an integer counter per system (PERF-D3). The harness used to call `len()` on those
integers, which raised `TypeError` on the first sample after any debt existed. Every earlier fixture
had empty debt, so nothing noticed. These tests run the real kernel with non-zero debt.

All measurements here are correctness checks of counters and digests, never timings.
"""
from __future__ import annotations

import dataclasses
from typing import Dict, List

import pytest

from src.config.profiles import HardwareClass, RuntimeProfile
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.kernel import Kernel
from src.perf import long_run_harness as lrh
from src.perf.long_run_harness import LongRunStabilityHarness, RunMode
from src.perf.scenarios import SCENARIO_BUILDERS
from src.platform.rng import DeterministicRNG

SCENARIO = "idle"  # no combat: the tactical-path nondeterminism ticket is open
ENTITIES = 5
SEED = 7
FLAGS = {"audit_mode": True}


def _profile(workers: int) -> RuntimeProfile:
    return RuntimeProfile(
        name="debt_harness_test",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=80.0,
        max_worker_count=workers,  # drain_debt() clears this many debt units per system per tick
        max_queue_depth=500,
        max_replay_buffer_kb=4096,
        max_observability_budget_percent=10.0,
        max_tick_budget_ms=50.0,
    )


@pytest.fixture
def recorded(monkeypatch):
    """Patch a recording Kernel into the harness and seed debt into the scenario's initial state.

    `ticks[i]` is the `work_debt` dict after the (i+1)-th `tick_once()` of the run, warmup included.
    """
    ticks: List[Dict[str, int]] = []
    digests: List[str] = []
    seed_debt: Dict[str, int] = {}

    class RecordingKernel(Kernel):
        def tick_once(self) -> None:
            super().tick_once()
            ticks.append(dict(self.state.work_debt))
            digests.append(CanonicalStateHasher.get_hash(self.state))

    real_builder = SCENARIO_BUILDERS[SCENARIO]

    def seeded_builder(entity_count, seed):
        return dataclasses.replace(real_builder(entity_count=entity_count, seed=seed), work_debt=dict(seed_debt))

    monkeypatch.setattr(lrh, "Kernel", RecordingKernel)
    monkeypatch.setitem(SCENARIO_BUILDERS, SCENARIO, seeded_builder)
    return ticks, digests, seed_debt


def _run(workers: int, total: int, warmup: int = 0, interval: int = 1):
    return LongRunStabilityHarness(_profile(workers)).execute_run(
        SCENARIO, total_ticks=total, entity_count=ENTITIES, warmup_ticks=warmup,
        sample_interval=interval, mode=RunMode.PURE, seed=SEED, flags=FLAGS,
    )


@pytest.mark.parametrize(
    "debt, expected_total, expected_systems",
    [
        ({}, 0, 0),
        ({"A": 3}, 3, 1),
        ({"A": 3, "B": 5, "C": 1}, 9, 3),
        ({"A": 3, "B": 0}, 3, 1),  # a zero entry is not a system with debt
    ],
)
def test_samples_report_exact_debt_when_nothing_drains(recorded, debt, expected_total, expected_systems):
    _, _, seed_debt = recorded
    seed_debt.update(debt)
    report = _run(workers=0, total=3)  # max_worker_count 0: drain is 0, debt stays put

    assert [s.tick for s in report.samples] == [1, 2, 3]
    for s in report.samples:
        assert s.work_debt == expected_total
        assert s.systems_with_debt == expected_systems


def test_system_whose_debt_returns_to_zero_leaves_the_count(recorded):
    ticks, _, seed_debt = recorded
    seed_debt.update({"A": 2, "B": 4})
    report = _run(workers=1, total=6)

    by_tick = {s.tick: s for s in report.samples}
    # Hand-computed: one unit drains per system per tick, floored at zero.
    expected = {1: (1, 3), 2: (0, 2), 3: (0, 1), 4: (0, 0), 5: (0, 0), 6: (0, 0)}
    for tick, (a, b) in expected.items():
        assert ticks[tick - 1] == {k: v for k, v in {"A": a, "B": b}.items()}, f"state at tick {tick}"
        assert by_tick[tick].work_debt == a + b
        assert by_tick[tick].systems_with_debt == (a > 0) + (b > 0)


def test_samples_equal_the_kernel_state_at_the_same_tick(recorded):
    """Real kernel, real drain, warmup before sampling, sparse sampling interval."""
    ticks, _, seed_debt = recorded
    seed_debt.update({"A": 9, "B": 6, "C": 2})
    warmup, total, interval = 2, 8, 2
    report = _run(workers=1, total=total, warmup=warmup, interval=interval)

    assert [s.tick for s in report.samples] == [2, 4, 6, 8]
    for s in report.samples:
        state_debt = ticks[warmup + s.tick - 1]
        assert s.work_debt == sum(state_debt.values())
        assert s.systems_with_debt == sum(1 for d in state_debt.values() if d > 0)
    assert report.samples[0].work_debt > report.samples[-1].work_debt  # debt really drained during the run


def test_sampling_does_not_change_the_proof_digest(recorded):
    """Digest of a harness run (sampling every tick) equals a bare kernel loop at every tick (PERF-D5)."""
    ticks, digests, seed_debt = recorded
    seed_debt.update({"A": 4, "B": 2})
    total = 6
    _run(workers=1, total=total, warmup=0, interval=1)
    harness_digests = list(digests)
    assert len(harness_digests) == total

    bare_state = SCENARIO_BUILDERS[SCENARIO](entity_count=ENTITIES, seed=SEED)
    effective_flags = {"no_frame_pacing": True, "no_replay": True, "force_full_scan": False, **FLAGS}
    bare = Kernel(_profile(1), bare_state, DeterministicRNG(SEED), flags=effective_flags)
    try:
        for i in range(total):
            bare.tick_once()
            assert CanonicalStateHasher.get_hash(bare.state) == harness_digests[i], f"digest differs at tick {i + 1}"
    finally:
        bare.shutdown()  # releases the drain-worker thread the session sentinel counts
