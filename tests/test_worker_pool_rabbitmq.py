import pickle
from unittest.mock import MagicMock, patch

from src.core.enums import AIState
from src.core.models import Entity, Vector2
from src.core.grid import Grid
from src.config import SimulationConfig
from src.engine.action_queue import ActionQueue
from src.engine.worker_pool import WorkerPool
from src.core.snapshot import Snapshot

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
        pool = WorkerPool(config, mock_brain)
        
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
        # The pool expects 2 responses because len(entities) == 2.
        # basic_get returns (method_frame, header_frame, body)
        mock_method_frame = MagicMock()
        
        # Fake Action Proposals for results
        fake_proposal_1 = "prop_101"
        fake_proposal_2 = "prop_202"
        
        call_count = 0
        def side_effect_basic_get(*args, **kwargs):
            nonlocal call_count
            if call_count == 0:
                body = pickle.dumps({"tick": 42, "entity_id": 101, "proposal": fake_proposal_1})
            elif call_count == 1:
                body = pickle.dumps({"tick": 42, "entity_id": 202, "proposal": fake_proposal_2})
            else:
                return None, None, None
            call_count += 1
            return mock_method_frame, None, body
            
        mock_channel.basic_get.side_effect = side_effect_basic_get
        
        # 4. Execute dispatch
        pool.dispatch(entities, mock_snapshot, action_queue)
        
        # 5. Assertions
        # Should have published 1 snapshot + 2 tasks
        assert mock_channel.basic_publish.call_count == 3
        
        # First layout: the snapshot to 'ai_snapshots' fanout
        call_1 = mock_channel.basic_publish.call_args_list[0]
        assert call_1.kwargs["exchange"] == "ai_snapshots"
        
        # Task 1
        call_2 = mock_channel.basic_publish.call_args_list[1]
        assert call_2.kwargs["exchange"] == ""
        assert call_2.kwargs["routing_key"] == "ai_tasks"
        task1 = pickle.loads(call_2.kwargs["body"])
        assert task1["entity_id"] == 101
        
        # Task 2
        call_3 = mock_channel.basic_publish.call_args_list[2]
        assert call_3.kwargs["routing_key"] == "ai_tasks"
        task2 = pickle.loads(call_3.kwargs["body"])
        assert task2["entity_id"] == 202
        
        # Ensure our results were collected into the ActionQueue!
        results = action_queue.drain()
        assert len(results) == 2
        assert fake_proposal_1 in set(results)
        assert fake_proposal_2 in set(results)
