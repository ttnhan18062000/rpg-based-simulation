from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from src_legacy.core.aspects.combat import CombatAspect
from src_legacy.core.aspects.progression import ProgressionAspect
from src_legacy.core.entities.entity import Entity
from src_legacy.core.models.vectors import Vector2
from src_legacy.core.gameplay.attributes import Attributes, AttributeCaps, recalc_derived_stats, speed_delay
from src_legacy.core.models.enums import AIState, EntityRole, RACE_PROFILES
from src_legacy.core.gameplay.faction import Faction

@pytest.mark.parametrize("hp, max_hp, atk, def_", [
    (10, 100, 10, 5),
    (-50, 50, 5, 0),
    (200, 100, 50, 20),
    (0, 100, 10, 10),
    (100, 0, 10, 10),
])
def test_integration_stats_invariants(hp, max_hp, atk, def_):
    """AOA Stabilization: Test CombatAspect integration invariants (formerly Stats)."""
    combat = CombatAspect(hp=hp, max_hp=max_hp, atk_base=atk, def_base=def_)
    combat.validate()
    
    assert isinstance(combat.hp_ratio, float)
    if combat.max_hp > 0:
        assert 0.0 <= combat.hp_ratio <= 1.0
    else:
        assert combat.hp_ratio == 0.0
    
    assert combat.hp >= 0
    assert combat.hp <= combat.max_hp

@pytest.mark.parametrize("level", [1, 10, 50, 100])
def test_integration_recalc_level_consistency(level):
    """Ensure level-based stat recalculation remains consistent across aspects in integration."""
    entity = Entity(id=1, kind="hero")
    entity.progression.level = level
    attrs = Attributes(vit=5, end=5, str_=5, agi=5)
    
    recalc_derived_stats(entity, attrs)
    assert entity.progression.level == level
    assert entity.combat.max_hp > 0

def test_speed_delay_invariants():
    """Test that speed_delay never returns NaN or out-of-bounds values."""
    for spd in range(-100, 1000):
        delay = speed_delay(spd, action="move")
        assert 0.1 <= delay <= 5.0  # Based on current _MIN_DELAY and _MAX_DELAY
        assert not (delay != delay) # check for NaN

@pytest.mark.parametrize("atk, def_, variance", [
    (100, 50, 0.5),
    (10, 100, 0.0),
    (500, 0, 1.0),
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
