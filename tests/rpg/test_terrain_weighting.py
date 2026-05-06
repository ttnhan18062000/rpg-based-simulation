import pytest
from src.core.state import (
    AuthoritativeState, EntityState, CombatComponent, NavigationComponent,
    TERRAIN_COST
)
from src.engine.movement import MovementSystem
from src.core.enums import ReasonCode
from src.core.movement_modes import MovementMode

def test_terrain_readiness_rejection():
    """
    Test that movement into high-cost terrain is rejected if readiness is insufficient.
    MOUNTAIN cost is 4.0. Entity move_cost is 10.0. Total = 40.0.
    Entity with 20.0 readiness should fail.
    """
    # 1. Setup State with a Mountain tile
    terrain = {(1, 1): "MOUNTAIN"}
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(1, 0)
        .combat(readiness=20.0)
        .combat(move_cost=10.0, alive=True)
        .navigation(mode=MovementMode.WANDER)
        .build())
    
    # 2. Attempt move to (1, 1)
    # Block sidesteps with WALLS to force the high-cost move check
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        terrain=terrain,
        blocked_tiles={(2, 0), (0, 0), (1, -1)} # Block all alternatives
    )
    
    target_pos = (1, 1)
    updates = MovementSystem.resolve_move(state, entity, target_pos)
    
    # 3. Assertions
    ent_upd = updates[1]
    
    assert ent_upd.moved_this_tick is False, f"Move should have failed, but got new_pos={ent_upd.new_position}"
    assert ent_upd.new_position is None
    assert ent_upd.navigation.failure_reason == ReasonCode.ACTION_EXHAUSTION

def test_terrain_readiness_success():
    """
    Test that movement into high-cost terrain succeeds if readiness is sufficient.
    """
    terrain = {(1, 1): "MOUNTAIN"}
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(1, 0)
        .combat(readiness=100.0)
        .combat(move_cost=10.0, alive=True)
        .navigation(mode=MovementMode.WANDER)
        .build())
    
    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={1: entity},
        terrain=terrain
    )
    
    target_pos = (1, 1)
    updates = MovementSystem.resolve_move(state, entity, target_pos)
    
    ent_upd = updates[1]
    assert ent_upd.moved_this_tick is True
    assert ent_upd.new_position == (1, 1)
    assert ent_upd.readiness_delta == -80.0 # (10.0 * 4.0) / 0.5 (WANDER mode)
