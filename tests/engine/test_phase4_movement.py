import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, NavigationComponent, CombatComponent
from src.core.movement_modes import MovementMode
from src.core.updates import StateUpdate, EntityUpdate, NavigationUpdate
from src.engine.movement import MovementSystem
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.core.builder import V2EntityBuilder

def test_movement_wait_and_reroute():
    # Setup: Hero blocked by a HOLD monster
    hero = (V2EntityBuilder(1)
            .kind("HERO")
            .location(5, 5)
            .combat(readiness=100.0)
            .target((7, 5))
            .build())
    
    monster = (V2EntityBuilder(2)
               .kind("MONSTER")
               .location(6, 5)
               .with_navigation_v2(mode=MovementMode.HOLD)
               .build())
    
    # Block BOTH sidesteps (5,4 and 5,6)
    wall1 = (V2EntityBuilder(3).kind("OBSTACLE").location(5, 4).build())
    wall2 = (V2EntityBuilder(4).kind("OBSTACLE").location(5, 6).build())
    
    state = AuthoritativeState(entities={1: hero, 2: monster, 3: wall1, 4: wall2}, tick=0, seed=123)
    
    # 1. First attempt: Should wait and increment wait_count
    updates = MovementSystem.resolve_move(state, hero, (6, 5))
    assert 1 in updates
    hero_upd = updates[1]
    assert hero_upd.new_position is None # Didn't move
    assert hero_upd.navigation.wait_count_delta == 1
    
    # Apply update to simulate next tick
    hero = replace(hero, navigation=replace(hero.navigation, wait_count=1))
    state = replace(state, entities={1: hero, 2: monster, 3: wall1, 4: wall2})
    
    # 2. Second attempt: Still blocked, wait_count should become 2
    updates = MovementSystem.resolve_move(state, hero, (6, 5))
    assert updates[1].navigation.wait_count_delta == 1 # 1+1 = 2
    
    # 3. Third attempt (Wait threshold reached): Should try reroute (e.g. move to 4,5)
    hero = replace(hero, navigation=replace(hero.navigation, wait_count=2))
    state = replace(state, entities={1: hero, 2: monster, 3: wall1, 4: wall2})
    
    updates = MovementSystem.resolve_move(state, hero, (6, 5))
    assert updates[1].new_position == (4, 5) # Rerouted to the only free neighbor (4,5)
    assert updates[1].navigation.wait_count_delta == -2 # Reset wait count on success

def test_anti_oscillation():
    # Setup: Hero moving between two tiles
    hero = (V2EntityBuilder(1)
            .kind("HERO")
            .location(5, 5)
            .combat(readiness=100.0)
            .with_navigation_v2(last_pos=(6, 5))
            .build())
    
    state = AuthoritativeState(entities={1: hero}, tick=0, seed=123)
    
    # Moving back to last_position should trigger oscillation count
    updates = MovementSystem.resolve_move(state, hero, (6, 5))
    assert updates[1].navigation.oscillation_count_delta == 1
    
    # If oscillation too high, should trigger replan
    hero = (V2EntityBuilder(1)
            .kind("HERO")
            .location(5, 5)
            .combat(readiness=100.0)
            .with_navigation_v2(last_pos=(6, 5), oscillation_count=3)
            .build())
    state = replace(state, entities={1: hero})
    
    updates = MovementSystem.resolve_move(state, hero, (6, 5))
    assert updates[1].navigation.clear_target is True # Replan: clear target
    assert updates[1].navigation.oscillation_count_delta == -3 # Reset
    assert updates[1].new_position is None # Stop moving
