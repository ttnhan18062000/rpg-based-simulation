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
    # Flow direction from (0,0) to (100,100) is (0.707, 0.707): an exact tie, which takes the y axis like the local step.
    assert up.new_position == (0.0, 1.0)

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


def test_flow_step_is_a_tile_step_along_the_dominant_axis():
    """A flow step moves one tile on the vector's dominant axis (ties take y), so positions never leave the tile grid."""
    from src.systems.world_systems.navigation import NavigationSystem

    def step(pos, town):
        entity = V2EntityBuilder(1).kind("hero").location(*pos).build()
        state = AuthoritativeState(tick=0, seed=1, town_center=town, entities={1: entity})
        return NavigationSystem.get_next_step(entity, town, state)

    assert step((0.0, 0.0), (300.0, 100.0)) == (1.0, 0.0)   # x dominant
    assert step((0.0, 0.0), (100.0, 300.0)) == (0.0, 1.0)   # y dominant
    assert step((200.0, 200.0), (100.0, 100.0)) == (200.0, 199.0)  # tie, both negative: y axis
    assert step((300.0, 0.0), (0.0, 20.0)) == (299.0, 0.0)   # negative x dominant


def test_flow_steps_always_land_on_whole_tiles_and_are_deterministic():
    """From any whole tile, repeated flow steps toward a far town centre never leave the tile grid, and repeat exactly."""
    from src.systems.world_systems.navigation import NavigationSystem

    town = (333.0, 217.0)

    def walk(start, n):
        entity = V2EntityBuilder(1).kind("hero").location(*start).build()
        pos, path = start, []
        for _ in range(n):
            e = V2EntityBuilder(1).kind("hero").location(*pos).build()
            state = AuthoritativeState(tick=0, seed=1, town_center=town, entities={1: e})
            pos = NavigationSystem.get_next_step(e, town, state)
            path.append(pos)
        return path

    path = walk((3.0, 5.0), 60)
    assert all(x == int(x) and y == int(y) for x, y in path)
    assert path == walk((3.0, 5.0), 60)
    assert all(abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1 for a, b in zip([(3.0, 5.0)] + path, path))
