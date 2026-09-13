"""
tests/unit/domains/combat_engagement/test_power.py

TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER

Unit tests for src/domains/combat_engagement/power.py: true_power, apparent_power,
deterministic_observation_noise, gap_uncertainty.
"""

from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, BiologicalComponent
from src.domains.combat_engagement.power import (
    true_power,
    apparent_power,
    deterministic_observation_noise,
    gap_uncertainty,
    UNCERTAINTY_FLOOR,
    UNCERTAINTY_CEILING,
)


def _entity(e_id, hp=100, max_hp=100, atk=10, def_stat=2):
    b = V2EntityBuilder(e_id)
    b.replace_combat(CombatComponent(hp=hp, max_hp=max_hp, atk=atk, def_stat=def_stat))
    b.replace_biological(BiologicalComponent(hunger=0.0, sleep_debt=0.0))
    b.identity(evolution_level=1)
    return b.build()


def test_true_power_matches_d11_formula_exactly():
    entity = _entity(1, hp=100, max_hp=100, atk=10, def_stat=4)
    # 10 + 4*0.5 + 100*0.1 = 10 + 2 + 10 = 22
    assert true_power(entity) == 22.0


def test_true_power_excludes_evolution_level():
    """
    Two entities with identical combat stats but different evolution_level must report identical
    true_power -- evolution_level is deliberately excluded (double-counts via Attribute Points).
    """
    b1 = V2EntityBuilder(1)
    b1.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=4))
    b1.identity(evolution_level=1)
    e1 = b1.build()

    b2 = V2EntityBuilder(2)
    b2.replace_combat(CombatComponent(hp=100, max_hp=100, atk=10, def_stat=4))
    b2.identity(evolution_level=5)
    e2 = b2.build()

    assert true_power(e1) == true_power(e2)


def test_apparent_power_healthy_equals_true_power():
    entity = _entity(1, hp=100, max_hp=100, atk=10, def_stat=4)
    assert apparent_power(entity) == true_power(entity)


def test_apparent_power_wounded_is_reduced():
    entity = _entity(1, hp=60, max_hp=100, atk=10, def_stat=4)  # hp_ratio 0.6 -> wounded band
    assert apparent_power(entity) == true_power(entity) * 0.85


def test_apparent_power_critical_is_more_reduced():
    entity = _entity(1, hp=20, max_hp=100, atk=10, def_stat=4)  # hp_ratio 0.2 -> critical band
    assert apparent_power(entity) == true_power(entity) * 0.6


def test_deterministic_noise_is_bit_identical_for_same_inputs():
    n1 = deterministic_observation_noise(seed=42, tick=10, observer_id=1, observed_id=2)
    n2 = deterministic_observation_noise(seed=42, tick=10, observer_id=1, observed_id=2)
    assert n1 == n2


def test_deterministic_noise_differs_across_changed_inputs():
    base = deterministic_observation_noise(seed=42, tick=10, observer_id=1, observed_id=2)
    diff_seed = deterministic_observation_noise(seed=43, tick=10, observer_id=1, observed_id=2)
    diff_tick = deterministic_observation_noise(seed=42, tick=11, observer_id=1, observed_id=2)
    diff_observer = deterministic_observation_noise(seed=42, tick=10, observer_id=2, observed_id=2)
    diff_observed = deterministic_observation_noise(seed=42, tick=10, observer_id=1, observed_id=3)

    assert len({base, diff_seed, diff_tick, diff_observer, diff_observed}) == 5


def test_deterministic_noise_is_bounded():
    for seed in range(5):
        for tick in range(5):
            n = deterministic_observation_noise(seed=seed, tick=tick, observer_id=1, observed_id=2)
            assert -1.0 <= n < 1.0


def test_gap_uncertainty_is_maximal_at_zero_gap():
    uncertainty_at_zero = gap_uncertainty(gap=0.0, perception=50.0)
    assert abs(uncertainty_at_zero - UNCERTAINTY_CEILING) < 1e-6


def test_gap_uncertainty_approaches_floor_at_large_gap():
    uncertainty_at_large_gap = gap_uncertainty(gap=500.0, perception=50.0)
    assert abs(uncertainty_at_large_gap - UNCERTAINTY_FLOOR) < 1e-3


def test_gap_uncertainty_is_monotonically_decreasing_in_gap():
    small_gap = gap_uncertainty(gap=1.0, perception=50.0)
    medium_gap = gap_uncertainty(gap=10.0, perception=50.0)
    large_gap = gap_uncertainty(gap=50.0, perception=50.0)
    assert small_gap > medium_gap > large_gap


def test_higher_perception_sharpens_faster_at_fixed_gap():
    """A higher-PER observer needs a smaller gap before its estimate sharpens (Sec 13.3)."""
    fixed_gap = 10.0
    low_per = gap_uncertainty(gap=fixed_gap, perception=1.0)
    high_per = gap_uncertainty(gap=fixed_gap, perception=99.0)
    assert high_per < low_per
