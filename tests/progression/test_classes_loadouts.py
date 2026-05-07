import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import EquipSlot
from src.core.enums import EntityRole, Faction


def make_class_entity(entity_id: int, class_id: str):
    """
    Build a classed hero with explicit class loadout.

    New builder rule:
        `.identity(class_id=...)` only stores the class id.
        Starting gear and learned skills must be injected explicitly unless
        the builder provides a dedicated class helper.

    Fraud this catches:
        - test assumes class_id alone grants gear
        - class loadout and skill setup silently disappear during builder cleanup
    """
    if class_id == "WARRIOR":
        gear = {
            EquipSlot.MAIN_HAND: "iron_sword",
            EquipSlot.TORSO: "leather_armor",
        }
        skills = {"power_strike"}
    elif class_id == "MAGE":
        gear = {
            EquipSlot.MAIN_HAND: "wooden_staff",
        }
        skills = {"fireball"}
    elif class_id == "ROGUE":
        gear = {
            EquipSlot.MAIN_HAND: "iron_dagger",
        }
        skills = {"swift_reflexes"}
    else:
        raise ValueError(f"Unsupported class_id: {class_id}")

    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .identity(
            role=EntityRole.HERO,
            faction=Faction.HERO_GUILD,
            class_id=class_id,
            learned_skills=skills,
        )
        .equipment(slots=gear)
        .build()
    )


def test_warrior_starting_gear():
    warrior = make_class_entity(1, "WARRIOR")

    slots = warrior.equipment.slots
    assert slots[EquipSlot.MAIN_HAND] == "iron_sword"
    assert slots[EquipSlot.TORSO] == "leather_armor"
    assert "power_strike" in warrior.identity.learned_skills


def test_mage_starting_gear():
    mage = make_class_entity(1, "MAGE")

    slots = mage.equipment.slots
    assert slots[EquipSlot.MAIN_HAND] == "wooden_staff"
    assert "fireball" in mage.identity.learned_skills


def test_rogue_starting_gear():
    rogue = make_class_entity(1, "ROGUE")

    slots = rogue.equipment.slots
    assert slots[EquipSlot.MAIN_HAND] == "iron_dagger"
    assert "swift_reflexes" in rogue.identity.learned_skills