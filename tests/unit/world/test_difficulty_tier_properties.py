"""Difficulty-tier properties no other test pins: the zone boundaries, the empty-zones fallback, the tier set and the growth of every stat.

Sources: src/world/spawn_config.py (DIFFICULTY_TIERS, DIFFICULTY_ZONES), src/world/regions.py (RegionService.get_difficulty_tier_at).
"""
import dataclasses

import pytest

from src.world import regions
from src.world.regions import RegionService
from src.world.spawn_config import DIFFICULTY_TIERS, DIFFICULTY_ZONES


def test_zone_boundaries_belong_to_the_inner_tier_and_the_next_step_to_the_outer():
    """Each boundary distance is inside its own zone (<=); one step past it is the next tier."""
    assert DIFFICULTY_ZONES == ((80, 1), (150, 2), (220, 3), (999, 4))
    assert [RegionService.get_difficulty_tier_at((d, 0)) for d in (80, 150, 220, 999)] == [1, 2, 3, 4]
    assert [RegionService.get_difficulty_tier_at((d + 0.01, 0)) for d in (80, 150, 220)] == [2, 3, 4]


def test_beyond_the_last_zone_falls_back_to_the_top_ordinary_tier():
    assert RegionService.get_difficulty_tier_at((5000, 0)) == 4


def test_empty_zones_default_to_the_top_ordinary_tier(monkeypatch):
    monkeypatch.setattr(regions, "DIFFICULTY_ZONES", ())
    assert RegionService.get_difficulty_tier_at((0, 0)) == 4
    assert RegionService.get_difficulty_tier_at((500, 500)) == 4


def test_every_tier_one_to_five_has_multipliers():
    assert set(DIFFICULTY_TIERS) == {1, 2, 3, 4, 5}


@pytest.mark.parametrize("field", [f.name for f in dataclasses.fields(next(iter(DIFFICULTY_TIERS.values())))])
def test_every_multiplier_is_non_decreasing_from_tier_one_to_five(field):
    values = [getattr(DIFFICULTY_TIERS[t], field) for t in (1, 2, 3, 4, 5)]
    assert values == sorted(values), f"{field} falls between tiers: {values}"
    assert values[-1] > values[0], f"{field} never grows: {values}"
