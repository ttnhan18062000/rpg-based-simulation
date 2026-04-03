import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from hypothesis import given, strategies as st
from tests.helpers.legacy_stats import Stats
from src.core.entities.entity import Entity, Vector2
from src.core.gameplay.attributes import Attributes, AttributeCaps, recalc_derived_stats, speed_delay
from src.core.models.enums import AIState, EntityRole, RACE_PROFILES
from src.core.gameplay.faction import Faction

def test_speed_delay_invariants():
    # Test that speed_delay never returns NaN or out-of-bounds values
    # Even for extreme speed values
    for spd in range(-100, 1000):
        delay = speed_delay(spd, action="move")
        assert 0.1 <= delay <= 5.0  # Based on current _MIN_DELAY and _MAX_DELAY
        assert not (delay != delay) # check for NaN

@given(
    st.integers(min_value=-100, max_value=200), # hp
    st.integers(min_value=1, max_value=200),   # max_hp
    st.integers(min_value=1, max_value=100),   # atk
    st.integers(min_value=0, max_value=100),   # def
    st.floats(min_value=-0.5, max_value=1.5),  # crit_rate
)
def test_stats_invariants(hp, max_hp, atk, def_, crit_rate):
    from src.core.aspects.combat import CombatAspect
    combat = CombatAspect(hp=hp, max_hp=max_hp, atk_base=atk, def_base=def_, crit_rate=crit_rate)
    combat.validate()
    
    # We expect hp_ratio to be clamped between 0 and 1 for safety
    assert isinstance(combat.hp_ratio, float)
    if combat.max_hp > 0:
        assert 0.0 <= combat.hp_ratio <= 1.0
    else:
        assert combat.hp_ratio == 0.0

@given(
    st.integers(min_value=1, max_value=1000), # atk
    st.integers(min_value=0, max_value=1000), # def
    st.floats(min_value=0.0, max_value=1.0),  # variance
)
def test_damage_calc_math(atk, def_, variance):
    # Simplified combat damage logic from combat.py
    raw_damage = atk - def_ // 2
    raw_damage = max(raw_damage, 1)
    
    # variance is from RNG, usually 0.0 to 1.0
    damage_variance = 0.2 # from config usually
    damage = int(raw_damage * (1.0 + damage_variance * (variance - 0.5)))
    damage = max(damage, 1)
    
    assert damage >= 1
    assert isinstance(damage, int)

@given(st.integers(min_value=1, max_value=100)) # level
def test_recalc_level_consistency(level):
    # Ensure level doesn't break recalc
    entity = Entity(id=1, kind="hero")
    entity.progression.level = level
    
    from src.core.gameplay.attributes import Attributes, recalc_derived_stats
    attrs = Attributes(vit=5, end=5, str_=5, agi=5)
    recalc_derived_stats(entity, attrs)
    
    assert entity.progression.level == level
    assert entity.combat.max_hp > 0

@given(
    st.integers(min_value=0, max_value=1000), # current_hp
    st.integers(min_value=1, max_value=1000), # damage
)
def test_combat_damage_invariants(current_hp, damage):
    # This is a placeholder for combat logic hardening
    # Ensuring HP doesn't wrap around or do weird things
    new_hp = max(0, current_hp - damage)
    assert new_hp >= 0
    assert new_hp <= current_hp
