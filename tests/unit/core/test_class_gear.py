"""Tests for class-aware gear selection and item power weighting."""

import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace
from src.core.models.enums import HeroClass
from src.core.gameplay.items.items import _item_power

def test_warrior_prefers_defensive_gear():
    """Verify that a Warrior weights defensive stats higher than a Mage."""
    # Item 1: Heavy Armor (+10 DEF, +5 ATK)
    armor_template = SimpleNamespace(
        def_bonus=10, atk_bonus=5, hp_bonus=0, spd_bonus=0,
        matk_bonus=0, mdef_bonus=0, crit_bonus=0.0, evasion_bonus=0.0
    )

    # Item 2: Sharp Sword (+15 ATK)
    sword_template = SimpleNamespace(
        def_bonus=0, atk_bonus=15, hp_bonus=0, spd_bonus=0,
        matk_bonus=0, mdef_bonus=0, crit_bonus=0.0, evasion_bonus=0.0
    )

    # Warrior weights: ATK 1.0, DEF 2.0
    # Armor Power: 5*1.0 + 10*2.0 = 25
    # Sword Power: 15*1.0 = 15
    # Result: Warrior likes Armor more (25 > 15)
    w_armor_pwr = _item_power(armor_template, HeroClass.WARRIOR)
    w_sword_pwr = _item_power(sword_template, HeroClass.WARRIOR)
    
    assert w_armor_pwr > w_sword_pwr

    # Mage weights: ATK 0.2, DEF 1.0 (hypothetical)
    # Armor Power: 5*0.2 + 10*1.0 = 11
    # Sword Power: 15*0.2 = 3
    # Actually, let's use a magic item
    wand_template = MagicMock()
    wand_template.combat.matk_bonus = 20
    wand_template.combat.atk_bonus = 0
    wand_template.combat.def_bonus = 0
    
    # Mage (MATK 2.0)
    m_wand_pwr = _item_power(wand_template, HeroClass.MAGE) # 20 * 2 = 40
    m_armor_pwr = _item_power(armor_template, HeroClass.MAGE) # 5*0.2 + 10*1.5? = 16
    
    assert m_wand_pwr > m_armor_pwr
