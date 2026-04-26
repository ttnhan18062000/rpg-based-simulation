import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import EquipSlot

def test_warrior_starting_gear():
    # Warrior should have iron_sword in MAIN_HAND and leather_armor in TORSO
    warrior = V2EntityBuilder(entity_id=1).role(0).with_class("WARRIOR").build()
    
    slots = warrior.equipment.slots
    assert slots[EquipSlot.MAIN_HAND] == "iron_sword"
    assert slots[EquipSlot.TORSO] == "leather_armor"
    assert "power_strike" in warrior.identity.learned_skills

def test_mage_starting_gear():
    # Mage should have wooden_staff in MAIN_HAND
    mage = V2EntityBuilder(entity_id=1).role(0).with_class("MAGE").build()
    
    slots = mage.equipment.slots
    assert slots[EquipSlot.MAIN_HAND] == "wooden_staff"
    assert "fireball" in mage.identity.learned_skills

def test_rogue_starting_gear():
    # Rogue should have iron_dagger in MAIN_HAND
    rogue = V2EntityBuilder(entity_id=1).role(0).with_class("ROGUE").build()
    
    slots = rogue.equipment.slots
    assert slots[EquipSlot.MAIN_HAND] == "iron_dagger"
    assert "swift_reflexes" in rogue.identity.learned_skills
