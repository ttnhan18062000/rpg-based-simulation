import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from unittest.mock import MagicMock
from src_legacy.core.models import Vector2, FloatVector2
from src_legacy.core.models.enums import Material
from src_legacy.ai.flow_fields import FlowField, FlowFieldManager

class MockGrid:
    def __init__(self, width, height, data=None):
        self.width = width
        self.height = height
        self.data = data or {}

    def get(self, pos):
        return self.data.get((pos.x, pos.y), Material.FLOOR)

    def is_walkable(self, pos):
        mat = self.get(pos)
        return mat not in (Material.WALL, Material.WATER, Material.LAVA)

def test_flow_field_basic_navigation():
    # Simple 3x3 grid, target at (2,2)
    grid = MockGrid(3, 3)
    manager = FlowFieldManager()
    ff = manager._generate_dijkstra_map(Vector2(2, 2), grid)
    
    # At (0,0), should point toward (1,1) or similar
    v = ff.get_vector(Vector2(0, 0))
    assert v is not None
    # On a simple grid, move should be toward target
    assert v.x >= 0 and v.y >= 0
    assert not (v.x == 0 and v.y == 0)

def test_flow_field_respects_terrain_cost():
    # 5x5 Grid to give more room for detour
    # Target at (4,2)
    # Direct path blocked by high-cost tiles (SWAMP=1.5)
    # Detour path has low-cost tiles (ROAD=0.7)
    
    # (0,2) [Start] -> (1,2)[S] -> (2,2)[S] -> (3,2)[S] -> (4,2)[Target]  (Cost: 1.5*3 + 1.0 = 5.5)
    # Detour: (0,2) -> (0,1)[R] -> (1,1)[R] -> (2,1)[R] -> (3,1)[R] -> (4,1)[R] -> (4,2) (Cost: 0.7*5 + 1.0 = 4.5)
    
    data = {
        (4, 2): Material.FLOOR,
        (1, 2): Material.SWAMP, (2, 2): Material.SWAMP, (3, 2): Material.SWAMP,
        (0, 1): Material.ROAD, (1, 1): Material.ROAD, (2, 1): Material.ROAD, 
        (3, 1): Material.ROAD, (4, 1): Material.ROAD, (0, 2): Material.ROAD
    }
    grid = MockGrid(5, 5, data)
    manager = FlowFieldManager()
    
    # Tick 0
    ff = manager._generate_dijkstra_map(Vector2(4, 2), grid, tick=0)
    
    # From (0,2), should point toward (0,1) or (1,1) [ROAD/Diagonal] 
    # Because (1,1) is closer and (0,1) is on the way.
    v = ff.get_vector(Vector2(0, 2))
    assert v is not None
    # v should have y < 0 (moving up toward road) and x >= 0
    assert v.y < 0
    assert v.x >= 0
    # It should NOT point toward (1,2) [x=1, y=0] which is a swamp
    assert not (v.x > 0.9 and abs(v.y) < 0.1)

def test_flow_field_smoothing_normalization():
    """Verify that get_vector returns a normalized Vector2."""
    grid = MockGrid(5, 5)
    manager = FlowFieldManager()
    ff = manager._generate_dijkstra_map(Vector2(4, 4), grid)
    
    v = ff.get_vector(Vector2(1, 1))
    assert isinstance(v, FloatVector2)
    assert abs(v.length() - 1.0) < 0.001

def test_flow_field_smoothing():
    """Verify that get_vector uses neighbor averaging for smoother curves."""
    grid = MockGrid(5, 5)
    ff = FlowField(Vector2(4, 4), 5, 5, tick=0)
    # Target is (4,4). At (1,1), we might have neighbors pointing different ways.
    # Manually inject neighbor vectors for (1,1) to (2,2)
    ff.vectors[1*5 + 1] = (1, 0) # (1,1)
    ff.vectors[1*5 + 2] = (0, 1) # (2,1)
    ff.vectors[2*5 + 1] = (1, 1) # (1,2)
    ff.vectors[2*5 + 2] = (-1, 0) # (2,2)
    
    # Use off-grid position with FloatVector2 to trigger bilinear interpolation
    v = ff.get_vector(FloatVector2(1.5, 1.5))
    assert isinstance(v, FloatVector2)
    # v should be an average of several vectors, then normalized
    assert abs(v.length() - 1.0) < 0.001
    # It should NOT be any single one of them
    assert not (v.x == 1.0 and v.y == 0.0)
    assert not (v.x == 0.0 and v.y == 1.0)

def test_cache_with_ttl():
    manager = FlowFieldManager()
    grid = MockGrid(10, 10)
    target = Vector2(5, 5)
    
    # 1. Get field
    ff1 = manager.get_flow_field(target, grid, current_tick=100)
    # 2. Get again (should be cached)
    ff2 = manager.get_flow_field(target, grid, current_tick=102)
    assert ff1 is ff2
    
    # 3. Wait for TTL (e.g. 5 ticks)
    ff3 = manager.get_flow_field(target, grid, current_tick=106)
    assert ff3 is not ff1 # Should have been re-generated
