import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


import pytest
from unittest.mock import MagicMock, patch
from src.core.entities.entity import Entity, Vector2
from src.ai.states.base import propose_move_toward
from src.core.models.enums import Faction, EntityRole

class MockGrid:
    def __init__(self, width=100, height=100):
        self.width = width
        self.height = height
    def is_town(self, pos): return pos == Vector2(90, 90)
    def is_camp(self, pos): return False
    def is_walkable(self, pos): return True
    def get(self, pos): return 0 # Material.FLOOR

class MockSnapshot:
    def __init__(self):
        self.tick = 100
        self.grid = MockGrid()
        self.entities = {}
    def nearby_entity_ids(self, x, y, r): return []

def test_navigation_uses_flow_field_for_far_town():
    actor = Entity(id=1, kind="hero")
    actor.spatial.pos = Vector2(10, 10)
    target = Vector2(90, 90) # Far town
    
    snapshot = MockSnapshot()
    
    with patch("src.ai.flow_fields.FlowFieldManager.get_flow_field") as mock_get_ff:
        mock_ff = MagicMock()
        mock_ff.get_vector.return_value = MagicMock(x=1, y=0)
        mock_get_ff.return_value = mock_ff
        
        with patch("src.ai.pathfinding.Pathfinder.find_path") as mock_find_path:
            proposal = propose_move_toward(actor, target, snapshot, "test")
            
            # Should have used Flow Field
            assert "Flow Field" in proposal.reason
            mock_get_ff.assert_called_with(target, snapshot.grid, 100)
            mock_find_path.assert_not_called()

def test_navigation_uses_astar_for_near_target():
    actor = Entity(id=2, kind="hero")
    actor.spatial.pos = Vector2(10, 10)
    target = Vector2(15, 15) # Near target (dist = 10)
    
    snapshot = MockSnapshot()
    # Ensure target is NOT a town for this test
    snapshot.grid.is_town = lambda p: False
    
    with patch("src.ai.flow_fields.FlowFieldManager.get_flow_field") as mock_get_ff:
        with patch("src.ai.pathfinding.Pathfinder.find_path") as mock_find_path:
            mock_find_path.return_value = [Vector2(11, 10)]
            
            proposal = propose_move_toward(actor, target, snapshot, "test")
            
            # Should NOT have used Flow Field (dist <= 10 or not a shared target)
            assert "A*" in proposal.reason
            mock_get_ff.assert_not_called()
            mock_find_path.assert_called()

def test_navigation_uses_flow_field_for_world_boss():
    actor = Entity(id=3, kind="hero")
    actor.spatial.pos = Vector2(10, 10)
    target = Vector2(90, 90) # Far world boss
    
    snapshot = MockSnapshot()
    snapshot.grid.is_town = lambda p: False
    
    # Mock World Boss entity at target
    boss = Entity(id=999, kind="boss")
    boss.spatial.pos = target
    boss.identity.role = EntityRole.WORLD_BOSS
    snapshot.entities[999] = boss
    snapshot.nearby_entity_ids = lambda x, y, r: [999]
    
    with patch("src.ai.flow_fields.FlowFieldManager.get_flow_field") as mock_get_ff:
        mock_ff = MagicMock()
        mock_ff.get_vector.return_value = MagicMock(x=1, y=0)
        mock_get_ff.return_value = mock_ff
        
        with patch("src.ai.pathfinding.Pathfinder.find_path") as mock_find_path:
            proposal = propose_move_toward(actor, target, snapshot, "test")
            
            # Should have used Flow Field for World Boss
            assert "Flow Field" in proposal.reason
            mock_get_ff.assert_called()
