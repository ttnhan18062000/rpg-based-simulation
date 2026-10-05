import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, TaskComponent, RegionState
from src.engine.tactical import TacticalDecisionSystem
from src.core.builder import V2EntityBuilder

def create_mock_entity(eid, faction, hp=100, pos=(10.0, 10.0)):
    return V2EntityBuilder(eid).kind("hero").identity(faction=faction).combat(hp=hp).location(*pos).combat(readiness=100.0).build()

def test_stalemate_break():
    attacker = create_mock_entity(1, 1)
    target = create_mock_entity(2, 2, pos=(10, 11))
    
    # Pre-set high stale_ticks (11 > 10 threshold)
    attacker = replace(attacker, task=TaskComponent(payload={"target_id": 2, "stale_ticks": 11}))
    
    region = RegionState(id="field", name="Field", bounds=(5, 5, 30, 30))
    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 2: target}, regions={"field": region})

    # Should break stalemate by wandering to a nearby point inside the entity's own region
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    assert update.task.payload_set["reason"] == "STALEMATE_BREAK"
    wander_to = update.task.payload_set["target_position"]
    assert update.navigation.target_set == wander_to
    assert 5 <= wander_to[0] <= 30 and 5 <= wander_to[1] <= 30
    assert wander_to != (0.0, 0.0)

def test_stale_ticks_increment():
    attacker = create_mock_entity(1, 1)
    target = create_mock_entity(2, 2, pos=(10, 11))
    
    # Pre-set stale_ticks = 5
    attacker = replace(attacker, task=TaskComponent(payload={"target_id": 2, "stale_ticks": 5}))
    
    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 2: target})
    
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    assert update.task.payload_set["stale_ticks"] == 6
