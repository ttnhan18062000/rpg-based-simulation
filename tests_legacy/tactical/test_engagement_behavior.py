import pytest
from dataclasses import replace
from src_legacy.core.state import EntityState, IdentityComponent, CombatComponent, AuthoritativeState, TaskComponent
from src_legacy.engine.tactical import TacticalDecisionSystem

def create_mock_entity(eid, faction, hp=100, pos=(0, 0), range=1):
    return EntityState(
        id=eid,
        kind="hero",
        position=pos,
        identity=IdentityComponent(faction=faction),
        combat=CombatComponent(hp=hp, max_hp=100, range=range, alive=(hp > 0)),
        task=TaskComponent()
    )

def test_attack_vs_pursuit_intent():
    attacker = create_mock_entity(1, 1, pos=(10, 10), range=1)
    target = create_mock_entity(2, 2, pos=(10, 11)) # Adjacency 1
    
    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 2: target})
    
    # 1. Melee Attack (Range 1, Dist 1)
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    assert update.task.work_kind_set == "ENTITY_ACT"
    assert update.task.payload_set["action"] == "ATTACK"
    assert update.task.payload_set["target_id"] == 2
    
    # 2. Pursuit (Range 1, Dist 2)
    target = replace(target, position=(10, 12))
    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 2: target})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    assert update.task.work_kind_set == "ENTITY_MOVE"
    assert update.task.payload_set["target_position"] == (10, 12)

def test_retreat_behavior():
    # Low HP (10/100 = 10%)
    attacker = create_mock_entity(1, 1, hp=10, pos=(10, 10))
    target = create_mock_entity(2, 2, pos=(10, 11))
    
    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 2: target})
    
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    assert update.task.work_kind_set == "ENTITY_MOVE"
    assert update.task.payload_set["reason"] == "PANIC_RETREAT"
    assert update.task.payload_set["target_position"] == (0.0, 0.0)

def test_target_stickiness():
    attacker = create_mock_entity(1, 1, pos=(10, 10))
    target_a = create_mock_entity(2, 2, hp=50, pos=(10, 11)) # Current target
    target_b = create_mock_entity(3, 2, hp=10, pos=(10, 12)) # "Better" target (lower HP)
    
    # Pre-set target A in payload
    attacker = replace(attacker, task=TaskComponent(payload={"target_id": 2}))
    
    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 2: target_a, 3: target_b})
    
    # Should stick to target A even though B has lower HP
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    assert update.task.payload_set["target_id"] == 2
