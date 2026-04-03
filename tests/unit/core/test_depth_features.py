import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import pytest
from src.core.entities.entity import Entity, Vector2
from src.core.gameplay.effects import well_rested_effect, StatusEffect, EffectType
from src.core.models.enums import HeroClass
from src.core.gameplay.items.items import _item_power
from src.core.gameplay.attributes import Attributes
from src.core.aspects.combat import CombatAspect
from src.core.aspects.spatial import SpatialAspect
from src.core.aspects.identity import IdentityAspect
from src.core.aspects.progression import ProgressionAspect

def test_well_rested_effect_application():
    """Verify that the Well-Rested buff correctly affects Max HP and XP mult."""
    combat = CombatAspect(max_hp=100)
    spatial = SpatialAspect(pos=Vector2(0, 0))
    identity = IdentityAspect()
    progression = ProgressionAspect(level=1)
    
    e = Entity(id=1, kind="hero", aspects={
        "combat": combat,
        "spatial": spatial,
        "identity": identity,
        "progression": progression
    })
    
    # 1. Base state
    assert e.combat.max_hp == 100
    assert abs(e.stats.progression.xp_mult - 1.0) < 0.001
    
    # 2. Add Well-Rested buff
    buff = well_rested_effect()
    e.effects.append(buff)
    
    # Well-Rested gives +10% Max HP and +20% XP mult
    assert e.combat.max_hp == 110
    assert abs(e.stats.progression.xp_mult - 1.2) < 0.001

def test_attribute_synergy_xp_mult():
    """Verify that Wisdom/Intelligence correctly affects XP multiplier."""
    combat = CombatAspect()
    identity = IdentityAspect()
    attrs = Attributes(wis=20, int_=20)
    progression = ProgressionAspect(level=1, attributes=attrs)
    
    e = Entity(id=2, kind="hero", aspects={
        "combat": combat,
        "identity": identity,
        "progression": progression
    })
    
    # Base XP is 1.30 at 20/20 (Formula: 1.0 + 20*0.01 + 20*0.005 = 1.30)
    mult = e.stats.progression.xp_mult
    assert abs(mult - 1.30) < 0.001
    
    # Add Well-Rested (* 1.2)
    e.effects.append(well_rested_effect())
    # 1.30 * 1.2 = 1.56
    assert abs(e.stats.progression.xp_mult - 1.56) < 0.001

def test_class_weighted_gear():
    """Verify that item power is correctly weighted for different classes."""
    from types import SimpleNamespace
    
    # Mock item template
    t = SimpleNamespace(
        item_type=1, # Weapon
        atk_bonus=20,
        matk_bonus=0,
        str_bonus=10,
        intl_bonus=10,
        agi_bonus=0,
        vit_bonus=0,
        spi_bonus=0,
        wis_bonus=0,
        end_bonus=0,
        per_bonus=0,
        cha_bonus=0,
        luck_bonus=0,
        crit_bonus=0,
        evasion_bonus=0,
        max_hp_bonus=0,
        max_stamina_bonus=0,
        speed_bonus=0,
        rarity=1,
        level=1,
        id=100
    )
    
    pow_warrior = _item_power(t, HeroClass.WARRIOR)
    pow_mage = _item_power(t, HeroClass.MAGE)
    
    assert pow_warrior > pow_mage
