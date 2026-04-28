import pytest
from dataclasses import replace
from src.core.state import EntityState, IdentityComponent, CombatComponent
from src.engine.legality import LegalityServiceV2

def create_mock_entity(eid, faction, hp=100, range=1, active=True):
    return EntityState(
        id=eid,
        kind="hero",
        position=(0, 0),
        readiness=100.0,
        active=active,
        identity=IdentityComponent(faction=faction),
        combat=CombatComponent(hp=hp, range=range, alive=(hp > 0))
    )

def test_melee_attack_legality():
    # 1. Legal Melee
    attacker = create_mock_entity(1, 1, range=1)
    target = create_mock_entity(2, 2)
    attacker = replace(attacker, position=(10, 10))
    target = replace(target, position=(10, 11)) # Manhattan dist 1
    
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, None)
    assert legal is True
    assert reason == "LEGAL"

    # 2. Out of Range Melee
    target = replace(target, position=(10, 12)) # Manhattan dist 2
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, None)
    assert legal is False
    assert reason == "OUT_OF_RANGE"

def test_ranged_attack_legality():
    # 1. Legal Ranged (Range 5)
    attacker = create_mock_entity(1, 1, range=5)
    target = create_mock_entity(2, 2)
    attacker = replace(attacker, position=(10, 10))
    target = replace(target, position=(10, 15)) # Manhattan dist 5
    
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, None)
    assert legal is True
    assert reason == "LEGAL"

    # 2. Out of Range Ranged
    target = replace(target, position=(10, 16)) # Manhattan dist 6
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, None)
    assert legal is False
    assert reason == "OUT_OF_RANGE"

def test_friendly_fire_legality():
    attacker = create_mock_entity(1, 1)
    target = create_mock_entity(2, 1) # Same faction
    attacker = replace(attacker, position=(10, 10))
    target = replace(target, position=(10, 11))
    
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, None)
    assert legal is False
    assert reason == "FRIENDLY_FIRE_ILLEGAL"

def test_incapacitated_legality():
    # 1. Attacker inactive
    attacker = create_mock_entity(1, 1, active=False)
    target = create_mock_entity(2, 2)
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, None)
    assert legal is False
    assert reason == "ATTACKER_INCAPACITATED"

    # 2. Target dead
    attacker = create_mock_entity(1, 1)
    target = create_mock_entity(2, 2, hp=0)
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, None)
    assert legal is False
    assert reason == "TARGET_INCAPACITATED"
