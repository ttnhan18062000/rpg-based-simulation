import pytest
from dataclasses import replace
from src.core.state import EntityState, IdentityComponent, CombatComponent, AuthoritativeState, TaskComponent
from src.engine.tactical import TacticalDecisionSystem
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction

def create_mock_entity(eid, faction, hp=100, pos=(0.0, 0.0), range=1):
    role = EntityRole.HERO if faction == 1 else EntityRole.MONSTER
    return (V2EntityBuilder(eid)
            .kind("hero" if role == EntityRole.HERO else "monster")
            .at(pos)
            .with_identity(role=role, faction=faction)
            .with_combat(hp=hp, max_hp=100, range=range)
            .build())

def test_attack_vs_pursuit_intent():
    attacker = create_mock_entity(1, 1, pos=(10.0, 10.0), range=1)
    target = create_mock_entity(2, 2, pos=(10.0, 11.0)) # Adjacency 1
    
    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 2: target})
    
    # 1. Melee Attack (Range 1, Dist 1)
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    assert update.task.work_kind_set == "ENTITY_ACT"
    assert update.task.payload_set["action"] == "ATTACK"
    assert update.task.payload_set["target_id"] == 2
    
    # 2. Pursuit (Range 1, Dist 2)
    target = replace(target, navigation=replace(target.navigation, position=(10.0, 12.0)))
    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 2: target})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    assert update.task.work_kind_set == "ENTITY_MOVE"
    assert update.task.payload_set["target_position"] == (10.0, 12.0)

def test_retreat_behavior():
    # Low HP (10/100 = 10%)
    attacker = create_mock_entity(1, 1, hp=10, pos=(10.0, 10.0))
    target = create_mock_entity(2, 2, pos=(10.0, 11.0))
    
    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 2: target})
    
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    assert update.task.work_kind_set == "ENTITY_MOVE"
    assert update.task.payload_set["reason"] == "PANIC_RETREAT"
    assert update.task.payload_set["target_position"] == (0.0, 0.0)

def test_target_stickiness():
    attacker = create_mock_entity(1, 1, pos=(10.0, 10.0))
    target_a = create_mock_entity(2, 2, hp=50, pos=(10.0, 11.0)) # Current target
    target_b = create_mock_entity(3, 2, hp=10, pos=(10.0, 12.0)) # "Better" target (lower HP)
    
    # Pre-set target A in payload
    attacker = replace(attacker, task=replace(attacker.task, payload={"target_id": 2}))
    
    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 2: target_a, 3: target_b})
    
    # Should stick to target A even though B has lower HP
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    assert update.task.payload_set["target_id"] == 2
