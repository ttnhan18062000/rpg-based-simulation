import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


import pytest
import time
from src.config import SimulationConfig
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.core.models.vectors import Vector2
from src.platform.spatial_hash import SpatialHash
from src.platform.rng import DeterministicRNG
from src.core.entities.entity_builder import EntityBuilder
from src.engine.world_loop import WorldLoop
from src.engine.worker_pool import WorkerPool
from src.engine.conflict_resolver import ConflictResolver
from src.systems.world.generator import EntityGenerator
from src.ai.brain import AIBrain

def run_bench(entity_count: int, ticks: int = 10):
    config = SimulationConfig(num_workers=1) # Inline for benchmark
    grid = Grid(512, 512)
    spatial = SpatialHash(cell_size=8)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    rng = DeterministicRNG(42)
    
    # 1. Spawn Entities
    builder = EntityBuilder(rng, 0)
    for i in range(entity_count):
        x = (i * 7) % 512
        y = (i * 13) % 512
        e = EntityBuilder(rng, i+1).kind("goblin").at(Vector2(x, y)).build()
        world.add_entity(e)
        
    brain = AIBrain(config, rng)
    pool = WorkerPool(config, brain, rng)
    resolver = ConflictResolver(config, rng)
    gen = EntityGenerator(config, rng)
    
    loop = WorldLoop(config, world, pool, resolver, gen, rng=rng)
    
    # 2. Benchmark
    start = time.time()
    for _ in range(ticks):
        loop.tick_once()
    end = time.time()
    
    duration = end - start
    tps = ticks / duration if duration > 0 else float('inf')
    eps = (entity_count * ticks) / duration if duration > 0 else float('inf')
    
    print(f"\n[BENCH] Entities: {entity_count} | Ticks: {ticks} | Duration: {duration:.3f}s | TPS: {tps:.1f} | EPS (Entities/s): {eps:.1f}")
    return tps, eps

def test_scaling_100_entities():
    tps, eps = run_bench(100)
    assert tps > 1.0 # Minimal sanity check

def test_scaling_500_entities():
    tps, eps = run_bench(500)
    assert tps > 0.5

@pytest.mark.slow
def test_scaling_1000_entities():
    tps, eps = run_bench(1000)
    assert tps > 0.1
