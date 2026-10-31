"""A calamity's intensity raises the regional hazard drain an entity takes: drain = int(hazard_level * (1 + calamity_intensity) * 10).

Source: src/world/environment.py (EnvironmentService.calculate_hazard_drain). Note: the producer that raises calamity_intensity in a live run is the
disclosed unwired part (TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES); this test pins the consumer.
"""
from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import RegionState
from src.world.environment import EnvironmentService


def _region(calamity_intensity):
    return RegionState(id="r", name="R", bounds=(0, 0, 10, 10), hazard_level=0.5, hazard_kind="PHYSICAL", calamity_intensity=calamity_intensity)


def _hero():
    return V2EntityBuilder(1).kind("hero").location(1.0, 1.0).build()


@pytest.mark.parametrize("intensity, expected", [(0.0, 5), (0.4, 7), (1.0, 10)])
def test_drain_follows_hazard_times_one_plus_calamity_intensity(intensity, expected):
    assert EnvironmentService.calculate_hazard_drain(_region(intensity), _hero()) == expected


def test_a_higher_calamity_intensity_never_lowers_the_drain():
    drains = [EnvironmentService.calculate_hazard_drain(_region(i / 10), _hero()) for i in range(0, 11)]
    assert drains == sorted(drains) and drains[-1] > drains[0]
