import pytest
from src_legacy.core.entities.entity import Entity
from src_legacy.core.aspects.combat import CombatAspect
from src_legacy.core.aspects.progression import ProgressionAspect
from src_legacy.core.aspects.identity import IdentityAspect
from src_legacy.core.aspects.spatial import SpatialAspect
from src_legacy.core.aspects.interaction import InteractionAspect
from src_legacy.core.gameplay.attributes import Attributes, AttributeCaps, recalc_derived_stats, train_attributes
from src_legacy.core.models.enums import TacticalRole, HeroClass

def test_initial_role_derivation():
    """Verify that a newly created entity derives its tactical role from its class."""
    entity = Entity(
        id=1, kind="hero",
        identity=IdentityAspect(hero_class=HeroClass.RANGER),
        progression=ProgressionAspect(hero_class=HeroClass.RANGER, attributes=Attributes()),
        combat=CombatAspect(),
        spatial=SpatialAspect(),
        interaction=InteractionAspect()
    )
    
    # Check if role was set to RANGED_SKIRMISHER during on_attach (triggered by model_post_init)
    assert entity.progression.tactical_role == TacticalRole.RANGED_SKIRMISHER

def test_dynamic_role_transition_with_hysteresis():
    """Verify that roles change only after hitting the hysteresis threshold."""
    # Start as Warrior
    entity = Entity(
        id=1, kind="hero",
        identity=IdentityAspect(hero_class=HeroClass.WARRIOR),
        progression=ProgressionAspect(hero_class=HeroClass.WARRIOR, attributes=Attributes(str_=10, vit=10, agi=5)),
        combat=CombatAspect(),
        spatial=SpatialAspect(),
        interaction=InteractionAspect()
    )
    
    # Trigger initial recalc
    recalc_derived_stats(entity, entity.progression.attributes)
    assert entity.progression.tactical_role == TacticalRole.MELEE_STRIKER
    # Initial stability should be higher than 0
    assert entity.progression.role_stability > 0
    
    # Pump Agility to 40 (Way higher than STR 10)
    # Ideal role should now be RANGED_SKIRMISHER
    # But hysteresis should keep it as MELEE_STRIKER for a few ticks
    entity.progression.attributes.agi = 40
    
    # 1st Recalc: stability should drop
    old_stability = entity.progression.role_stability
    recalc_derived_stats(entity, entity.progression.attributes)
    assert entity.progression.tactical_role == TacticalRole.MELEE_STRIKER
    assert entity.progression.role_stability < old_stability
    
    # Recalc until it flips (should take about 5 calls if stability started at 5)
    for _ in range(10):
        recalc_derived_stats(entity, entity.progression.attributes)
        if entity.progression.tactical_role == TacticalRole.RANGED_SKIRMISHER:
            break
            
    assert entity.progression.tactical_role == TacticalRole.RANGED_SKIRMISHER

def test_specialized_training_soft_caps():
    """Verify that 'off-role' stats train slower than 'on-role' stats."""
    # MELEE_STRIKER (Warrior)
    warrior = Entity(
        id=1, kind="hero",
        identity=IdentityAspect(hero_class=HeroClass.WARRIOR),
        progression=ProgressionAspect(
            level=1, 
            hero_class=HeroClass.WARRIOR, 
            attributes=Attributes(str_=29, int_=11), # Just below soft caps
            attribute_caps=AttributeCaps(str_cap=100, int_cap=100),
            aptitudes={"str": 1.0, "int": 1.0}
        ),
        combat=CombatAspect(),
        spatial=SpatialAspect(),
        interaction=InteractionAspect()
    )
    
    # Recalc to set role
    recalc_derived_stats(warrior, warrior.progression.attributes)
    assert warrior.progression.tactical_role == TacticalRole.MELEE_STRIKER
    
    # STR Soft Limit for Primary (Lv1): 1*10 + 20 = 30
    # INT Soft Limit for Off-Role (Lv1): 1*2 + 10 = 12
    
    # 1. Train STR. Should be 100% until 30.
    train_attributes(warrior, "attack") # str gain: 0.015
    assert warrior.progression.attributes._str_frac == pytest.approx(0.015)
    
    # Increase STR above 30
    warrior.progression.attributes.str_ = 31
    train_attributes(warrior, "attack") 
    # Current STR >= 30, so rate should be 0.015 * 0.5 = 0.0075
    # Total frac = 0.015 + 0.0075 = 0.0225
    assert warrior.progression.attributes._str_frac == pytest.approx(0.0225)
    
    # 2. Train INT. Should slow down sooner.
    # Current INT = 11. Soft cap is 12.
    train_attributes(warrior, "skill") # int gain: 0.010
    assert warrior.progression.attributes._int_frac == pytest.approx(0.010)
    
    # Increase INT above 12
    warrior.progression.attributes.int_ = 13
    train_attributes(warrior, "skill")
    # Current INT >= 12, so rate should be 0.010 * 0.5 = 0.005
    # Total frac = 0.010 + 0.005 = 0.015
    assert warrior.progression.attributes._int_frac == pytest.approx(0.015)

def test_output_derived_stat_ceilings():
    """Verify that final derived stats (ATK, HP, etc.) have soft caps."""
    # Create a god-like entity
    god = Entity(
        id=1, kind="hero",
        combat=CombatAspect(atk_base=0, max_hp_base=0),
        progression=ProgressionAspect(
            attributes=Attributes(str_=200, vit=200, end=200),
            tactical_role=TacticalRole.MELEE_STRIKER
        ),
        spatial=SpatialAspect(),
        interaction=InteractionAspect()
    )
    
    # ATK Formula: base_atk + int(str * 0.5)
    # STR 200 -> +100 ATK.
    # Soft cap for ATK is 40.
    # Formula: cap (40) + overflow (60) * 0.5 (until 2x cap) + further overflow * 0.1
    # overflow 40 to 80 (Stage 2): 40 * 0.5 = 20. Total = 60.
    # extreme overflow 20 (Stage 3): 20 * 0.1 = 2. Total = 62.
    
    recalc_derived_stats(god, god.progression.attributes)
    
    # ATK: Expected ~62
    assert god.combat.atk_base == 62
    
    # HP: Max HP = 2 * VIT + 0.5 * END = 2*200 + 100 = 500
    # Soft cap for HP is 200.
    # Stage 2: 200 * 0.5 = 100. Total = 300.
    # Stage 3: (500 - 400) * 0.1 = 10. Total = 310.
    assert god.combat.max_hp == 310
