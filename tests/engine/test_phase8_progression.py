# tests/engine/test_phase8_progression.py
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, AttributeComponent, CombatComponent, EquipmentComponent, EquipSlot, AptitudeComponent, InventoryComponent
from src.core.updates import StateUpdate, EntityUpdate, IdentityUpdate, AttributeUpdate, EquipmentUpdate, RewardUpdate
from src.engine.evolution import EvolutionSystem
from src.engine.apply import ApplyPath
from src.core.enums import EntityRole

from src.core.builder import V2EntityBuilder

def test_evolution_level_up_hero():
    """Verify that a Hero levels up and unlocks skills at milestones."""
    entity = (V2EntityBuilder(1)
              .kind("HERO")
              .location(0.0, 0.0)
              .identity(role=EntityRole.HERO, evolution_level=1, evolution_points=0)
              .attributes(vitality=5, strength=5)
              .combat(hp=110)
              .combat(atk=12)
              .build())
    state = AuthoritativeState(entities={1: entity}, tick=0, seed=0)
    
    # Give enough XP to reach Level 5
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, identity=IdentityUpdate(evolution_points_delta=1800))
    })
    
    result_upd = EvolutionSystem.evaluate(state, update)
    final_state = ApplyPath.apply_generation(state, result_upd)
    
    hero = final_state.entities[1]
    assert hero.identity.evolution_level >= 5
    assert "power_strike" in hero.identity.learned_skills
    assert hero.identity.unspent_ap > 0

def test_equipment_stat_derivation():
    """Verify that equipping items updates combat stats via ApplyPath."""
    entity = (V2EntityBuilder(1)
              .kind("HERO")
              .location(0.0, 0.0)
              .attributes(strength=10)
              .combat(atk=15, range=1)
              .build())
    state = AuthoritativeState(entities={1: entity}, tick=0, seed=0)
    
    # Equip an iron_sword (+10 ATK, Range 1)
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, equipment=EquipmentUpdate(slot_updates={EquipSlot.MAIN_HAND: "iron_sword"}))
    })
    
    final_state = ApplyPath.apply_generation(state, update)
    hero = final_state.entities[1]
    
    assert hero.combat.atk == 25 # 15 base + 10 gear
    assert hero.equipment.slots[EquipSlot.MAIN_HAND] == "iron_sword"

def test_passive_skill_bonus():
    """Verify that learning a passive skill updates combat stats."""
    entity = (V2EntityBuilder(1)
              .kind("HERO")
              .location(0.0, 0.0)
              .attributes(agility=10)
              .combat(evasion=0.06)
              .build())
    state = AuthoritativeState(entities={1: entity}, tick=0, seed=0)
    
    # Learn swift_reflexes (+0.1 evasion)
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, identity=IdentityUpdate(learned_skills=["swift_reflexes"]))
    })
    
    final_state = ApplyPath.apply_generation(state, update)
    hero = final_state.entities[1]
    
    assert pytest.approx(hero.combat.evasion) == 0.16 # 0.06 base + 0.1 skill

def test_attribute_stat_scaling():
    """Verify that increasing attributes updates combat stats."""
    entity = (V2EntityBuilder(1)
              .kind("HERO")
              .location(0.0, 0.0)
              .attributes(strength=10)
              .combat(atk=15)
              .build())
    state = AuthoritativeState(entities={1: entity}, tick=0, seed=0)
    
    # Increase strength by 20 -> ATK should increase by 10
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, attributes=AttributeUpdate(strength_delta=20))
    })
    
    final_state = ApplyPath.apply_generation(state, update)
    hero = final_state.entities[1]
    
    assert hero.combat.atk == 25
    assert hero.attributes.strength == 30
