import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, NavigationComponent, CombatComponent, IdentityComponent, RegionState
from src.core.enums import EntityRole, Faction
from src.engine.combat import CombatResolutionSystem
from src.engine.legality import LegalityServiceV2
from src.engine.domain_logic import SimulationDomainLogic
from src.core.builder import V2EntityBuilder

def create_mock_entity(
    entity_id,
    faction=Faction.HERO_GUILD,
    role=EntityRole.HERO,
    pos=(0, 0),
    hp=100,
    attack_range=1,
    readiness=100.0,
    active=True,
):
    entity = (
        V2EntityBuilder(entity_id)
        .kind("ACTOR")
        .location(*pos)
        .identity(
            faction=faction,
            role=role,
        )
        .combat(
            hp=hp,
            max_hp=max(hp, 100),
            atk=10,
            def_stat=5,
            attack_range=attack_range,
            readiness=readiness,
            alive=hp > 0,
        )
        .lifecycle(active=active)
        .build()
    )

    return entity

def test_attacker_incapacitated():
    """
    Verify dead or inactive attackers cannot attack.

    Fraud this catches:
    - hp=0 actor still has combat.alive=True
    - lifecycle.active=False is set but top-level entity.active remains True
    - legality allows incapacitated attackers to perform attacks
    """
    target = create_mock_entity(
        2,
        faction=Faction.MONSTER_HORDE,
        role=EntityRole.MONSTER,
        pos=(1, 0),
    )

    # Dead attacker.
    attacker_dead = create_mock_entity(
        1,
        hp=0,
        active=True,
    )

    state = AuthoritativeState(
        entities={1: attacker_dead, 2: target},
        tick=0,
        seed=1,
    )

    assert attacker_dead.combat.alive is False
    assert attacker_dead.active is True

    is_legal, reason = LegalityServiceV2.verify_attack_legality(
        attacker_dead,
        target,
        state,
    )

    assert is_legal is False
    assert reason == "ATTACKER_INCAPACITATED"

    # Inactive attacker.
    attacker_inactive = create_mock_entity(
        1,
        hp=100,
        active=False,
    )

    state = AuthoritativeState(
        entities={1: attacker_inactive, 2: target},
        tick=0,
        seed=1,
    )

    assert attacker_inactive.lifecycle.active is False
    assert attacker_inactive.active is False

    is_legal, reason = LegalityServiceV2.verify_attack_legality(
        attacker_inactive,
        target,
        state,
    )

    assert is_legal is False
    assert reason == "ATTACKER_INCAPACITATED"


def test_target_incapacitated():
    """
    Verify dead or inactive targets cannot be attacked.

    Fraud this catches:
    - hp=0 target still has combat.alive=True
    - lifecycle.active=False is set but top-level entity.active remains True
    - legality allows attacks against incapacitated targets
    """
    attacker = create_mock_entity(1)

    # Dead target.
    target_dead = create_mock_entity(
        2,
        hp=0,
        faction=Faction.MONSTER_HORDE,
        role=EntityRole.MONSTER,
        pos=(1, 0),
    )

    state = AuthoritativeState(
        entities={1: attacker, 2: target_dead},
        tick=0,
        seed=1,
    )

    assert target_dead.combat.alive is False

    is_legal, reason = LegalityServiceV2.verify_attack_legality(
        attacker,
        target_dead,
        state,
    )

    assert is_legal is False
    assert reason == "TARGET_INCAPACITATED"

    # Inactive target.
    target_inactive = create_mock_entity(
        2,
        faction=Faction.MONSTER_HORDE,
        role=EntityRole.MONSTER,
        pos=(1, 0),
        hp=100,
        active=False,
    )

    state = AuthoritativeState(
        entities={1: attacker, 2: target_inactive},
        tick=0,
        seed=1,
    )

    assert target_inactive.lifecycle.active is False
    assert target_inactive.active is False

    is_legal, reason = LegalityServiceV2.verify_attack_legality(
        attacker,
        target_inactive,
        state,
    )

    assert is_legal is False
    assert reason == "TARGET_INCAPACITATED"

def test_attacker_status_blocked():
    attacker = create_mock_entity(1)
    target = create_mock_entity(2, faction=Faction.MONSTER_HORDE, pos=(1,0))
    state = AuthoritativeState(entities={1: attacker, 2: target}, tick=0, seed=1)
    
    # Stunned
    attacker_stunned = (V2EntityBuilder(1)
                        .kind("ACTOR")
                        .combat(readiness=100.0)
                        .identity(properties={"status_stunned": True})
                        .build())
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker_stunned, target, state)
    assert not is_legal
    assert reason == "ATTACKER_STATUS_BLOCKED"
    
    # Frozen
    attacker_frozen = (V2EntityBuilder(1)
                       .kind("ACTOR")
                       .combat(readiness=100.0)
                       .identity(properties={"status_frozen": True})
                       .build())
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker_frozen, target, state)
    assert not is_legal
    assert reason == "ATTACKER_STATUS_BLOCKED"

