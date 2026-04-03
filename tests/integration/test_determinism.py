import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
import time
from src.config import SimulationConfig
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.platform.spatial_hash import SpatialHash
from src.platform.rng import DeterministicRNG
from src.engine.world_loop import WorldLoop
from src.engine.worker_pool import WorkerPool
from src.engine.conflict_resolver import ConflictResolver
from src.ai.brain import AIBrain
from src.systems.world.generator import EntityGenerator

class MockEmit:
    def __call__(self, category: str, message: str, **kwargs):
        pass

def run_simulation(seed: int, ticks: int) -> str:
    """Run a simulation with a fixed seed and return its final state hash."""
    cfg = SimulationConfig(
        grid_width=50, 
        grid_height=50,
        initial_entity_count=10,
        generator_max_entities=20,
        max_ticks=ticks,
        num_workers=1 # Single worker avoids race conditions in non-thread-safe parts
    )
    
    rng = DeterministicRNG(seed)
    grid = Grid(cfg.grid_width, cfg.grid_height)
    spatial = SpatialHash(cfg.spatial_cell_size)
    world = WorldState(seed=seed, grid=grid, spatial_index=spatial)
    
    # Standard helper setup
    brain = AIBrain(cfg, rng)
    worker_pool = WorkerPool(cfg, brain, rng)
    conflict_resolver = ConflictResolver(cfg, rng)
    generator = EntityGenerator(cfg, rng)
    
    # WorldLoop initialization (using the new phases)
    loop = WorldLoop(
        config=cfg,
        world=world,
        worker_pool=worker_pool,
        conflict_resolver=conflict_resolver,
        generator=generator,
        rng=rng
    )
    
    # Execute the requested number of ticks
    for _ in range(ticks):
        loop.tick_once()
    
    worker_pool.shutdown()
    return world.compute_hash()

def test_simulation_determinism():
    """Verify that two identical simulations with the same seed produce the same result."""
    seed = 42
    ticks = 50
    
    print(f"\nRunning simulation A (seed={seed}, ticks={ticks})...")
    hash_a = run_simulation(seed, ticks)
    
    print(f"Running simulation B (seed={seed}, ticks={ticks})...")
    hash_b = run_simulation(seed, ticks)
    
    print(f"Hash A: {hash_a}")
    print(f"Hash B: {hash_b}")
    
    assert hash_a == hash_b, "Simulation is non-deterministic! Hashes should match for the same seed."

def test_different_seeds_different_hashes():
    """Verify that different seeds produce different world states."""
    ticks = 20
    hash_1 = run_simulation(101, ticks)
    hash_2 = run_simulation(102, ticks)
    
    assert hash_1 != hash_2, "Different seeds produced identical hashes (highly unlikely)."
