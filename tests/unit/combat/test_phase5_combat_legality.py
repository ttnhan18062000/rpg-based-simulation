
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, NavigationComponent, CombatComponent, IdentityComponent
from src.core.enums import EntityRole, ReasonCode
from src.engine.combat import CombatResolutionSystem

from src.core.builder import V2EntityBuilder

def create_mock_entity(id, faction="HERO_FACTION", role=EntityRole.HERO, pos=(0,0), hp=100, range=1, readiness=100.0):
    return (V2EntityBuilder(id)
            .kind("ACTOR")
            .location(*pos)
            .combat(hp=hp, attack_range=range, readiness=readiness, alive=hp > 0)
            .identity(role=role, faction=faction)
            .build())

def test_melee_legality():
    attacker = create_mock_entity(1, pos=(0,0), range=1)
    target = create_mock_entity(2, pos=(1,0), faction="MONSTER_FACTION") # Adjacent
    state = AuthoritativeState(entities={1: attacker, 2: target}, tick=0, seed=1)
    
    # Legal
    update = CombatResolutionSystem.resolve_attack(attacker, target, state)
    assert update.outcome_kind != "REJECTED"
    
    # Illegal (Dist 2)
    target_far = replace(target, navigation=replace(target.navigation, position=(2,0)))
    state_far = AuthoritativeState(entities={1: attacker, 2: target_far}, tick=0, seed=1)
    update = CombatResolutionSystem.resolve_attack(attacker, target_far, state_far)
    assert update.outcome_kind == "REJECTED"
    # Note: failure_reason depends on implementation, might be OUT_OF_RANGE or TARGET_INVALID
    assert update.failure_reason in [ReasonCode.TARGET_INVALID, ReasonCode.OUT_OF_RANGE]

def test_ranged_legality():
    attacker = create_mock_entity(1, pos=(0,0), range=5)
    target = create_mock_entity(2, pos=(4,0), faction="MONSTER_FACTION") # In range
    state = AuthoritativeState(entities={1: attacker, 2: target}, tick=0, seed=1)
    
    # Legal
    update = CombatResolutionSystem.resolve_attack(attacker, target, state)
    assert update.outcome_kind != "REJECTED"
    
    # Illegal (Dist 6)
    target_far = replace(target, navigation=replace(target.navigation, position=(6,0)))
    state_far = AuthoritativeState(entities={1: attacker, 2: target_far}, tick=0, seed=1)
    update = CombatResolutionSystem.resolve_attack(attacker, target_far, state_far)
    assert update.outcome_kind == "REJECTED"
    assert update.failure_reason in [ReasonCode.TARGET_INVALID, ReasonCode.OUT_OF_RANGE]

def test_readiness_block():
    attacker = create_mock_entity(1, readiness=99.0)
    target = create_mock_entity(2, faction="MONSTER_FACTION", pos=(1,0))
    state = AuthoritativeState(entities={1: attacker, 2: target}, tick=0, seed=1)
    
    update = CombatResolutionSystem.resolve_attack(attacker, target, state)
    assert update.outcome_kind == "REJECTED"
    assert update.failure_reason == ReasonCode.INSUFFICIENT_READINESS

def test_status_block():
    attacker = create_mock_entity(1)
    attacker = replace(attacker, identity=replace(attacker.identity, properties={"status_frozen": True}))
    target = create_mock_entity(2, faction="MONSTER_FACTION", pos=(1,0))
    state = AuthoritativeState(entities={1: attacker, 2: target}, tick=0, seed=1)
    
    update = CombatResolutionSystem.resolve_attack(attacker, target, state)
    assert update.outcome_kind == "REJECTED"
    assert update.failure_reason == ReasonCode.ATTACKER_STATUS_BLOCKED

def test_dead_legality():
    # Attacker dead
    attacker = create_mock_entity(1, hp=0)
    target = create_mock_entity(2, faction="MONSTER_FACTION", pos=(1,0))
    state = AuthoritativeState(entities={1: attacker, 2: target}, tick=0, seed=1)
    update = CombatResolutionSystem.resolve_attack(attacker, target, state)
    assert update.outcome_kind == "REJECTED"
    assert update.failure_reason == ReasonCode.ATTACKER_INCAPACITATED
    
    # Target dead
    attacker_alive = create_mock_entity(1)
    target_dead = create_mock_entity(2, hp=0, faction="MONSTER_FACTION", pos=(1,0))
    state_dead = AuthoritativeState(entities={1: attacker_alive, 2: target_dead}, tick=0, seed=1)
    update = CombatResolutionSystem.resolve_attack(attacker_alive, target_dead, state_dead)
    assert update.outcome_kind == "REJECTED"
    assert update.failure_reason == ReasonCode.TARGET_INCAPACITATED

def test_friendly_fire():
    attacker = create_mock_entity(1, faction="HERO_FACTION")
    target = create_mock_entity(2, faction="HERO_FACTION", pos=(1,0))
    state = AuthoritativeState(entities={1: attacker, 2: target}, tick=0, seed=1)
    
    update = CombatResolutionSystem.resolve_attack(attacker, target, state)
    assert update.outcome_kind == "REJECTED"
    assert update.failure_reason == ReasonCode.FRIENDLY_FIRE_ILLEGAL

    # Logic ID: COMB-029

def test_aoe_legality():
    attacker = create_mock_entity(1, pos=(0,0), range=5)
    state = AuthoritativeState(entities={1: attacker}, tick=0, seed=1)
    
    # Legal AoE center
    updates = CombatResolutionSystem.resolve_aoe_attack(attacker, (3,0), 2, state)
    assert updates[attacker.id].outcome_kind != "REJECTED"
    
    # Illegal AoE center (Out of range)
    updates = CombatResolutionSystem.resolve_aoe_attack(attacker, (6,0), 2, state)
    assert updates[attacker.id].outcome_kind == "REJECTED"
    assert updates[attacker.id].failure_reason == ReasonCode.OUT_OF_RANGE
    
    # Illegal (Readiness)
    attacker = replace(attacker, combat=replace(attacker.combat, readiness=0))
    updates = CombatResolutionSystem.resolve_aoe_attack(attacker, (3,0), 2, state)
    assert updates[attacker.id].outcome_kind == "REJECTED"
    assert updates[attacker.id].failure_reason in [ReasonCode.ACTION_EXHAUSTION, ReasonCode.INSUFFICIENT_READINESS]

def test_multi_attack_filtering():
    a1 = create_mock_entity(1, pos=(0,0)) # Legal
    a2 = create_mock_entity(2, pos=(5,5)) # Illegal (Too far)
    target = create_mock_entity(3, pos=(1,0), faction="MONSTER_FACTION")
    
    state = AuthoritativeState(entities={1: a1, 2: a2, 3: target}, tick=0, seed=1)
    
    # a2 should be filtered out, only a1 hits
    update = CombatResolutionSystem.resolve_multi_attack([a1, a2], target, state)
    assert update.outcome_kind != "REJECTED"
    assert len(update.simultaneous_intents) == 1
    assert update.simultaneous_intents[0].attacker_id == 1
    
    # Both illegal
    a1_far = replace(a1, navigation=replace(a1.navigation, position=(5,5)))
    update_none = CombatResolutionSystem.resolve_multi_attack([a1_far, a2], target, state)
    assert update_none.outcome_kind == "REJECTED"
    assert update_none.failure_reason in [ReasonCode.TARGET_INVALID, ReasonCode.OUT_OF_RANGE]
