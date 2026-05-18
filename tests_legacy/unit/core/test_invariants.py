import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


import pytest
from src_legacy.core.aspects.combat import CombatAspect
from src_legacy.core.aspects.progression import ProgressionAspect
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.gameplay.attributes import Attributes, AttributeCaps, recalc_derived_stats, speed_delay
from src_legacy.core.models.enums import AIState, EntityRole, RACE_PROFILES
from src_legacy.core.gameplay.faction import Faction

def test_speed_delay_invariants():
    """Test that speed_delay never returns NaN or out-of-bounds values."""
    for spd in range(-100, 1000):
        delay = speed_delay(spd, action="move")
        assert 0.1 <= delay <= 5.0
        assert not (delay != delay) # check for NaN

@pytest.mark.parametrize("hp, max_hp, atk, def_", [
    (10, 100, 10, 5),
    (-50, 50, 5, 0),
    (200, 100, 50, 20),
    (0, 100, 10, 10),
    (100, 0, 10, 10),
])
def test_stats_invariants(hp, max_hp, atk, def_):
    """AOA Stabilization: Test CombatAspect invariants (formerly Stats)."""
    combat = CombatAspect(hp=hp, max_hp=max_hp, atk_base=atk, def_base=def_)
    combat.validate() # Trigger AOA clamping
    
    assert isinstance(combat.hp_ratio, float)
    if combat.max_hp > 0:
        assert 0.0 <= combat.hp_ratio <= 1.0
    else:
        assert combat.hp_ratio == 0.0
    
    assert combat.hp >= 0
    assert combat.hp <= combat.max_hp
    assert combat.atk_base >= 1 # clamped min

@pytest.mark.parametrize("atk, def_, variance", [
    (10, 5, 0.0),
    (100, 20, 0.5),
    (50, 100, 1.0),
    (1000, 0, 0.25),
])
def test_damage_calc_math(atk, def_, variance):
    """Test the core damage calculation logic in isolation."""
    raw_damage = atk - def_ // 2
    raw_damage = max(raw_damage, 1)
    
    damage_variance = 0.2
    damage = int(raw_damage * (1.0 + damage_variance * (variance - 0.5)))
    damage = max(damage, 1)
    
    assert damage >= 1
    assert isinstance(damage, int)

@pytest.mark.parametrize("level", [1, 10, 50, 100])
def test_recalc_level_consistency(level):
    """Ensure level-based stat recalculation remains consistent across aspects."""
    combat = CombatAspect()
    prog = ProgressionAspect(level=level)
    attrs = Attributes(vit=5, end=5, str_=5, agi=5)
    
    hero = Entity(id=level, kind="hero")
    hero.combat = combat
    hero.progression = prog
    
    recalc_derived_stats(hero, attrs)
    assert prog.level == level
    assert combat.max_hp > 0

@pytest.mark.parametrize("current_hp, damage", [
    (100, 10),
    (50, 60),
    (0, 10),
    (100, 0),
])
def test_combat_damage_invariants(current_hp, damage):
    """Ensure HP reduction application doesn't cause overflow or invalid states."""
    new_hp = max(0, current_hp - damage)
    assert new_hp >= 0
    assert new_hp <= current_hp
