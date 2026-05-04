import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, IdentityComponent, CombatComponent, NavigationComponent, StrategicComponent, TaskComponent
from src.engine.tactical import TacticalDecisionSystem
from src.core.movement_modes import MovementMode

def test_mob_beyond_leash_returns_home():
    state = AuthoritativeState(tick=100, seed=42)
    
    # Monster far from home (0,0), leash 5
    m1 = EntityState(
        id=1, kind="monster", position=(10.0, 0.0),
        identity=IdentityComponent(faction=2),
        combat=CombatComponent(hp=100, max_hp=100),
        navigation=NavigationComponent(home_position=(0.0, 0.0), leash_radius=5.0),
        strategic=StrategicComponent(),
        task=TaskComponent(work_kind="IDLE")
    )
    
    # Add a hero nearby to trigger tactical intent
    h1 = EntityState(
        id=2, kind="hero", position=(11.0, 0.0),
        identity=IdentityComponent(faction=1),
        combat=CombatComponent(hp=100, max_hp=100),
        navigation=NavigationComponent(),
        strategic=StrategicComponent(),
        task=TaskComponent(work_kind="IDLE")
    )
    
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
    m1 = EntityState(
        id=1, kind="monster", position=(6.0, 0.0),
        identity=IdentityComponent(faction=2),
        combat=CombatComponent(hp=100, max_hp=100),
        navigation=NavigationComponent(home_position=(0.0, 0.0), leash_radius=5.0),
        strategic=StrategicComponent(),
        task=TaskComponent(work_kind="ENTITY_ACT", payload={"target_id": 2})
    )
    
    h1 = EntityState(
        id=2, kind="hero", position=(5.0, 0.0),
        identity=IdentityComponent(faction=1),
        combat=CombatComponent(hp=100, max_hp=100),
        navigation=NavigationComponent(),
        strategic=StrategicComponent(),
        task=TaskComponent(work_kind="IDLE")
    )
    
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
    m1 = EntityState(
        id=1, kind="monster", position=(8.0, 0.0),
        identity=IdentityComponent(faction=2),
        combat=CombatComponent(hp=100, max_hp=100),
        navigation=NavigationComponent(home_position=(0.0, 0.0), leash_radius=5.0),
        strategic=StrategicComponent(),
        task=TaskComponent(work_kind="ENTITY_ACT", payload={"target_id": 2})
    )
    
    h1 = EntityState(
        id=2, kind="hero", position=(9.0, 0.0),
        identity=IdentityComponent(faction=1),
        combat=CombatComponent(hp=100, max_hp=100),
        navigation=NavigationComponent(),
        strategic=StrategicComponent(),
        task=TaskComponent(work_kind="IDLE")
    )
    
    state = replace(state, entities={1: m1, 2: h1})
    
    update = TacticalDecisionSystem.evaluate_entity_intent(state, m1)
    
    assert update.navigation.target_set == (0.0, 0.0)
    assert update.task.payload_set["reason"] == "LEASH_RETURN"
    
    print("\nSuccessfully verified mob beyond chase radius returns home.")
