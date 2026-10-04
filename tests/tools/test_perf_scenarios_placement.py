"""Placement legality of the perf-harness scenario builders (TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION)."""
from __future__ import annotations

import pytest

from src.config.profiles import PROD_SMALL as SimulationProfile
from src.engine.checkpoint import CanonicalHashScheduler, DigestStatus
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.observability.hard_law_monitor import HardLawMonitor
from src.perf.scenarios import build_metropolis_state
from src.platform.rng import DeterministicRNG


def _spawn_violations(state):
    return [v for v in HardLawMonitor.check_initial_placement(state) if v.law_id == "LAW-SPAWN-OCCUPANCY"]


@pytest.mark.parametrize("entity_count,region_count", [(1000, 50), (500, 50), (200, 50), (100, 7)])
def test_metropolis_places_no_two_objects_on_one_tile(entity_count, region_count):
    state = build_metropolis_state(entity_count=entity_count, region_count=region_count)
    assert _spawn_violations(state) == []


def test_metropolis_is_deterministic_in_positions_and_proof_digest():
    a = build_metropolis_state(entity_count=200)
    b = build_metropolis_state(entity_count=200)
    assert {i: e.navigation.position for i, e in a.entities.items()} == {
        i: e.navigation.position for i, e in b.entities.items()
    }
    sched = CanonicalHashScheduler()
    da, db = sched.compute_digest(a, 0), sched.compute_digest(b, 0)
    assert da.status is DigestStatus.COMPUTED and da == db


def test_metropolis_raises_when_a_region_has_no_free_tile_left():
    with pytest.raises(ValueError, match="raise region_count"):
        build_metropolis_state(entity_count=2000, region_count=1)


def test_metropolis_kernel_ticks_record_no_placement_violation():
    state = build_metropolis_state(entity_count=100)
    kernel = Kernel(
        SimulationProfile, state, DeterministicRNG(42), executor=LocalSequentialExecutor(),
        flags={"audit_mode": True, "no_frame_pacing": True, "no_replay": True},
    )
    try:
        for _ in range(3):
            kernel.tick_once()
        recorded = getattr(kernel._status, "hard_law_violations", [])
        assert [v for v in recorded if v.law_id in ("LAW-SPAWN-OCCUPANCY", "LAW-OCCUPANCY-COLLISION")] == []
    finally:
        kernel.shutdown()
