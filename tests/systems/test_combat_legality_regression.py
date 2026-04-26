import pytest
from dataclasses import replace
from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, 
    CombatComponent, InventoryComponent, StrategicComponent, 
    BiologicalComponent, SocialComponent, NavigationComponent,
    LifecycleComponent, EntityRole
)
from src.engine.combat import CombatResolutionSystem
from src.engine.domain_logic import SimulationDomainLogic

def create_mock_entity(e_id, pos, faction=1, role=EntityRole.MONSTER):
    return EntityState(
        id=e_id,
        kind="actor",
        position=pos,
        readiness=100.0,
        identity=IdentityComponent(role=role, faction=faction),
        combat=CombatComponent(hp=100, max_hp=100, atk=10, def_stat=5, range=1, alive=True),
        inventory=InventoryComponent(),
        strategic=StrategicComponent(),
        biological=BiologicalComponent(),
        social=SocialComponent(),
        navigation=NavigationComponent(),
        lifecycle=LifecycleComponent(),
        properties={},
        active=True
    )

def test_friendly_fire_legality():
    """Verify that attacking an ally is illegal."""
    hero1 = create_mock_entity(1, (1.0, 1.0), faction=1, role=EntityRole.HERO)
    hero2 = create_mock_entity(2, (2.0, 1.0), faction=1, role=EntityRole.HERO)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero1, 2: hero2})
    
    # Hero 1 attacks Hero 2
    updates = SimulationDomainLogic.execute_action(hero1, {"action": "ATTACK", "target_id": 2}, context=state)
    update = updates[hero1.id]
    
    assert update.combat is None
    assert update.navigation.failure_reason == "FRIENDLY_FIRE_ILLEGAL"

def test_range_legality():
    """Verify that attacking out of range is illegal."""
    hero = create_mock_entity(1, (1.0, 1.0), role=EntityRole.HERO)
    monster = create_mock_entity(2, (10.0, 10.0), role=EntityRole.MONSTER, faction=2)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: monster})
    
    # Hero attacks monster (out of range 1)
    updates = SimulationDomainLogic.execute_action(hero, {"action": "ATTACK", "target_id": 2}, context=state)
    update = updates[hero.id]
    
    assert update.combat is None
    assert update.navigation.failure_reason == "OUT_OF_RANGE"

def test_shatter_logic():
    """Verify SHATTER damage bonus (1.5x) against frozen targets."""
    attacker = create_mock_entity(1, (1.0, 1.0))
    defender = create_mock_entity(2, (2.0, 1.0), faction=2)
    # Freeze the defender
    defender = replace(defender, properties={"status_frozen": True})
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})
    
    combat_up = CombatResolutionSystem.resolve_attack(attacker, defender, state)
    
    assert "SHATTER" in combat_up.trace
    assert combat_up.trace["SHATTER"] == 1.5
    # Standard damage with 10 atk vs 5 def is roughly 4-5. With 1.5x atk (15 vs 5) it should be higher.
    # Formula: 15 * (15 / (15 + 10 + 1)) = 15 * (15 / 26) = 15 * 0.57 = ~8
    assert combat_up.damage_taken > 6

def test_exhaustion_debuff():
    """Verify EXHAUSTION damage reduction (0.8x) when sleep debt is high."""
    attacker = create_mock_entity(1, (1.0, 1.0))
    attacker = replace(attacker, biological=BiologicalComponent(sleep_debt=90.0))
    defender = create_mock_entity(2, (2.0, 1.0), faction=2)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})
    
    combat_up = CombatResolutionSystem.resolve_attack(attacker, defender, state)
    
    assert "EXHAUSTION" in combat_up.trace
    assert combat_up.trace["EXHAUSTION"] == 0.8

def test_combat_trace_modifiers():
    """Verify that multiple modifiers are recorded in the trace."""
    attacker = create_mock_entity(1, (1.0, 1.0))
    defender = create_mock_entity(2, (2.0, 1.0), faction=2)
    
    # Force High Ground
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender}, terrain={(1, 1): "HILL"})
    
    combat_up = CombatResolutionSystem.resolve_attack(attacker, defender, state)
    
    assert "HIGH_GROUND" in combat_up.trace
    assert combat_up.trace["FINAL_ATK_MULT"] > 1.0

def test_readiness_legality():
    """Verify that an entity with < 100 readiness cannot attack."""
    hero = create_mock_entity(1, (1.0, 1.0), role=EntityRole.HERO)
    hero = replace(hero, readiness=50.0)
    monster = create_mock_entity(2, (2.0, 1.0), role=EntityRole.MONSTER, faction=2)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: monster})
    
    # Hero attacks monster with 50 readiness
    updates = SimulationDomainLogic.execute_action(hero, {"action": "ATTACK", "target_id": 2}, context=state)
    update = updates[hero.id]
    
    assert update.combat is None
    assert update.navigation.failure_reason == "INSUFFICIENT_READINESS"

def test_los_legality():
    """Verify that attacking through a wall is illegal."""
    hero = create_mock_entity(1, (1.0, 1.0), role=EntityRole.HERO)
    monster = create_mock_entity(2, (3.0, 1.0), role=EntityRole.MONSTER, faction=2)
    # Range is 1, let's give hero a bow (range 5)
    hero = replace(hero, combat=replace(hero.combat, range=5))
    
    # Wall at (2,1)
    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: monster}, terrain={(2, 1): "WALL"})
    
    # Hero attacks monster through wall
    updates = SimulationDomainLogic.execute_action(hero, {"action": "ATTACK", "target_id": 2}, context=state)
    update = updates[hero.id]
    
    assert update.combat is None
    assert update.navigation.failure_reason == "LOS_OBSTRUCTED"
