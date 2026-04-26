import pytest
from src_legacy.core.builder import V2EntityBuilder
from src_legacy.core.classes import CLASS_REGISTRY
from src_legacy.core.skills import SKILL_REGISTRY

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
def test_builder_class_integration():
    # 1. Build a Warrior
    builder = V2EntityBuilder(1).with_class("WARRIOR")
    warrior = builder.build()
    
    assert warrior.identity.class_id == "WARRIOR"
    assert "power_strike" in warrior.identity.learned_skills
    
    # Warrior base_hp (150) + defaults (VIT 5 -> +10, END 5 -> +2) = 162
    assert warrior.combat.max_hp == 162
    # Warrior base_atk (15) + defaults (STR 5 -> +2 ATK) = 17
    assert warrior.combat.atk == 17

@pytest.mark.v2_contract
def test_builder_mage_integration():
    # 1. Build a Mage
    builder = V2EntityBuilder(2).with_class("MAGE")
    mage = builder.build()
    
    assert mage.identity.class_id == "MAGE"
    assert "fireball" in mage.identity.learned_skills
    
    # Mage base_hp (80) + defaults (VIT 5 -> +10, END 5 -> +2) = 92
    assert mage.combat.max_hp == 92
    # Mage base_atk (20) + defaults (STR 5 -> +2 ATK) = 22
    assert mage.combat.atk == 22
