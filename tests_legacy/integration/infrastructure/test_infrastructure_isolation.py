import pytest
import os
import sys
from unittest.mock import MagicMock, patch

# [MILESTONE 1 - Track Task 1 Proof]
# Verify that the simulation infra is resilient to missing broker packages

@pytest.fixture
def broker_disabled():
    """Force brokers into disabled mode via environment."""
    with patch.dict(os.environ, {"DISABLE_RABBITMQ": "1", "DISABLE_KAFKA": "1"}):
        yield

def test_rabbitmq_isolation_when_package_missing(broker_disabled):
    """Prove that get_rabbitmq returns None and doesn't crash even if pika is 'missing'."""
    # Simulate pika being missing by patching the module in sys.modules to None or raising ImportError
    with patch("src.api.rabbitmq_client.HAS_PIKA", False), \
         patch("src.api.rabbitmq_client.pika", None):
        
        from src_legacy.api.rabbitmq_client import get_rabbitmq, is_rabbitmq_disabled
        
        assert is_rabbitmq_disabled() is True
        assert get_rabbitmq() is None

def test_kafka_isolation_when_package_missing(broker_disabled):
    """Prove that get_kafka_producer returns None and doesn't crash even if confluent_kafka is 'missing'."""
    with patch("src.api.kafka_client.HAS_KAFKA", False), \
         patch("src.api.kafka_client.Producer", None):
        
        from src_legacy.api.kafka_client import get_kafka_producer, is_kafka_disabled
        
        assert is_kafka_disabled() is True
        assert get_kafka_producer() is None

def test_worker_pool_fallback_to_inline(broker_disabled):
    """Prove that WorkerPool falls back to inline execution when brokers are disabled."""
    from src_legacy.engine.worker_pool import WorkerPool
    from src_legacy.config import SimulationConfig
    from src_legacy.ai.brain import AIBrain
    from src_legacy.platform.rng import DeterministicRNG
    from src_legacy.core.gameplay.faction import FactionRegistry
    
    config = SimulationConfig(num_workers=4) # Request multiple workers
    rng = DeterministicRNG(42)
    brain = AIBrain(config, rng, FactionRegistry.default())
    
    # We expect this to NOT connect to RabbitMQ and set _channel to None
    with patch("src.api.rabbitmq_client.get_rabbitmq", return_value=None):
        pool = WorkerPool(config, brain, rng)
        assert pool._channel is None
        
        # Verify it uses _think (which is called by _dispatch_inline)
        mock_entities = [MagicMock(id=1)]
        mock_entities[0].combat.hp = 100
        mock_entities[0].combat.max_hp = 100
        mock_entities[0].mind.routine.hunger_level = 0.0
        mock_entities[0].mind.emotion.panic = 0.0
        
        mock_snapshot = MagicMock()
        mock_snapshot.entities = {1: mock_entities[0]}
        mock_snapshot.tick = 0
        mock_action_queue = MagicMock()
        
        with patch.object(AIBrain, "decide", return_value=(0, MagicMock())) as mock_decide:
             pool.dispatch(mock_entities, mock_snapshot, mock_action_queue)
             # If it falls back to inline, it will call _think, which calls brain.decide
             mock_decide.assert_called()

def test_persistence_phase_broker_resilience(broker_disabled):
    """Prove that PersistencePhase skips broker publishing when disabled."""
    from src_legacy.engine.phases.persistence import PersistencePhase
    from src_legacy.core.models.world_state import WorldState
    from src_legacy.core.world.grid import Grid
    from src_legacy.platform.spatial_hash import SpatialHash
    
    grid = Grid(10, 10)
    spatial = SpatialHash(10)
    world = WorldState(seed=42, grid=grid, spatial_index=spatial)
    
    phase = PersistencePhase()
    
    # Use a MagicMock for context to provide only necessary fields
    ctx = MagicMock()
    ctx.world = world
    ctx.config = MagicMock()
    ctx.tick_applied = []
    ctx.tick_events = []
    
    # Mock Redis to ensure it doesn't return and stop execution before Kafka part
    with patch("src.api.redis_client.get_sync_redis") as mock_redis, \
         patch("src.api.kafka_client.get_kafka_producer", return_value=None) as mock_get_kafka:
        
        # Make Redis return a mock so it proceeds past the first return
        mock_redis.return_value = MagicMock()
        
        # Should not crash and should check for kafka producer
        phase.execute(ctx)
        mock_get_kafka.assert_called() # Now it should be reached
