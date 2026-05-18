import pytest
from unittest.mock import MagicMock
from src_legacy.core.entities.entity import Entity
from src_legacy.core.aspects.combat import CombatAspect
from src_legacy.core.aspects.progression import ProgressionAspect
from src_legacy.core.aspects.identity import IdentityAspect
from src_legacy.core.aspects.spatial import SpatialAspect
from src_legacy.core.aspects.interaction import InteractionAspect
from src_legacy.core.gameplay.attributes import Attributes, recalc_derived_stats
from src_legacy.actions.damage import PhysicalDamageCalculator, MagicalDamageCalculator
from src_legacy.actions.combat import DamageResolutionService
from src_legacy.core.models.enums import DamageType, Element
from src_legacy.core.models.vectors import Vector2

def test_stat_recalculation():
    """Verify that attributes correctly influence base stats."""
    entity = Entity(
        id=1, kind="hero",
        identity=IdentityAspect(traits=[]),
        combat=CombatAspect(atk_base=10, max_hp_base=100),
        progression=ProgressionAspect(),
        spatial=SpatialAspect(vision_range=6),
        interaction=InteractionAspect(loot_bonus=1.0)
    )
    
    # 10 STR should add 5 to atk_base (int(10 * 0.5))
    attrs = Attributes(str_=10, vit=0, end=0)
    recalc_derived_stats(entity, attrs)
    
    # Check if atk_base increased (10 + 5)
    assert entity.combat.atk_base == 15

def test_damage_resolution_math():
    """Verify the damage formula results."""
    # Create actual entities
    attacker = Entity(
        id=1, kind="hero",
        combat=CombatAspect(atk_base=100, luck=0, crit_rate=0),
        progression=ProgressionAspect(attributes=Attributes(str_=0))
    )
    
    defender = Entity(
        id=2, kind="hero",
        combat=CombatAspect(def_base=50, evasion=0),
        progression=ProgressionAspect(attributes=Attributes(vit=0)),
        spatial=SpatialAspect(pos=Vector2(0, 0))
    )
    
    world = MagicMock()
    world.tick = 100
    config = MagicMock()
    config.damage_variance = 0.0 # No variance for stable testing
    
    rng = MagicMock()
    rng.next_bool.return_value = False # No evasion, no crit
    rng.next_float.return_value = 0.5 # Mid-point variance
    
    # Resolution
    # atk_final = 100, def_final = 50
    # raw_damage = 100 * (100 / (100 + 100 + 1)) = 49.75 -> 49
    damage, is_crit, is_evaded, details = DamageResolutionService.resolve(
        attacker, defender, world, config, rng
    )
    
    assert damage == 49
    assert not is_crit
    assert not is_evaded
    assert details["mitigation"] == 51

def test_attribute_scaling_overlap():
    """Verify the 'double scaling' of attributes."""
    # PhysicalDamageCalculator adds a 2% mult per point of STR
    calc = PhysicalDamageCalculator()
    
    attacker = Entity(
        id=1, kind="hero",
        combat=CombatAspect(atk_base=100),
        progression=ProgressionAspect(attributes=Attributes(str_=10)),
        spatial=SpatialAspect(pos=Vector2(0, 0))
    )
    
    defender = Entity(
        id=2, kind="hero",
        combat=CombatAspect(def_base=0),
        progression=ProgressionAspect(attributes=Attributes(vit=0)),
        spatial=SpatialAspect(pos=Vector2(0, 0)) # No flanking
    )
    
    ctx = calc.resolve(attacker, defender)
    
    # atk_mult should be 1.0 + (10 * 0.02) = 1.2
    assert ctx.atk_mult == pytest.approx(1.2)
