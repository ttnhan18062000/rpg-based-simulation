import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
from src.core.models import Vector2, FloatVector2
from src.ai.flow_fields import FlowField, FlowFieldManager

class MockGrid:
    def __init__(self, width, height, towns=None, camps=None):
        self.width = width
        self.height = height
        self.towns = towns or []
        self.camps = camps or []

    def get(self, pos):
        return 0 # Material.FLOOR or any default

    def is_town(self, pos):
        return (pos.x, pos.y) in self.towns

    def is_camp(self, pos):
        return (pos.x, pos.y) in self.camps

    def is_walkable(self, pos):
        return True

def test_bilinear_interpolation_basic():
    # 10x10 field
    ff = FlowField(Vector2(9, 9), 10, 10)
    # Target is (9,9). At (1,1), (2,1), (1,2), (2,2) we point roughly SE (1,1)
    # Let's manually set vectors to simplify
    ff.vectors[1*10 + 1] = (1, 0)   # (1,1) -> Right
    ff.vectors[1*10 + 2] = (0, 1)   # (2,1) -> Down
    ff.vectors[2*10 + 1] = (1, 1)   # (1,2) -> SE
    ff.vectors[2*10 + 2] = (1, 0)   # (2,2) -> Right
    
    # At (1.5, 1.5), should be an average
    v = ff.get_vector(FloatVector2(1.5, 1.5))
    assert v is not None
    assert isinstance(v, FloatVector2)
    # Weights are all 0.25 (center of 4 nodes)
    # vx = (1*0.25 + 0*0.25 + 1*0.25 + 1*0.25) = 0.75
    # vy = (0*0.25 + 1*0.25 + 1*0.25 + 0*0.25) = 0.5
    # Result should be normalized (0.75, 0.5)
    assert v.x > 0 and v.y > 0
    assert abs(v.x / v.y - 1.5) < 0.1 # 0.75 / 0.5 = 1.5

def test_static_target_caching():
    manager = FlowFieldManager()
    grid = MockGrid(10, 10, towns=[(5, 5)])
    target = Vector2(5, 5)
    
    # 1. Get field at tick 100
    ff1 = manager.get_flow_field(target, grid, current_tick=100)
    
    # 2. Get again at tick 200 (well past default TTL of 5)
    # Since it's a TOWN, it should still be ff1
    ff2 = manager.get_flow_field(target, grid, current_tick=200)
    assert ff1 is ff2

def test_moving_target_ttl():
    manager = FlowFieldManager()
    grid = MockGrid(10, 10) # No towns
    target = Vector2(3, 3)
    
    # 1. Get field at tick 100
    ff1 = manager.get_flow_field(target, grid, current_tick=100)
    
    # 2. Get again at tick 104 (within TTL)
    ff2 = manager.get_flow_field(target, grid, current_tick=104)
    assert ff1 is ff2
    
    # 3. Get again at tick 106 (past TTL)
    ff3 = manager.get_flow_field(target, grid, current_tick=106)
    assert ff1 is not ff3
