import pytest

from src.core.builder import V2EntityBuilder
from src.core.classes import CLASS_REGISTRY
from src.core.skills import SKILL_REGISTRY
from src.core.state import EquipSlot
from src.core.enums import EntityRole, Faction


def _normalize_gear_slots(starting_gear: dict) -> dict[EquipSlot, str]:
    """
    Normalize CLASS_REGISTRY starting gear into EquipmentComponent slot format.

    Supports both:
        {"MAIN_HAND": "iron_sword"}
    and:
        {EquipSlot.MAIN_HAND: "iron_sword"}
    """
    slots = {}

    for slot, item_id in starting_gear.items():
        if isinstance(slot, EquipSlot):
            slots[slot] = item_id
        else:
            slots[EquipSlot[slot]] = item_id

    return slots


def make_class_entity(entity_id: int, class_id: str):
    """
    Build a classed hero using the new explicit V2 builder style.

    New builder rule:
        `.identity(class_id=...)` only stores the class id.
        It does not automatically apply class registry stats, skills, or gear.

    Therefore this helper explicitly reads CLASS_REGISTRY and injects:
        - class_id
        - learned_skills
        - starting gear
        - base combat stats

    Fraud this catches:
        - tests accidentally assume hidden builder behavior
        - registry contains correct class data but entity setup forgets to apply it
        - class skills/gear silently disappear during builder cleanup
    """
    class_def = CLASS_REGISTRY[class_id]

    return (
        V2EntityBuilder(entity_id)
        .kind("hero")
        .identity(
            role=EntityRole.HERO,
            faction=Faction.HERO_GUILD,
            class_id=class_id,
            learned_skills=set(class_def.starting_skills),
        )
        .combat(
            hp=class_def.base_hp,
            max_hp=class_def.base_hp,
            atk=class_def.base_atk,
            def_stat=getattr(class_def, "base_def", 0),
            alive=True,
            readiness=100.0,
        )
        .equipment(
            slots=_normalize_gear_slots(getattr(class_def, "starting_gear", {}))
        )
        .lifecycle(active=True)
        .build()
    )


@pytest.mark.v2_contract
def test_class_registry_lookup():
    assert "WARRIOR" in CLASS_REGISTRY

    w_defn = CLASS_REGISTRY["WARRIOR"]

    assert w_defn.base_hp == 150
    assert "power_strike" in w_defn.starting_skills


@pytest.mark.v2_contract
def test_skill_registry_lookup():
    assert "fireball" in SKILL_REGISTRY

    f_defn = SKILL_REGISTRY["fireball"]

    assert f_defn.power == 2.0
    assert f_defn.cost == 25


@pytest.mark.v2_contract
def test_builder_stores_class_id_without_hidden_registry_application():
    """
    Verify the clean builder only stores class_id.

    This intentionally replaces the old expectation that
    `.identity(class_id="WARRIOR")` automatically applies class stats,
    learned skills, and gear.
    """
    warrior = (
        V2EntityBuilder(1)
        .kind("hero")
        .identity(
            role=EntityRole.HERO,
            faction=Faction.HERO_GUILD,
            class_id="WARRIOR",
        )
        .build()
    )

    assert warrior.identity.class_id == "WARRIOR"


@pytest.mark.v2_contract
def test_explicit_warrior_class_application():
    warrior = make_class_entity(1, "WARRIOR")

    assert warrior.identity.class_id == "WARRIOR"
    assert "power_strike" in warrior.identity.learned_skills

    assert warrior.combat.max_hp == 150
    assert warrior.combat.atk == 15

    assert warrior.equipment.slots[EquipSlot.MAIN_HAND] == "iron_sword"
    assert warrior.equipment.slots[EquipSlot.TORSO] == "leather_armor"


@pytest.mark.v2_contract
def test_explicit_mage_class_application():
    mage = make_class_entity(2, "MAGE")

    assert mage.identity.class_id == "MAGE"
    assert "fireball" in mage.identity.learned_skills

    assert mage.combat.max_hp == 80
    assert mage.combat.atk == 20

    assert mage.equipment.slots[EquipSlot.MAIN_HAND] == "wooden_staff"