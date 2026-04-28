
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, NavigationComponent, CombatComponent
from src.core.movement_modes import MovementMode
from src.core.updates import StateUpdate, EntityUpdate, NavigationUpdate
from src.engine.movement import MovementSystem
from src.engine.pipeline import AuthoritativeApplyPipeline

def test_movement_wait_and_reroute():
    # Setup: Hero blocked by a HOLD monster
    hero = EntityState(id=1, kind="HERO", position=(5, 5), readiness=100.0)
    hero = replace(hero, navigation=replace(hero.navigation, target=(7, 5)))
    
    monster = EntityState(id=2, kind="MONSTER", position=(6, 5))
    monster = replace(monster, navigation=replace(monster.navigation, movement_mode=MovementMode.HOLD))
    
    # Block BOTH sidesteps (5,4 and 5,6)
    wall1 = EntityState(id=3, kind="OBSTACLE", position=(5, 4))
    wall2 = EntityState(id=4, kind="OBSTACLE", position=(5, 6))
    
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
    hero = EntityState(id=1, kind="HERO", position=(5, 5), readiness=100.0)
    hero = replace(hero, navigation=replace(hero.navigation, last_position=(6, 5)))
    
    state = AuthoritativeState(entities={1: hero}, tick=0, seed=123)
    
    # Moving back to last_position should trigger oscillation count
    updates = MovementSystem.resolve_move(state, hero, (6, 5))
    assert updates[1].navigation.oscillation_count_delta == 1
    
    # If oscillation too high, should trigger replan
    hero = replace(hero, navigation=replace(hero.navigation, oscillation_count=3, last_position=(6, 5)))
    state = replace(state, entities={1: hero})
    
    updates = MovementSystem.resolve_move(state, hero, (6, 5))
    assert updates[1].navigation.clear_target is True # Replan: clear target
    assert updates[1].navigation.oscillation_count_delta == -3 # Reset
    assert updates[1].new_position is None # Stop moving
