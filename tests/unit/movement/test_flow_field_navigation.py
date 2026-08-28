import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, NavigationComponent, CombatComponent, IdentityComponent
from src.engine.movement import MovementSystem
from src.core.builder import V2EntityBuilder
from src.systems.world_systems.navigation import FlowFieldService

def test_flow_field_long_distance():
    # Observer at (0, 0)
    entity = (V2EntityBuilder(1)
              .kind("hero")
              .location(0.0, 0.0)
              .combat(readiness=100.0)
              .navigation(target=(100.0, 100.0))
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
              .location(0.0, 0.0)
              .combat(readiness=100.0)
              .navigation(target=(10.0, 5.0))
              .build())
    
    # Setup Target nearby
    state = AuthoritativeState(tick=100, seed=42, town_center=(100.0, 100.0), entities={1: entity})
    
    # Resolve move
    updates = MovementSystem.resolve_move(state, entity, (10.0, 5.0))
    
    up = updates[1]
    # Local fallback: (abs(dx) > abs(dy)) -> (1, 0)
    assert up.new_position == (1.0, 0.0)
    
    print(f"\nSuccessfully verified Local Navigation fallback: {up.new_position}")


def test_get_flow_direction_town_uses_real_town_center_not_hardcoded_anchor():
    """FlowFieldService.get_flow_direction(target_kind='TOWN', ...) must steer toward the real
    compiled state.town_center, not the hardcoded ANCHORS['TOWN'] waypoints (TCK-20260824-TOWN-
    CENTER-POINTER-FIX). Uses a town_center distinct from both (100,100) and (200,50) so the
    result can only be explained by reading state.town_center."""
    state = AuthoritativeState(tick=0, seed=1, town_center=(300.0, 100.0), entities={})

    direction = FlowFieldService.get_flow_direction((0.0, 0.0), "TOWN", state)

    assert direction is not None
    dx, dy = direction
    # (300, 100) normalized from origin is (0.9487, 0.3162) -- distinct from the direction
    # either hardcoded anchor would produce ((100,100) -> (0.707, 0.707), (200,50) -> (0.970,
    # 0.243)), so this result can only be explained by reading the real state.town_center.
    assert 0.94 < dx < 0.96
    assert 0.31 < dy < 0.32
