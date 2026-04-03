import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
import pickle
from unittest.mock import MagicMock
from src.core.world.grid import Grid
from src.core.models.enums import Material
from src.core.entities.entity import Entity, Vector2
from src.workers.ai_worker_daemon import AIWorkerDaemon
from src.core.models.snapshot import Snapshot
from src.utils.serialization import SimulationSerializer

def test_grid_bytearray_correctness():
    """Verify Grid correctly stores and retrieves materials using bytearray and cache."""
    g = Grid(10, 10)
    pos = Vector2(x=5, y=5)
    
    # Initial state (default is FLOOR=0)
    assert g.get(pos) == Material.FLOOR
    
    # Set to WALL=1
    g.set(pos, Material.WALL)
    assert g.get(pos) == Material.WALL
    assert g.get_xy(5, 5) == Material.WALL
    
    # Set to WATER=2
    g.set(pos, Material.WATER)
    assert g.get(pos) == Material.WATER
    
    # Out of bounds
    assert g.get(Vector2(x=-1, y=0)) == Material.WALL
    assert g.get_xy(10, 10) == Material.WALL

def test_grid_copy_is_not_shared():
    """Verify Grid.copy() duplicates the bytearray data."""
    g1 = Grid(5, 5)
    pos = Vector2(x=2, y=2)
    g1.set(pos, Material.WALL)
    
    g2 = g1.copy()
    assert g2.get(pos) == Material.WALL
    
    # Modify g2, g1 should remain unchanged
    g2.set(pos, Material.WATER)
    assert g2.get(pos) == Material.WATER
    assert g1.get(pos) == Material.WALL

def test_entity_copy_shallow_vs_refs():
    """Verify Entity.copy() is shallow for aspects but produces a new Entity object."""
    e1 = Entity(id=1, kind="hero")
    e1.spatial.pos = Vector2(x=10, y=10)
    
    e2 = e1.copy()
    assert e2.id == e1.id
    assert e2 is not e1
    
    # Post-optimization: aspects are shallow copied (references remain same)
    # BUT wait! If I modify e2.spatial.pos, does it affect e1.spatial.pos?
    # e1.spatial.pos is a Vector2 (Pydantic model). 
    # model_copy(deep=False) copies the reference to the Vector2 object.
    
    e2.spatial.pos = Vector2(x=20, y=20)
    assert e1.spatial.pos.x == 10  # e1 remains at (10,10) because we REPLACED the reference in e2
    
    # AOA Stabilization: Aspect copies are now DEEP to ensure state isolation.
    e1.mind.perception.terrain_memory[(0,0)] = 1
    assert (0,0) not in e2.mind.perception.terrain_memory 
    
    # This confirms deep isolation as intended for AOA Pillar 1.

def test_ai_worker_batch_processing_logic():
    """Verify AIWorkerDaemon correctly handles a batch of tasks."""
    # Mocking necessary parts
    daemon = AIWorkerDaemon.__new__(AIWorkerDaemon) # Skip __init__
    daemon._logger = MagicMock()
    daemon.brain = MagicMock()
    daemon.current_tick = 10
    
    # Mock snapshot
    entities = {1: Entity(id=1, kind="hero"), 2: Entity(id=2, kind="mob")}
    daemon.current_snapshot = MagicMock(entities=entities, tick=10)
    
    # Mock brain decision
    from src.actions.base import ActionProposal
    from src.core.models.enums import ActionType, AIState
    proposal = ActionProposal(actor_id=1, verb=ActionType.REST)
    daemon.brain.decide.return_value = (AIState.WANDER, proposal)
    
    # Mock RabbitMQ channel
    ch = MagicMock()
    method = MagicMock(delivery_tag=1)
    
    # Create a batch task
    batch_task = {
        "tick": 10,
        "entity_ids": [1, 2]
    }
    body = SimulationSerializer.dumps(batch_task)
    
    # Mock _send_batch_result
    daemon._send_batch_result = MagicMock()
    
    # Run on_task
    daemon.on_task(ch, method, None, body)
    
    # Verify processing
    assert daemon.brain.decide.call_count == 2
    daemon._send_batch_result.assert_called_once()
    args, _ = daemon._send_batch_result.call_args
    tick, results = args
    assert tick == 10
    assert len(results) == 2
    assert results[0]["entity_id"] == 1
    assert results[1]["entity_id"] == 2
    
    # Verify ack
    ch.basic_ack.assert_called_once_with(delivery_tag=1)

if __name__ == "__main__":
    pytest.main([__file__])
