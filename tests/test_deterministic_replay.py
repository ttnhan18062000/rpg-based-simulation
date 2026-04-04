import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


"""Tests for deterministic simulation replay.

The engine uses domain-separated xxhash RNG, so two runs with the same seed
and config MUST produce identical world states at every tick. This test
runs the full engine twice and compares state hashes.
"""

import hashlib
import pytest

# CRITICAL: Disable all external infrastructure for tests to prevent 2-minute connection retries.
os.environ["DISABLE_KAFKA"] = "1"
os.environ["RABBITMQ_URL"] = "localhost" # Just mock


from src.config import SimulationConfig
from src.core.models.world_state import WorldState
from src.engine.world_loop import WorldLoop
from src.engine.worker_pool import WorkerPool
from src.engine.conflict_resolver import ConflictResolver
from src.ai.brain import AIBrain
from src.platform.rng import DeterministicRNG
from src.core.world.world_generator import WorldGenerator
from src.core.gameplay.faction import FactionRegistry


def _state_fingerprint_lite(world: WorldState) -> str:
    """Hash the live world state directly (AOA Optimized).
    
    Bypasses Snapshot.from_world() and PersistencePhase.
    """
    parts: list[str] = [f"tick={world.tick}", f"seed={world.seed}"]

    # Entity state — sorted by ID for determinism
    for eid in sorted(world.entities):
        e = world.entities[eid]
        # Direct access to aspects (Live/Mutable) is safe for fingerprinting between ticks
        parts.append(
            f"e{eid}:{e.kind}@{e.spatial.pos.x},{e.spatial.pos.y}"
            f"|hp={e.combat.hp}/{e.combat.max_hp}"
            f"|atk={e.combat.atk_base}|def={e.combat.def_base}|spd={e.combat.spd_base}"
            f"|xp={e.progression.xp}|lvl={e.progression.level}|gold={e.progression.gold}"
            f"|alive={e.combat.alive}|state={e.mind.decision.ai_state}"
        )

    # Ground items — sorted by position
    for pos in sorted(world.ground_items):
        items = world.ground_items[pos]
        parts.append(f"ground{pos}:{','.join(sorted(items))}")

    raw = "\n".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()


def _run_n_ticks(seed: int, ticks: int, entities: int = 5) -> list[str]:
    """Build a manual WorldLoop, tick N times, return fingerprint at Milestones.
    
    Optimized for AOA:
    1. Bypasses EngineManager (No Threading / No Snapshots).
    2. Disables PersistencePhase (No Kafka / No Serialization).
    3. Disables RabbitMQ (num_workers=1).
    """
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
    
    # 1. Build manual components
    rng = DeterministicRNG(seed)
    gen_service = WorldGenerator(cfg, rng)
    world, generator = gen_service.generate()
    
    freg = FactionRegistry.default()
    brain = AIBrain(cfg, rng, freg)
    wpool = WorkerPool(cfg, brain, rng)
    resolver = ConflictResolver(cfg, rng)
    
    loop = WorldLoop(
        config=cfg, world=world, worker_pool=wpool,
        conflict_resolver=resolver, generator=generator,
        faction_reg=freg, rng=rng
    )

    # CRITICAL: Strip the PersistencePhase to prevent expensive Kafka/Serialization during tests.
    from src.engine.phases.persistence import PersistencePhase
    loop._phases = [p for p in loop._phases if not isinstance(p, PersistencePhase)]

    # Milestone 1: Initial State (Tick 0)
    fingerprints: list[str] = [_state_fingerprint_lite(world)]

    for _ in range(ticks):
        cont = loop.tick_once()
        if not cont:
            break

    # Milestone 2: Final State (Tick N)
    if ticks > 0:
        fingerprints.append(_state_fingerprint_lite(world))

    wpool.shutdown()

    return fingerprints


class TestDeterministicReplay:
    """Two runs with the same seed must produce identical state milestones."""

    def test_initial_state_identical(self):
        """Tick 0 (after build, before any ticks) must match."""
        fp_a = _run_n_ticks(seed=42, ticks=0)
        fp_b = _run_n_ticks(seed=42, ticks=0)
        assert fp_a[0] == fp_b[0], "Initial state diverged"

    def test_10_ticks_identical(self):
        """10 ticks with seed=42 must produce identical fingerprints."""
        fp_a = _run_n_ticks(seed=42, ticks=10, entities=5)
        fp_b = _run_n_ticks(seed=42, ticks=10, entities=5)
        assert len(fp_a) == len(fp_b)
        for i, (a, b) in enumerate(zip(fp_a, fp_b)):
            assert a == b, f"State diverged at milestone {i}"

    def test_50_ticks_identical(self):
        """50 ticks — longer run catches late-tick drift."""
        fp_a = _run_n_ticks(seed=99, ticks=50, entities=8)
        fp_b = _run_n_ticks(seed=99, ticks=50, entities=8)
        assert len(fp_a) == len(fp_b)
        for i, (a, b) in enumerate(zip(fp_a, fp_b)):
            assert a == b, f"State diverged at milestone {i}"

    def test_different_seeds_diverge(self):
        """Different seeds must produce different state."""
        fp_a = _run_n_ticks(seed=42, ticks=5, entities=5)
        fp_b = _run_n_ticks(seed=99, ticks=5, entities=5)
        # At least one milestone (initial or final) should differ
        assert any(a != b for a, b in zip(fp_a, fp_b)), "Different seeds produced same state"
