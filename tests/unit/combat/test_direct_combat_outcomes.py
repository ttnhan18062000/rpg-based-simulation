import pytest
"""
- [RPG-COMBAT-001] Damage calculation follows the Fractional Armor Mitigation (FAM) law.
- [RPG-COMBAT-002] Combat outcomes (SURVIVE, DEFEAT, KILL) are mutually exclusive.
"""
from src.core.state import AuthoritativeState
from src.engine.combat import CombatResolutionSystem
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction

def create_mock_entity(eid, faction=Faction.HERO_GUILD, atk=10, dfn=5, hp=100, role=EntityRole.HERO):
    return (V2EntityBuilder(eid)
        .kind("hero")
        .location(0.0, 0.0)
        .combat(readiness=100.0)
        .identity(role=role, faction=faction)
        .attributes(strength=0, vitality=0)
        .combat(hp=hp, max_hp=hp, atk=atk, def_stat=dfn)
        .build())

def test_combat_damage_calculation():
    """
    [RPG-COMBAT-001] Damage calculation follows the Fractional Armor Mitigation (FAM) law.
    Formula: damage = atk * (atk / (atk + def * 2.0 + 1.0))
    atk=10, def=5 => 10 * (10 / (10 + 10 + 1)) = 10 * (10/21) = 10 * 0.476 = 4.76 => 4
    """
    attacker = create_mock_entity(1, atk=10)
    defender = create_mock_entity(2, dfn=5)
    
    damage = CombatResolutionSystem.calculate_damage(attacker, defender)
    assert damage == 4

def test_survival_outcome():
    attacker = create_mock_entity(1, faction=1, atk=10)
    defender = create_mock_entity(2, faction=2, hp=100) # Different faction
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})
    update = CombatResolutionSystem.resolve_attack(attacker, defender, state=state)
    assert update.damage_taken > 0
    assert update.outcome_kind == "SURVIVE"
    assert update.alive_set is True

def test_defeat_outcome():
    # Non-lethal attack
    attacker = create_mock_entity(1, faction=1, atk=1000)
    defender = create_mock_entity(2, faction=2, hp=10, role=EntityRole.MONSTER)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})
    update = CombatResolutionSystem.resolve_attack(attacker, defender, state=state, is_lethal=False)
    assert update.outcome_kind == "DEFEAT"
    assert update.alive_set is False

def test_kill_outcome():
    # Lethal attack
    attacker = create_mock_entity(1, faction=1, atk=1000)
    defender = create_mock_entity(2, faction=2, hp=10, role=EntityRole.MONSTER)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})
    update = CombatResolutionSystem.resolve_attack(attacker, defender, state=state, is_lethal=True)
    assert update.outcome_kind == "KILL"
    assert update.alive_set is False

def test_opportunity_attack_outcome():
    attacker = create_mock_entity(1, faction=1)
    defender = create_mock_entity(2, faction=2)
    
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: defender})
    update = CombatResolutionSystem.resolve_opportunity_attack(attacker, defender, state=state)
    assert update.is_opportunity_attack is True
    assert update.is_lethal is False # OAs are usually non-lethal in this engine's tactical rules
    assert update.outcome_kind in ["SURVIVE", "DEFEAT"]
