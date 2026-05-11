from __future__ import annotations
import pytest
from dataclasses import replace
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, EntityState, TaskComponent
from src.core.updates import EntityUpdate, TaskUpdate
from src.engine.tactical import TacticalDecisionSystem
from src.core.enums import EntityRole, Faction

def make_entity(eid: int, pos: tuple[float, float], faction: Faction = Faction.HERO_GUILD):
    return (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(float(pos[0]), float(pos[1]))
        .identity(faction=faction)
        .combat(hp=100, max_hp=100, alive=True, tactical_role="VANGUARD", readiness=100.0)
        .lifecycle(active=True)
        .build()
    )

def test_target_stickiness_maintained():
    """
    LAW: COMB-270 - Target stickiness prevents unrealistic full retarget every tick.
    """
    attacker = make_entity(1, pos=(0, 0), faction=Faction.HERO_GUILD)
    target1 = make_entity(2, pos=(1, 0), faction=Faction.MONSTER_HORDE) # Close
    target2 = make_entity(3, pos=(2, 0), faction=Faction.MONSTER_HORDE) # Slightly further
    
    state = AuthoritativeState(
        tick=10,
        seed=1,
        entities={1: attacker, 2: target1, 3: target2}
    )
    
    # 1. Initial decision: should pick target1 (closest)
    upd1 = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    assert upd1 is not None
    assert upd1.task is not None
    assert upd1.task.payload_set["target_id"] == 2
    
    # 2. Next tick: attacker is now "stuck" to target1
    attacker_stuck = replace(attacker, task=TaskComponent(payload={"target_id": 2}))
    
    # Even if target2 becomes closer, it should stick to target1 for a while
    target2_closer = replace(target2, navigation=replace(target2.navigation, position=(0.5, 0)))
    state_v2 = replace(state, entities={1: attacker_stuck, 2: target1, 3: target2_closer})
    
    upd2 = TacticalDecisionSystem.evaluate_entity_intent(state_v2, attacker_stuck)
    assert upd2.task.payload_set["target_id"] == 2, "Should have stuck to target 2 despite target 3 being closer"

def test_target_stickiness_breaks_on_death():
    """
    LAW: COMB-271 - Target stickiness can break when target invalid/dead.
    """
    attacker = make_entity(1, pos=(0, 0), faction=Faction.HERO_GUILD)
    target1 = make_entity(2, pos=(1, 0), faction=Faction.MONSTER_HORDE)
    target1_dead = replace(target1, combat=replace(target1.combat, hp=0, alive=False))
    target2 = make_entity(3, pos=(5, 0), faction=Faction.MONSTER_HORDE)
    
    state = AuthoritativeState(
        tick=10,
        seed=1,
        entities={1: attacker, 2: target1_dead, 3: target2}
    )
    
    attacker_stuck = replace(attacker, task=TaskComponent(payload={"target_id": 2}))
    
    upd = TacticalDecisionSystem.evaluate_entity_intent(state, attacker_stuck)
    assert upd.task.payload_set["target_id"] == 3, "Should have switched to target 3 because target 2 is dead"

def test_target_stickiness_breaks_on_distance_threshold():
    """
    LAW: COMB-271 - Target stickiness can break when target out of range beyond threshold.
    """
    attacker = make_entity(1, pos=(0, 0), faction=Faction.HERO_GUILD)
    target1 = make_entity(2, pos=(20, 0), faction=Faction.MONSTER_HORDE) # Very far
    target2 = make_entity(3, pos=(1, 0), faction=Faction.MONSTER_HORDE) # Very close
    
    state = AuthoritativeState(
        tick=10,
        seed=1,
        entities={1: attacker, 2: target1, 3: target2}
    )
    
    attacker_stuck = replace(attacker, task=TaskComponent(payload={"target_id": 2}))
    
    upd = TacticalDecisionSystem.evaluate_entity_intent(state, attacker_stuck)
    assert upd.task.payload_set["target_id"] == 3, "Should have switched to target 3 because target 2 is too far"
