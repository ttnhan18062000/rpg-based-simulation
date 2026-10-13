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


# ── build_mixed_state (TCK-20261004-PERF-SCENARIO-MIXED-STATE-SPAWN-COLLISION) ──
# It merges idle heroes (x = id % 100), arena monsters (x = 5) and resource nodes under independent coordinate schemes, so a monster landed on a hero's tile
# (5, 0) and on a node's tile (5, 10). Measured before the fix: 2 violations at 100, 2 at 200, 7 at 1000.


@pytest.mark.parametrize("entity_count", [100, 200, 1000])
def test_mixed_state_places_no_two_objects_on_one_tile(entity_count):
    from src.perf.scenarios import build_mixed_state

    assert _spawn_violations(build_mixed_state(entity_count=entity_count)) == []


def test_mixed_state_keeps_every_object_and_only_moves_colliding_monsters():
    from src.perf.scenarios import build_combat_arena_state, build_idle_state, build_mixed_state

    state = build_mixed_state(entity_count=200)
    heroes = build_idle_state(entity_count=80)
    assert len(state.entities) == 80 + 60 and len(state.resource_nodes) == 60
    assert all(state.entities[i].navigation.position == h.navigation.position for i, h in heroes.entities.items())
    arena = build_combat_arena_state(team_a_count=0, team_b_count=60, seed=43)
    moved = [eid for eid, m in arena.entities.items() if state.entities[80 + eid].navigation.position != m.navigation.position]
    assert moved, "the 200-entity mix collides, so at least one monster must have moved"
    for eid in moved:  # a moved monster keeps its x and only slides along y
        assert state.entities[80 + eid].navigation.position[0] == arena.entities[eid].navigation.position[0]


def test_mixed_state_is_deterministic_in_positions_and_proof_digest():
    from src.perf.scenarios import build_mixed_state

    a, b = build_mixed_state(entity_count=200), build_mixed_state(entity_count=200)
    assert {i: e.navigation.position for i, e in a.entities.items()} == {i: e.navigation.position for i, e in b.entities.items()}
    sched = CanonicalHashScheduler()
    da, db = sched.compute_digest(a, 0), sched.compute_digest(b, 0)
    assert da.status is DigestStatus.COMPUTED and da == db


def test_first_free_tile_slides_along_y_only_past_taken_tiles():
    from src.perf.scenarios import _first_free_tile

    assert _first_free_tile((5.0, 0.0), set()) == (5.0, 0.0)
    assert _first_free_tile((5.0, 0.0), {(5.0, 0.0), (5.0, 1.0)}) == (5.0, 2.0)
    assert _first_free_tile((5.0, 0.0), {(6.0, 0.0)}) == (5.0, 0.0)
