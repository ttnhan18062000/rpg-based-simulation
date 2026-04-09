import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


from src.utils.serialization import SimulationSerializer
from src.core.models.snapshot import Snapshot
import json
from unittest.mock import MagicMock, patch
from src.core.models.enums import AIState
from src.core.entities.entity import Entity, Vector2
from src.core.world.grid import Grid
from src.config import SimulationConfig
from src.engine.action_queue import ActionQueue
from src.engine.worker_pool import WorkerPool

def test_worker_pool_rabbitmq_dispatch(monkeypatch):
    """Test that WorkerPool interacts with pika channels exactly as designed."""
    # 1. Setup mock infrastructure
    config = SimulationConfig(num_workers=4, worker_timeout_seconds=2.0)
    mock_brain = MagicMock()
    
    mock_conn = MagicMock()
    mock_channel = MagicMock()
    mock_conn.channel.return_value = mock_channel
    
    # Need to simulate the connection return
    with patch("src.engine.worker_pool.get_rabbitmq", return_value=mock_conn):
        from src.platform.rng import DeterministicRNG
        rng = DeterministicRNG(seed=42)
        pool = WorkerPool(config, mock_brain, rng)
        
        assert pool._channel == mock_channel
        
        # 2. Setup mock data
        e1 = Entity(id=101, kind="goblin", pos=Vector2(0,0))
        e2 = Entity(id=202, kind="hero", pos=Vector2(1,1))
        
        entities = [e1, e2]
        
        grid = Grid(10, 10)
        mock_snapshot = Snapshot(
            tick=42, seed=1, entities={}, grid=grid, ground_items={},
            camps=(), buildings=(), resource_nodes=(), treasure_chests=(), regions=(),
        )
        
        action_queue = ActionQueue()
        
        # 3. Simulate RabbitMQ basic_get responses for the 'ai_results' queue
        # The pool now expects 1 response (BATCH) containing all results.
        mock_method_frame = MagicMock()
        
        from src.core.models.enums import ActionType
        # Fake Action Proposals for results
        fake_proposal_1 = {"actor_id": 101, "verb": ActionType.MOVE, "reason": "test"}
        fake_proposal_2 = {"actor_id": 202, "verb": ActionType.ATTACK, "reason": "test"}
        
        def side_effect_basic_get(*args, **kwargs):
            results = [
                {"entity_id": 101, "proposal": fake_proposal_1},
                {"entity_id": 202, "proposal": fake_proposal_2}
            ]
            body = SimulationSerializer.dumps({"tick": 42, "results": results})
            return mock_method_frame, None, body
            
        mock_channel.basic_get.side_effect = side_effect_basic_get
        
        # 4. Execute dispatch
        pool.dispatch(entities, mock_snapshot, action_queue)
        
        # 5. Assertions
        # Should have published 1 snapshot + 1 batch task
        assert mock_channel.basic_publish.call_count == 2
        
        # First call: the snapshot to 'ai_snapshots' fanout
        call_1 = mock_channel.basic_publish.call_args_list[0]
        assert call_1.kwargs["exchange"] == "ai_snapshots"
        
        # Second call: the batch task to 'ai_tasks'
        call_2 = mock_channel.basic_publish.call_args_list[1]
        assert call_2.kwargs["exchange"] == ""
        assert call_2.kwargs["routing_key"] == "ai_tasks"
        batch_task = SimulationSerializer.loads(call_2.kwargs["body"])
        assert batch_task["tick"] == 42
        assert set(batch_task["entity_ids"]) == {101, 202}
        
        # Ensure our results were collected into the ActionQueue!
        results = action_queue.drain()
        assert len(results) == 2
        # Proposal might be deserialized as dict if not validated, but here we check it's present
        proposals = [r if isinstance(r, str) else r.verb for r in results]
        assert len(proposals) == 2
