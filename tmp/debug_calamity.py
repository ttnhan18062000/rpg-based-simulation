import os
import sys
import time
import logging

# Set up logging to stdout
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, os.getcwd())

try:
    from src.core.enums import AIState, EntityRole, Faction, HeroClass
    from src.core.models import Vector2, Entity
    from src.core.grid import Grid
    from src.systems.spatial_hash import SpatialHash
    from src.core.world_state import WorldState
    from src.systems.generator import EntityGenerator
    from src.engine.world_loop import WorldLoop
    from src.config import SimulationConfig
    from src.systems.rng import DeterministicRNG
    from src.ai.brain import AIBrain
    from src.engine.worker_pool import WorkerPool
    from src.engine.conflict_resolver import ConflictResolver
    from unittest.mock import MagicMock
except ImportError as e:
    logger.error(f"Import failed: {e}")
    sys.exit(1)

def run_diagnostic():
    logger.info("Initializing setup...")
    config = SimulationConfig()
    grid = Grid(100, 100)
    spatial = SpatialHash(5)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    rng = DeterministicRNG(42)
    
    brain = AIBrain(config, rng)
    worker_pool = MagicMock()
    conflict_resolver = ConflictResolver(config, rng)
    generator = EntityGenerator(config, rng)
    
    loop = WorldLoop(config, world, worker_pool, conflict_resolver, generator, rng=rng)
    
    logger.info("Spawning calamity...")
    boss = generator.spawn_calamity(world, "gorath")
    if boss:
        world.add_entity(boss)
        logger.info(f"Boss spawned at {boss.pos}")
    
    logger.info("Running tick check for spawns...")
    world.tick = 5000
    loop._check_calamity_spawns()
    logger.info("Calamity spawn check done.")
    
    logger.info("Applying auras...")
    loop._apply_calamity_auras()
    logger.info("Aura application done.")
    
    logger.info("Running complete tick...")
    loop.tick_once()
    logger.info("Tick once done.")

if __name__ == "__main__":
    start_time = time.time()
    try:
        run_diagnostic()
        logger.info(f"Diagnostic completed in {time.time() - start_time:.2f}s")
    except Exception as e:
        logger.error(f"Diagnostic failed with error: {e}")
        import traceback
        traceback.print_exc()
