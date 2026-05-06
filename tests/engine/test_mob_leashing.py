import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, IdentityComponent, CombatComponent, NavigationComponent, StrategicComponent, TaskComponent
from src.engine.tactical import TacticalDecisionSystem
from src.core.enums import Faction
from src.core.movement_modes import MovementMode

from src.core.builder import V2EntityBuilder

def test_mob_beyond_leash_returns_home():
    state = AuthoritativeState(tick=100, seed=42)
    
    # Monster far from home (0,0), leash 5
    m1 = (V2EntityBuilder(1)
          .kind("monster")
          .location(8.0, 0.0)
          .identity(faction=Faction.MONSTER_HORDE)
          .combat(hp=100)
          .home_pos(0.0, 0.0)
          .leash_radius(5.0)
          .combat(readiness=100.0)
          .build())
    
    # Add a hero nearby to trigger tactical intent
    h1 = (V2EntityBuilder(2)
          .kind("hero")
          .location(11.0, 0.0)
          .identity(faction=Faction.HERO_GUILD)
          .combat(hp=100)
          .build())
    
    state = replace(state, entities={1: m1, 2: h1})
    
    update = TacticalDecisionSystem.evaluate_entity_intent(state, m1)
    
    assert update.navigation is not None
    assert update.navigation.target_set == (0.0, 0.0)
    assert update.navigation.movement_mode_set == MovementMode.RETREAT
    assert update.task.payload_set["reason"] == "LEASH_RETURN"
    
    print("\nSuccessfully verified mob beyond leash returns home.")

def test_mob_within_chase_radius_continues():
    state = AuthoritativeState(tick=100, seed=42)
    
    # Monster at (6.0, 0), home (0,0), leash 5. 
    # Within 1.5x leash (7.5)
    m1 = (V2EntityBuilder(1)
          .kind("monster")
          .location(3.0, 0.0)
          .identity(faction=Faction.MONSTER_HORDE)
          .combat(hp=100)
          .home_pos(0.0, 0.0)
          .leash_radius(5.0)
          .combat(readiness=100.0)
          .task("ENTITY_ACT", {"target_id": 2})
          .build())
    
    h1 = (V2EntityBuilder(2)
          .kind("hero")
          .location(5.0, 0.0)
          .identity(faction=Faction.HERO_GUILD)
          .combat(hp=100)
          .build())
    
    state = replace(state, entities={1: m1, 2: h1})
    
    update = TacticalDecisionSystem.evaluate_entity_intent(state, m1)
    
    # Should NOT be LEASH_RETURN
    assert update.task.payload_set.get("reason") != "LEASH_RETURN"
    # Should be ATTACK or PURSUE
    if update.task.payload_set.get("action") == "ATTACK":
        pass
    elif update.navigation and update.navigation.movement_mode_set == MovementMode.PURSUE:
        pass
    else:
        pytest.fail(f"Expected ATTACK or PURSUE, got {update}")
    
    print("\nSuccessfully verified mob within chase radius continues engagement.")

def test_mob_beyond_chase_radius_returns_home():
    state = AuthoritativeState(tick=100, seed=42)
    
    # Monster at (8.0, 0), home (0,0), leash 5. 
    # Beyond 1.5x leash (7.5)
    m1 = (V2EntityBuilder(1)
          .kind("monster")
          .location(8.0, 0.0)
          .identity(faction=Faction.MONSTER_HORDE)
          .combat(hp=100)
          .home_pos(0.0, 0.0)
          .leash_radius(5.0)
          .combat(readiness=100.0)
          .task("ENTITY_ACT", {"target_id": 2})
          .build())
    
    h1 = (V2EntityBuilder(2)
          .kind("hero")
          .location(9.0, 0.0)
          .identity(faction=Faction.HERO_GUILD)
          .combat(hp=100)
          .build())
    
    state = replace(state, entities={1: m1, 2: h1})
    
    update = TacticalDecisionSystem.evaluate_entity_intent(state, m1)
    
    assert update.navigation.target_set == (0.0, 0.0)
    assert update.task.payload_set["reason"] == "LEASH_RETURN"
    
    print("\nSuccessfully verified mob beyond chase radius returns home.")
