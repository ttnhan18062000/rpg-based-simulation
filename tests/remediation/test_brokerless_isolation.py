import pytest
import sys
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_missing_brokers():
    """Mock sys.modules to pretend pika and confluent_kafka are not installed."""
    with patch.dict("sys.modules", {"pika": None, "confluent_kafka": None}):
        yield

def test_rabbitmq_client_handles_missing_pika(mock_missing_brokers):
    """Verify that rabbitmq_client correctly detects missing library."""
    # We must reload or re-import to see the mocked state if it was already imported
    import importlib
    import src.api.rabbitmq_client as rm_client
    importlib.reload(rm_client)
    
    assert rm_client.HAS_PIKA is False
    assert rm_client.get_rabbitmq() is None

def test_kafka_client_handles_missing_confluent_kafka(mock_missing_brokers):
    """Verify that kafka_client correctly detects missing library."""
    import importlib
    import src.api.kafka_client as k_client
    importlib.reload(k_client)
    
    assert k_client.HAS_KAFKA is False
    assert k_client.get_kafka_producer() is None
    assert k_client.create_kafka_consumer() is None

def test_simulation_step_runs_without_brokers(mock_missing_brokers):
    """Verify that a simulation step can be executed even if brokers are missing.
    [INFRA ISOLATION PROOF]
    """
    import importlib
    import src.api.rabbitmq_client
    import src.api.kafka_client
    importlib.reload(src.api.rabbitmq_client)
    importlib.reload(src.api.kafka_client)

    from src.engine.world_loop import WorldLoop
    from src.core.models.world_state import WorldState
    from src.core.entities.entity import Entity
    from src.config import SimulationConfig
    from src.engine.worker_pool import WorkerPool
    from src.engine.conflict_resolver import ConflictResolver
    from src.systems.world.generator import EntityGenerator
    from src.ai.brain import AIBrain
    from src.platform.rng import DeterministicRNG
    from src.core.gameplay.faction import FactionRegistry
    from src.core.world.grid import Grid
    from src.platform.spatial_hash import SpatialHash
    
    # 1. Setup minimal world
    cfg = SimulationConfig()
    grid = Grid(cfg.grid_width, cfg.grid_height)
    spatial = SpatialHash(cfg.spatial_cell_size)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    hero = Entity(id=1, kind="hero")
    world.add_entity(hero)
    
    # 2. Setup components
    rng = DeterministicRNG(42)
    faction_reg = FactionRegistry.default()
    brain = AIBrain(cfg, rng, faction_reg)
    worker_pool = WorkerPool(cfg, brain, rng)
    conflict_resolver = ConflictResolver(cfg, rng)
    generator = EntityGenerator(cfg, rng)
    
    # 3. Setup loop with disabled brokers (env vars)
    with patch.dict("os.environ", {"DISABLE_RABBITMQ": "1", "DISABLE_KAFKA": "1"}):
        loop = WorldLoop(
            config=cfg, 
            world=world, 
            worker_pool=worker_pool,
            conflict_resolver=conflict_resolver,
            generator=generator,
            rng=rng,
            faction_reg=faction_reg
        )
        # Verify loop doesn't crash during initialization or first step
        try:
            loop.tick_once()
        except Exception as e:
            pytest.fail(f"WorldLoop.tick_once() crashed without brokers: {e}")

def test_engine_manager_recovery_handles_missing_kafka(mock_missing_brokers):
    """Verify that EngineManager recovery mode doesn't crash if Kafka is missing."""
    import importlib
    import src.api.kafka_client
    import src.api.engine_manager as engine_manager
    importlib.reload(src.api.kafka_client)
    importlib.reload(engine_manager)
    
    from src.api.engine_manager import EngineManager
    from src.config import SimulationConfig
    
    cfg = SimulationConfig()
    manager = EngineManager(config=cfg)
    # verify that recovery attempts don't hard crash
    try:
        # Should return None or log error instead of crashing
        res = manager._try_recover_world(cfg)
        assert res is None
    except Exception as e:
        pytest.fail(f"EngineManager._try_recover_world() crashed without Kafka: {e}")
