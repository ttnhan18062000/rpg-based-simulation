"""
Tests for MotivationPressureResolver.

Verifies:
- Territorial predator produces territory/hunger pressure
- Cautious commoner produces safety/duty pressure
- Merchant produces wealth/trade pressure (wealth_pressure high)
- Undead purpose-bound produces purpose pressure
- Missing both profiles → empty() with source=no_profile
- Outputs are normalised (0.0–1.0) and deterministic
- Resolver never mutates catalog or entity
"""

from __future__ import annotations

import pytest

from src.content.repository import CatalogRepository
from src.world.motivation.pressure_resolver import MotivationPressureResolver, MotivationPressureSet


@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def resolver(catalog):
    return MotivationPressureResolver(catalog)


def _make_entity(need_profile_id=None, drive_profile_id=None):
    """Minimal fake entity with identity.properties."""
    from types import SimpleNamespace
    props = {}
    if need_profile_id:
        props["need_profile_id"] = need_profile_id
    if drive_profile_id:
        props["drive_profile_id"] = drive_profile_id
    identity = SimpleNamespace(properties=props)
    return SimpleNamespace(identity=identity)


# ---------------------------------------------------------------------------
# Archetype test cases
# ---------------------------------------------------------------------------

def test_territorial_predator_produces_territory_and_hunger_pressure(resolver):
    """territorial_predator drive + carnivore_survival need → high territory and hunger."""
    entity = _make_entity(
        need_profile_id="carnivore_survival",
        drive_profile_id="territorial_predator",
    )
    result = resolver.resolve_pressures(entity)

    assert result.territory_pressure > 0.5, f"Expected high territory pressure, got {result.territory_pressure}"
    assert result.hunger_pressure > 0.5, f"Expected high hunger pressure, got {result.hunger_pressure}"
    assert result.source == "need_and_drive_profile"


def test_cautious_commoner_produces_safety_and_duty_pressure(resolver):
    """cautious_commoner drive + humanoid_survival need → high safety, non-zero duty."""
    entity = _make_entity(
        need_profile_id="humanoid_survival",
        drive_profile_id="cautious_commoner",
    )
    result = resolver.resolve_pressures(entity)

    assert result.safety_pressure > 0.5, f"Expected high safety pressure, got {result.safety_pressure}"
    assert result.duty_pressure > 0.0, f"Expected non-zero duty pressure, got {result.duty_pressure}"
    assert result.source == "need_and_drive_profile"


def test_merchant_produces_wealth_pressure(resolver):
    """profit_seeker drive → high wealth_pressure."""
    entity = _make_entity(drive_profile_id="profit_seeker")
    result = resolver.resolve_pressures(entity)

    assert result.wealth_pressure > 0.5, f"Expected high wealth pressure, got {result.wealth_pressure}"
    assert result.source == "drive_profile_only"


def test_undead_purpose_bound_produces_purpose_pressure(resolver):
    """undead_purpose need → high purpose_pressure, low/zero hunger."""
    entity = _make_entity(need_profile_id="undead_purpose")
    result = resolver.resolve_pressures(entity)

    assert result.purpose_pressure > 0.5, f"Expected high purpose pressure, got {result.purpose_pressure}"
    assert result.hunger_pressure == 0.0, f"Undead should have no hunger, got {result.hunger_pressure}"
    assert result.source == "need_profile_only"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_missing_both_profiles_returns_empty(resolver):
    entity = _make_entity()
    result = resolver.resolve_pressures(entity)
    assert result == MotivationPressureSet.empty()
    assert result.source == "no_profile"


def test_unknown_profile_id_returns_empty(resolver):
    entity = _make_entity(need_profile_id="nonexistent_profile")
    result = resolver.resolve_pressures(entity)
    assert result.source == "no_profile"


# ---------------------------------------------------------------------------
# Normalisation and determinism
# ---------------------------------------------------------------------------

def test_all_pressures_normalised(resolver):
    """All output pressures must be in [0.0, 1.0]."""
    entity = _make_entity(
        need_profile_id="carnivore_survival",
        drive_profile_id="territorial_predator",
    )
    result = resolver.resolve_pressures(entity)
    for field_name in type(result).model_fields:
        if field_name == "source":
            continue
        val = getattr(result, field_name)
        assert 0.0 <= val <= 1.0, f"{field_name}={val} out of [0.0, 1.0]"


def test_resolution_is_deterministic(resolver):
    entity = _make_entity(
        need_profile_id="humanoid_survival",
        drive_profile_id="cautious_commoner",
    )
    result_a = resolver.resolve_pressures(entity)
    result_b = resolver.resolve_pressures(entity)
    assert result_a == result_b


def test_resolver_does_not_mutate_catalog(catalog):
    """resolve_pressures() must not modify the catalog."""
    need_count_before = len(catalog.need_profiles)
    drive_count_before = len(catalog.drive_profiles)

    resolver = MotivationPressureResolver(catalog)
    entity = _make_entity(need_profile_id="humanoid_survival", drive_profile_id="cautious_commoner")
    resolver.resolve_pressures(entity)

    assert len(catalog.need_profiles) == need_count_before
    assert len(catalog.drive_profiles) == drive_count_before
