import pytest
from dataclasses import replace
from src.core.state import NavigationComponent, LifecycleComponent, AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.engine.legality import LegalityServiceV2
from src.core.enums import ReasonCode

def create_mock_entity(eid, faction, hp=100, range=1, active=True):
    builder = (V2EntityBuilder(eid)
               .kind("hero")
               .faction(faction)
               .with_base_stats(range=range)
               .hp(hp)
               .active(active)
               .readiness(100.0))
    return builder.build()

def test_melee_attack_legality():
    # 1. Legal Melee
    attacker = create_mock_entity(1, 1, range=1)
    target = create_mock_entity(2, 2)
    attacker = replace(attacker, navigation=replace(attacker.navigation, position=(10, 10)))
    target = replace(target, navigation=replace(target.navigation, position=(10, 11))) # Manhattan dist 1
    
    state = AuthoritativeState(tick=1, seed=1)
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)
    assert legal is True
    assert reason == ReasonCode.LEGAL

    # 2. Out of Range Melee
    target = replace(target, navigation=replace(target.navigation, position=(10, 12))) # Manhattan dist 2
    state = AuthoritativeState(tick=1, seed=1)
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)
    assert legal is False
    assert reason == ReasonCode.OUT_OF_RANGE

def test_ranged_attack_legality():
    # 1. Legal Ranged (Range 5)
    attacker = create_mock_entity(1, 1, range=5)
    target = create_mock_entity(2, 2)
    attacker = replace(attacker, navigation=replace(attacker.navigation, position=(10, 10)))
    target = replace(target, navigation=replace(target.navigation, position=(10, 15))) # Manhattan dist 5
    
    state = AuthoritativeState(tick=1, seed=1)
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)
    assert legal is True
    assert reason == ReasonCode.LEGAL

    # 2. Out of Range Ranged
    target = replace(target, navigation=replace(target.navigation, position=(10, 16))) # Manhattan dist 6
    state = AuthoritativeState(tick=1, seed=1)
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)
    assert legal is False
    assert reason == ReasonCode.OUT_OF_RANGE

def test_friendly_fire_legality():
    attacker = create_mock_entity(1, 1)
    target = create_mock_entity(2, 1) # Same faction
    attacker = replace(attacker, navigation=replace(attacker.navigation, position=(10, 10)))
    target = replace(target, navigation=replace(target.navigation, position=(10, 11)))
    
    state = AuthoritativeState(tick=1, seed=1)
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)
    assert legal is False
    assert reason == ReasonCode.FRIENDLY_FIRE_ILLEGAL

def test_incapacitated_legality():
    # 1. Attacker inactive
    attacker = create_mock_entity(1, 1, active=False)
    target = create_mock_entity(2, 2)
    state = AuthoritativeState(tick=1, seed=1)
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)
    assert legal is False
    assert reason == ReasonCode.ATTACKER_INCAPACITATED

    # 2. Target dead
    attacker = create_mock_entity(1, 1)
    target = create_mock_entity(2, 2, hp=0)
    state = AuthoritativeState(tick=1, seed=1)
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)
    assert legal is False
    assert reason == ReasonCode.TARGET_INCAPACITATED
