import pytest
import json
from unittest.mock import MagicMock, patch
from src.engine.phases.persistence import PersistencePhase
from src.engine.phases.context import EngineContext
from src.core.models.world_state import WorldState
from src.core.world.grid import Grid
from src.core.entities.entity import Entity, Vector2
from src.platform.spatial_hash import SpatialHash

@pytest.fixture(autouse=True)
def mock_infrastructure():
    # Force HAS_REDIS to True for testing logic
    import src.engine.phases.persistence as p
    original_has_redis = p.HAS_REDIS
    p.HAS_REDIS = True
    
    with patch("src.api.redis_client.get_sync_redis") as m:
        yield m.return_value
        
    p.HAS_REDIS = original_has_redis

@pytest.fixture
def persistence():
    return PersistencePhase()

def create_mock_context(world_state):
    ctx = MagicMock(spec=EngineContext)
    ctx.world = world_state
    ctx.config = MagicMock()
    ctx.tick_events = []
    ctx.tick_applied = []
    return ctx

class TestCanonicalStream:
    """Verifies Pillar 5: Canonicalization of simulation Map-Stream."""

    def test_delta_published_to_redis(self, persistence):
        from src.api.redis_client import get_sync_redis
        mock_redis = get_sync_redis()

        # 1. Setup World with one entity
        world = WorldState(seed=0, grid=Grid(10, 10), spatial_index=SpatialHash(10))
        hero = Entity(id=1, kind="hero")
        hero.spatial.pos = Vector2(1,1)
        world.add_entity(hero)
        
        ctx = create_mock_context(world)
        
        # Initial Tick
        persistence.execute(ctx)
        
        # Verify xadd called
        assert mock_redis.xadd.called
        # call_args.args is (stream_name, mapping_dict)
        args = mock_redis.xadd.call_args.args
        assert args[0] == "sim:stream"
        data = args[1]
        assert "payload" in data
        assert "rich" in data
        assert "compact" in data
        
        # Verify isolation: trauma/threat shouldn't be in payload (slim)
        payload = json.loads(data["payload"])
        assert "changed" in payload
        entity_delta = payload["changed"][0]
        assert "hp" in entity_delta
        assert "trauma" not in entity_delta
        assert "threat" not in entity_delta

    def test_movement_produces_delta(self, persistence):
        from src.api.redis_client import get_sync_redis
        mock_redis = get_sync_redis()

        world = WorldState(seed=0, grid=Grid(10, 10), spatial_index=SpatialHash(10))
        hero = Entity(id=1, kind="hero")
        hero.spatial.pos = Vector2(1,1)
        world.add_entity(hero)
        
        ctx = create_mock_context(world)
        
        # Tick 1: Baseline
        persistence.execute(ctx)
        mock_redis.xadd.reset_mock()
        
        # Tick 2: Move hero
        hero.spatial.pos = Vector2(1,2)
        world.tick = 1
        persistence.execute(ctx)
        
        # Verify delta contains change
        assert mock_redis.xadd.called
        args = mock_redis.xadd.call_args.args
        data = args[1]
        payload = json.loads(data["payload"])
        assert len(payload["changed"]) == 1
        assert payload["changed"][0]["y"] == 2

    def test_heartbeat_every_20_ticks(self, persistence):
        from src.api.redis_client import get_sync_redis
        mock_redis = get_sync_redis()

        world = WorldState(seed=0, grid=Grid(10, 10), spatial_index=SpatialHash(10))
        ctx = create_mock_context(world)
        
        # Baseline (Tick 0 pushes initial)
        persistence.execute(ctx)
        mock_redis.xadd.reset_mock()
        
        # Tick 1 (No changes, no heartbeat)
        world.tick = 1
        persistence.execute(ctx)
        assert not mock_redis.xadd.called
        
        # Tick 20 (Heartbeat!)
        world.tick = 20
        persistence.execute(ctx)
        assert mock_redis.xadd.called
        args = mock_redis.xadd.call_args.args
        data = args[1]
        payload = json.loads(data["payload"])
        assert payload["tick"] == 20
        assert payload["changed"] == []
