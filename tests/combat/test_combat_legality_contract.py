import pytest
from dataclasses import replace
from src.core.state import NavigationComponent, LifecycleComponent, AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.engine.legality import LegalityServiceV2
from src.core.enums import ReasonCode, Faction

def create_mock_entity(eid, faction, hp=100, attack_range=1, active=True):
    entity = (
        V2EntityBuilder(eid)
        .kind("hero")
        .identity(faction=faction)
        .combat(
            hp=hp,
            max_hp=max(100, hp),
            attack_range=attack_range,
            alive=hp > 0,
            readiness=100.0,
        )
        .lifecycle(active=active)
        .build()
    )

    return entity

def test_melee_attack_legality():
    # 1. Legal Melee
    attacker = create_mock_entity(1, Faction.HERO_GUILD, attack_range=1)
    target = create_mock_entity(2, Faction.MONSTER_HORDE)
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
    attacker = create_mock_entity(1, Faction.HERO_GUILD, attack_range=5)
    target = create_mock_entity(2, Faction.MONSTER_HORDE)
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
    attacker = create_mock_entity(1, Faction.HERO_GUILD)
    target = create_mock_entity(2, Faction.HERO_GUILD) # Same faction
    attacker = replace(attacker, navigation=replace(attacker.navigation, position=(10, 10)))
    target = replace(target, navigation=replace(target.navigation, position=(10, 11)))
    
    state = AuthoritativeState(tick=1, seed=1)
    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)
    assert legal is False
    assert reason == ReasonCode.FRIENDLY_FIRE_ILLEGAL

def test_incapacitated_legality():
    attacker = create_mock_entity(
        1,
        Faction.HERO_GUILD,
        active=False,
    )
    target = create_mock_entity(
        2,
        Faction.MONSTER_HORDE,
    )

    assert attacker.lifecycle.active is False
    assert attacker.active is False

    state = AuthoritativeState(
        tick=1,
        seed=1,
        entities={1: attacker, 2: target},
    )

    legal, reason = LegalityServiceV2.verify_attack_legality(
        attacker,
        target,
        state,
    )

    assert legal is False
    assert reason == ReasonCode.ATTACKER_INCAPACITATED