def test_self_attack_rejection():
    attacker = create_mock_entity(1)
    state = AuthoritativeState(entities={1: attacker}, tick=0, seed=1)
    
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, attacker, state)
    assert not is_legal
    assert reason == "SELF_ATTACK_ILLEGAL"

def test_regional_suppression():
    attacker = create_mock_entity(1, pos=(10,10))
    region = RegionState(id="SOP", name="Safe Zone", bounds=(0,0,20,20), suppression_active=True)
    state = AuthoritativeState(entities={1: attacker}, regions={"SOP": region}, tick=0, seed=1)
    
    # Suppressed actions
    for action in ["SABOTAGE", "RECRUIT", "THEFT"]:
        is_legal, reason = LegalityServiceV2.verify_action_legality(attacker, action, state)
        assert not is_legal
        assert reason == "REGIONAL_SUPPRESSION"
        
    # Allowed actions
    is_legal, reason = LegalityServiceV2.verify_action_legality(attacker, "ATTACK", state)
    assert is_legal

def test_los_obstruction():
    attacker = create_mock_entity(1, pos=(0,0), attack_range=5)
    target = create_mock_entity(2, pos=(3,0), faction=Faction.MONSTER_HORDE)
    
    # Blocked by WALL
    state_blocked = AuthoritativeState(
        entities={1: attacker, 2: target}, 
        terrain={(1,0): "WALL"},
        tick=0, seed=1
    )
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state_blocked)
    assert not is_legal
    assert reason == "LOS_OBSTRUCTED"
    
    # Clear path
    state_clear = AuthoritativeState(
        entities={1: attacker, 2: target}, 
        terrain={(1,0): "PLAIN"},
        tick=0, seed=1
    )
    is_legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state_clear)
    assert is_legal

def test_aoe_negative_cases():
    attacker = create_mock_entity(1, pos=(0,0), attack_range=5)
    state = AuthoritativeState(entities={1: attacker}, tick=0, seed=1)
    
    # Attacker status blocked (Stunned)
    attacker_stunned = (V2EntityBuilder(1)
                        .kind("ACTOR")
                        .location(0, 0)
                        .combat(readiness=100.0)
                        .identity(properties={"status_stunned": True})
                        .build())
    res = CombatResolutionSystem.resolve_aoe_attack(attacker_stunned, (2,0), 2, state)
    assert res[1].outcome_kind == "REJECTED"
    assert res[1].failure_reason == "ATTACKER_STATUS_BLOCKED"
    
    # Out of range
    res = CombatResolutionSystem.resolve_aoe_attack(attacker, (6,0), 2, state)
    assert res[1].outcome_kind == "REJECTED"
    assert res[1].failure_reason == "OUT_OF_RANGE"
    
    # LoS blocked to AoE center
    state_blocked = AuthoritativeState(
        entities={1: attacker}, 
        terrain={(1,0): "WALL"},
        tick=0, seed=1
    )
    res = CombatResolutionSystem.resolve_aoe_attack(attacker, (2,0), 2, state_blocked)
    assert res[1].outcome_kind == "REJECTED"
    assert res[1].failure_reason == "LOS_OBSTRUCTED"

def test_execute_action_target_not_found():
    attacker = create_mock_entity(1)
    state = AuthoritativeState(entities={1: attacker}, tick=0, seed=1)
    
    # RECRUIT missing target
    updates = SimulationDomainLogic.execute_action(attacker, {"action": "RECRUIT", "target_id": 999}, context=state)
    assert 1 in updates
    assert updates[1].navigation.failure_reason == "TARGET_NOT_FOUND"
    
    # ATTACK missing target
    updates = SimulationDomainLogic.execute_action(attacker, {"action": "ATTACK", "target_id": 999}, context=state)
    assert 1 in updates
    assert updates[1].readiness_delta == -10.0

def test_execute_action_legality_fail():
    attacker = create_mock_entity(1)
    target = create_mock_entity(2, faction=Faction.HERO_GUILD, pos=(1,0)) # Friendly
    state = AuthoritativeState(entities={1: attacker, 2: target}, tick=0, seed=1)
    
    # ATTACK friendly fire
    updates = SimulationDomainLogic.execute_action(attacker, {"action": "ATTACK", "target_id": 2}, context=state)
    assert 1 in updates
    assert updates[1].readiness_delta == -50.0
    assert updates[1].navigation.failure_reason == "FRIENDLY_FIRE_ILLEGAL"
