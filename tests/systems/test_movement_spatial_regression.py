import pytest
from dataclasses import replace
from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, 
    CombatComponent, InventoryComponent, StrategicComponent, 
    BiologicalComponent, SocialComponent, NavigationComponent,
    LifecycleComponent, EntityRole
)
from src.core.movement_modes import MovementMode
from src.engine.movement import MovementSystem
from src.core.updates import StateUpdate, EntityUpdate

def create_mock_entity(e_id, pos, faction=1, role=EntityRole.MONSTER, mode=MovementMode.WANDER):
    return EntityState(
        id=e_id,
        kind="actor",
        position=pos,
        identity=IdentityComponent(role=role, faction=faction),
        combat=CombatComponent(hp=100, max_hp=100, alive=True),
        inventory=InventoryComponent(),
        strategic=StrategicComponent(),
        biological=BiologicalComponent(),
        social=SocialComponent(),
        navigation=NavigationComponent(movement_mode=mode),
        lifecycle=LifecycleComponent(),
        active=True
    )

def test_sidestep_recovery():
    """Verify that if forward move is blocked, actor tries sidestepping."""
    # Actor at (1,1) tries to move to (2,1). (2,1) is blocked.
    actor = create_mock_entity(1, (1.0, 1.0))
    blocker = create_mock_entity(2, (2.0, 1.0))
    
    # Grid:
    # (1,0) [ ]
    # (1,1) [A] -> (2,1) [B]
    # (1,2) [ ]
    # Sidesteps: (1,0), (1,2)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: actor, 2: blocker})
    
    updates = MovementSystem.resolve_move(state, actor, (2.0, 1.0))
    
    # Should have sidestepped to (1,0) or (1,2)
    new_pos = updates[1].new_position
    assert new_pos in [(1.0, 0.0), (1.0, 2.0)]
    assert updates[1].moved_this_tick is True

def test_yielding_recovery():
    """Verify that high-priority entity can force a low-priority entity to yield."""
    hero = create_mock_entity(1, (1.0, 1.0), role=EntityRole.HERO)
    monster = create_mock_entity(2, (2.0, 1.0), role=EntityRole.MONSTER)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: monster})
    
    # Hero tries to move to monster's tile. Block sidesteps (1,0) and (1,2)
    s1 = create_mock_entity(3, (1.0, 0.0))
    s2 = create_mock_entity(4, (1.0, 2.0))
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: monster, 3: s1, 4: s2})
    
    updates = MovementSystem.resolve_move(state, hero, (2.0, 1.0))
    
    # Hero should succeed
    assert updates[1].new_position == (2.0, 1.0)
    # Monster should have yielded
    assert 2 in updates
    assert updates[2].new_position != (2.0, 1.0)
    assert updates[2].navigation.failure_reason == "YIELDED"

def test_hold_mode_refusal():
    """Verify that HOLD mode prevents yielding."""
    hero = create_mock_entity(1, (1.0, 1.0), role=EntityRole.HERO)
    monster = create_mock_entity(2, (2.0, 1.0), role=EntityRole.MONSTER, mode=MovementMode.HOLD)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: monster})
    
    # Hero tries to move to monster's tile
    updates = MovementSystem.resolve_move(state, hero, (2.0, 1.0))
    
    # Hero should fail (because monster won't yield and no sidesteps possible? wait, hero might sidestep)
    # To ensure hero fails, we block sidesteps
    wall_1_0 = create_mock_entity(3, (1.0, 0.0))
    wall_1_2 = create_mock_entity(4, (1.0, 2.0))
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: monster, 3: wall_1_0, 4: wall_1_2})
    
    updates = MovementSystem.resolve_move(state, hero, (2.0, 1.0))
    
    assert updates[1].new_position is None
    assert updates[1].navigation.failure_reason == "OCCUPANCY_VIOLATION"

def test_retreat_evasion_skips_oa():
    """Verify that RETREAT + EVASIVE skips opportunity attacks."""
    hero = create_mock_entity(1, (1.0, 1.0), role=EntityRole.HERO, mode=MovementMode.RETREAT)
    # Set evasive style
    hero = replace(hero, combat=replace(hero.combat, action_style=2)) # 2 = EVASIVE
    
    monster = create_mock_entity(2, (2.0, 1.0), faction=2) # Different faction
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: monster})
    
    # Hero moves away from monster to (0,1)
    updates = MovementSystem.resolve_move(state, hero, (0.0, 1.0), mode=MovementMode.RETREAT)
    
    # Should not have combat update in hero's entity update
    assert updates[1].combat is None
    assert updates[1].new_position == (0.0, 1.0)

def test_normal_move_triggers_oa():
    """Verify that WANDER move triggers opportunity attacks when engaged."""
    hero = create_mock_entity(1, (1.0, 1.0), role=EntityRole.HERO, mode=MovementMode.WANDER)
    monster = create_mock_entity(2, (2.0, 1.0), faction=2)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: monster})
    
    # Hero moves away to (0,1)
    updates = MovementSystem.resolve_move(state, hero, (0.0, 1.0), mode=MovementMode.WANDER)
    
    # Should have combat update (Damage taken from OA)
    assert updates[1].combat is not None
    assert updates[1].combat.damage_taken > 0
