import pytest
from src_v2.core.state import EntityState, IdentityComponent, CombatComponent
from src_v2.engine.combat import CombatResolutionSystem

def create_mock_entity(eid, atk=10, dfn=5, hp=100):
    return EntityState(
        id=eid,
        kind="hero",
        position=(0, 0),
        identity=IdentityComponent(faction=1),
        combat=CombatComponent(hp=hp, max_hp=hp, atk=atk, def_stat=dfn)
    )

def test_combat_damage_calculation():
    # Formula: damage = atk * (atk / (atk + def * 2.0 + 1.0))
    # atk=10, def=5 => 10 * (10 / (10 + 10 + 1)) = 10 * (10/21) = 10 * 0.476 = 4.76 => 4
    attacker = create_mock_entity(1, atk=10)
    defender = create_mock_entity(2, dfn=5)
    
    damage = CombatResolutionSystem.calculate_damage(attacker, defender)
    assert damage == 4

def test_survival_outcome():
    attacker = create_mock_entity(1, atk=10)
    defender = create_mock_entity(2, hp=100)
    
    update = CombatResolutionSystem.resolve_attack(attacker, defender)
    assert update.damage_taken > 0
    assert update.outcome_kind == "SURVIVE"
    assert update.alive_set is True

def test_defeat_outcome():
    # Non-lethal attack
    attacker = create_mock_entity(1, atk=1000)
    defender = create_mock_entity(2, hp=10)
    
    update = CombatResolutionSystem.resolve_attack(attacker, defender, is_lethal=False)
    assert update.outcome_kind == "DEFEAT"
    assert update.alive_set is False

def test_kill_outcome():
    # Lethal attack
    attacker = create_mock_entity(1, atk=1000)
    defender = create_mock_entity(2, hp=10)
    
    update = CombatResolutionSystem.resolve_attack(attacker, defender, is_lethal=True)
    assert update.outcome_kind == "KILL"
    assert update.alive_set is False

def test_opportunity_attack_outcome():
    attacker = create_mock_entity(1)
    defender = create_mock_entity(2)
    
    update = CombatResolutionSystem.resolve_opportunity_attack(attacker, defender)
    assert update.is_opportunity_attack is True
    assert update.is_lethal is False # OAs are usually non-lethal in this engine's tactical rules
    assert update.outcome_kind in ["SURVIVE", "DEFEAT"]
