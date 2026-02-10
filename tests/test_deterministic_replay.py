"""Tests for deterministic simulation replay.

The engine uses domain-separated xxhash RNG, so two runs with the same seed
and config MUST produce identical world states at every tick. This test
runs the full engine twice and compares state hashes.
"""

import sys
import os
import hashlib
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import SimulationConfig
from src.api.engine_manager import EngineManager


def _state_fingerprint(mgr: EngineManager) -> str:
    """Hash the observable world state into a short hex digest."""
    snap = mgr.get_snapshot()
    assert snap is not None, "Snapshot must exist after build"

    parts: list[str] = [f"tick={snap.tick}", f"seed={snap.seed}"]

    # Entity state — sorted by ID for determinism
    for eid in sorted(snap.entities):
        e = snap.entities[eid]
        parts.append(
            f"e{eid}:{e.kind}@{e.pos.x},{e.pos.y}"
            f"|hp={e.stats.hp}/{e.stats.max_hp}"
            f"|atk={e.stats.atk}|def={e.stats.def_}|spd={e.stats.spd}"
            f"|xp={e.stats.xp}|lvl={e.stats.level}|gold={e.stats.gold}"
            f"|alive={e.alive}|state={e.ai_state}"
        )

    # Ground items — sorted by position
    for pos in sorted(snap.ground_items):
        items = snap.ground_items[pos]
        parts.append(f"ground{pos}:{','.join(sorted(items))}")

    raw = "\n".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()


def _run_n_ticks(seed: int, ticks: int, entities: int = 5) -> list[str]:
    """Build an EngineManager, tick N times, return fingerprint per tick."""
    cfg = SimulationConfig(
        world_seed=seed,
        max_ticks=ticks + 1,
        initial_entity_count=entities,
        num_workers=1,            # single worker for determinism
        grid_width=64,
        grid_height=64,
        num_camps=2,
        num_forest_regions=1,
        num_desert_regions=1,
        num_swamp_regions=1,
        num_mountain_regions=1,
        num_ruins=1,
        num_dungeon_entrances=0,
        resources_per_region=2,
    )
    mgr = EngineManager(cfg)
    fingerprints: list[str] = [_state_fingerprint(mgr)]

    loop = mgr._loop
    assert loop is not None

    for _ in range(ticks):
        cont = loop.tick_once()
        # Update snapshot so fingerprint reads new state
        snap = loop.create_snapshot()
        with mgr._snapshot_lock:
            mgr._latest_snapshot = snap
        fingerprints.append(_state_fingerprint(mgr))
        if not cont:
            break

    if mgr._worker_pool:
        mgr._worker_pool.shutdown()

    return fingerprints


class TestDeterministicReplay:
    """Two runs with the same seed must produce identical state at every tick."""

    def test_initial_state_identical(self):
        """Tick 0 (after build, before any ticks) must match."""
        fp_a = _run_n_ticks(seed=42, ticks=0)
        fp_b = _run_n_ticks(seed=42, ticks=0)
        assert fp_a[0] == fp_b[0], "Initial state diverged"

    def test_10_ticks_identical(self):
        """10 ticks with seed=42 must produce identical fingerprints."""
        fp_a = _run_n_ticks(seed=42, ticks=10, entities=5)
        fp_b = _run_n_ticks(seed=42, ticks=10, entities=5)
        assert len(fp_a) == len(fp_b), f"Tick counts differ: {len(fp_a)} vs {len(fp_b)}"
        for i, (a, b) in enumerate(zip(fp_a, fp_b)):
            assert a == b, f"State diverged at tick {i}"

    @pytest.mark.slow
    def test_50_ticks_identical(self):
        """50 ticks — longer run catches late-tick drift."""
        fp_a = _run_n_ticks(seed=99, ticks=50, entities=8)
        fp_b = _run_n_ticks(seed=99, ticks=50, entities=8)
        assert len(fp_a) == len(fp_b)
        for i, (a, b) in enumerate(zip(fp_a, fp_b)):
            assert a == b, f"State diverged at tick {i}"

    def test_different_seeds_diverge(self):
        """Different seeds must produce different state."""
        fp_a = _run_n_ticks(seed=42, ticks=5, entities=5)
        fp_b = _run_n_ticks(seed=99, ticks=5, entities=5)
        # At least one tick should differ (almost certainly all after tick 0)
        assert any(a != b for a, b in zip(fp_a, fp_b)), "Different seeds produced same state"
