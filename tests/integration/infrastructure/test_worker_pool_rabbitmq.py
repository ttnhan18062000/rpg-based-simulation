import sys
import os
import pickle
from unittest.mock import MagicMock, patch

from src.engine.worker_pool import WorkerPool
from unittest.mock import MagicMock, patch

from src.core.models.enums import AIState
from src.core.models.vectors import Vector2
from src.core.world.grid import Grid
from src.config import SimulationConfig
from src.engine.action_queue import ActionQueue
from src.engine.worker_pool import WorkerPool
from src.core.models.snapshot import Snapshot
from src.core.entities.entity import Entity
from src.core.aspects.spatial import SpatialAspect
from src.platform.rng import DeterministicRNG

def test_worker_pool_rabbitmq_dispatch(monkeypatch):
    """Test that WorkerPool interacts with pika channels exactly as designed."""
    # 1. Setup mock infrastructure
    config = SimulationConfig(num_workers=4, worker_timeout_seconds=2.0)
    mock_brain = MagicMock()
    rng = DeterministicRNG(42)
    
    mock_conn = MagicMock()
    mock_channel = MagicMock()
    mock_conn.channel.return_value = mock_channel
    
    # Need to simulate the connection return
    with patch("src.engine.worker_pool.get_rabbitmq", return_value=mock_conn):
        pool = WorkerPool(config, mock_brain, rng)
        
        assert pool._channel == mock_channel
        
        # 2. Setup mock data
        e1 = Entity(id=101, kind="goblin", spatial=SpatialAspect(pos=Vector2(0,0)))
        e2 = Entity(id=202, kind="hero", spatial=SpatialAspect(pos=Vector2(1,1)))
        
        entities = [e1, e2]
        
        grid = Grid(10, 10)
        mock_snapshot = Snapshot(
            tick=42, seed=1, entities={}, grid=grid, ground_items={},
            camps=(), buildings=(), resource_nodes=(), treasure_chests=(), regions=(),
        )
        
        action_queue = ActionQueue()
        
        # 3. Simulate RabbitMQ basic_get responses for the 'ai_results' queue
        # The pool expects 2 responses because len(entities) == 2.
        # basic_get returns (method_frame, header_frame, body)
        mock_method_frame = MagicMock()
        
        # Fake Action Proposals for results
        fake_proposal_1 = "prop_101"
        fake_proposal_2 = "prop_202"
        
        import json
        call_count = 0
        def side_effect_basic_get(*args, **kwargs):
            nonlocal call_count
            if call_count == 0:
                body = json.dumps({
                    "tick": 42, 
                    "results": [
                        {"entity_id": 101, "proposal": {"actor_id": 101, "verb": 0, "new_ai_state": 1}},
                        {"entity_id": 202, "proposal": {"actor_id": 202, "verb": 0, "new_ai_state": 1}}
                    ]
                }).encode("utf-8")
                call_count += 1
                return mock_method_frame, None, body
            return None, None, None
            
        mock_channel.basic_get.side_effect = side_effect_basic_get
        
        # 4. Execute dispatch
        pool.dispatch(entities, mock_snapshot, action_queue)
        
        # 5. Assertions
        # Should have published 1 snapshot + 1 batch task (AOA Phase 6 optimization)
        # IF IT FAILS HERE, PRINT EXCEPTION
             
        assert mock_channel.basic_publish.call_count == 2
        
        # Ensure our results were collected into the ActionQueue!
        results = action_queue.drain()
        assert len(results) == 2
        # Use simple AIState check since we moved from strings to objects
        assert any(r.new_ai_state == 1 for r in results)
