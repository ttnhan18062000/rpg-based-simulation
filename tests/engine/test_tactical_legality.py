import pytest
from dataclasses import replace
from src.core.state import EntityState, AuthoritativeState, CombatComponent, NavigationComponent, IdentityComponent
from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate
from src.core.enums import ReasonCode, EntityRole
from src.engine.tactical import TacticalDecisionSystem
from src.core.builder import V2EntityBuilder

def test_tactical_legality_filtering():
    # Setup state with a wall between attacker and closest target
    initial_state = AuthoritativeState(tick=100, seed=42)
    state = replace(initial_state, terrain={(1, 0): "WALL"})
    
    # Attacker at (0, 0), Faction 1
    attacker = (V2EntityBuilder(1)
                .kind("hero")
                .at((0.0, 0.0))
                .readiness(100.0)
                .faction(1)
                .with_base_stats(range=5)
                .build())
    
    # Target 1 (Illegal): Closest but behind wall at (2, 0), Faction 2
    t1 = (V2EntityBuilder(2)
          .kind("monster")
          .at((2.0, 0.0))
          .faction(2)
          .with_current_hp(10)
          .build())
    
    # Target 2 (Legal): Further away at (0, 2), no wall, Faction 2
    t2 = (V2EntityBuilder(3)
          .kind("monster")
          .at((0.0, 2.0))
          .faction(2)
          .with_current_hp(100)
          .build())
    
    state = replace(state, entities={1: attacker, 2: t1, 3: t2})
    
    # Evaluate intent
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    
    # Assertions
    assert update.task is not None, "Tactical Decision failed to produce a task"
    target_id = update.task.payload_set.get("target_id")
    action = update.task.payload_set.get("action")
    
    print(f"\nTactical Decision: Action={action}, Target={target_id}")
    
    assert target_id == 3, f"Expected to target 3 (legal), but targeted {target_id}"
    assert action == "ATTACK", f"Expected ATTACK action, but got {action}"

def test_tactical_blocked_kite():
    # Setup state where kiting is blocked by a wall
    initial_state = AuthoritativeState(tick=100, seed=42)
    # Skirmisher kiting distance is 6 (4 + 2). Wall at (-6, 0) blocks it.
    state = replace(initial_state, terrain={(-6, 0): "WALL"})
    
    # Attacker (Skirmisher) at (0, 0), Faction 1
    attacker = (V2EntityBuilder(1)
                .kind("hero")
                .at((0.0, 0.0))
                .readiness(100.0)
                .faction(1)
                .with_base_stats(range=5, tactical_role="SKIRMISHER")
                .build())
    
    # Target at (1, 0), Faction 2
    target = (V2EntityBuilder(2)
              .kind("monster")
              .at((1.0, 0.0))
              .faction(2)
              .with_current_hp(100)
              .build())
    
    state = replace(state, entities={1: attacker, 2: target})
    
    # Evaluate intent
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    
    # Assertions
    assert update.task is not None, "Tactical Decision failed to produce a task for kiting"
    reason = update.task.payload_set.get("reason")
    print(f"\nKite Fallback: Reason={reason}")
    
    assert reason == "PURSUIT_BLOCKED_KITE"
