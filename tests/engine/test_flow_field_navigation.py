import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, NavigationComponent, CombatComponent, IdentityComponent
from src.engine.movement import MovementSystem
from src.core.builder import V2EntityBuilder

def test_flow_field_long_distance():
    # Observer at (0, 0)
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .at((0.0, 0.0))
              .readiness(100.0)
              .target((100.0, 100.0))
              .build())
    
    # Setup Town far away
    state = AuthoritativeState(tick=100, seed=42, town_center=(100.0, 100.0), entities={1: entity})
    
    # Resolve move
    updates = MovementSystem.resolve_move(state, entity, (100.0, 100.0))
    
    up = updates[1]
    # Flow direction from (0,0) to (100,100) is (0.707, 0.707) approx
    
    assert up.new_position is not None
    nx, ny = up.new_position
    
    # Since dist > 50, it uses FlowField
    # Vector (100, 100) normalized is (0.707, 0.707)
    assert 0.7 < nx < 0.8
    assert 0.7 < ny < 0.8
    
    print(f"\nSuccessfully verified Flow Field navigation to Town: {up.new_position}")

def test_local_navigation_fallback():
    # Observer at (0, 0)
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .at((0.0, 0.0))
              .readiness(100.0)
              .target((10.0, 5.0))
              .build())
    
    # Setup Target nearby
    state = AuthoritativeState(tick=100, seed=42, town_center=(100.0, 100.0), entities={1: entity})
    
    # Resolve move
    updates = MovementSystem.resolve_move(state, entity, (10.0, 5.0))
    
    up = updates[1]
    # Local fallback: (abs(dx) > abs(dy)) -> (1, 0)
    assert up.new_position == (1.0, 0.0)
    
    print(f"\nSuccessfully verified Local Navigation fallback: {up.new_position}")
