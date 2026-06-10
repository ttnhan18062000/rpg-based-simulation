"""
Tests for RegionThreatClassifier — projection-based region safety classification.

Verifies:
- Town-controlled region is safe from hero perspective
- Goblin camp is hostile from hero perspective
- Wolf den is contextual threat (threatened, not hostile)
- Merchant road is contested when bandit population is active
- Legacy fallback works for factions without catalog perspectives
- Classification never mutates catalog state
- Classification is deterministic
"""

from __future__ import annotations

import pytest

from src.content.repository import CatalogRepository
from src.world.region_threat_classifier import RegionThreatClassifier


@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def classifier(catalog):
    return RegionThreatClassifier(catalog)


# ---------------------------------------------------------------------------
# Catalog-projection scenarios
# ---------------------------------------------------------------------------

def test_town_region_safe_from_hero_perspective(classifier):
    """town_council is in hero_guild_perspective.ally_groups → region is safe."""
    result = classifier.classify(
        perspective_faction_id="hero_guild",
        controlling_faction_id="town_council",
        population_faction_ids=[],
    )
    assert result.label == "safe"
    assert result.source == "catalog_projection"
    assert "town_council" in result.contributing_factions


def test_goblin_camp_hostile_from_hero_perspective(classifier):
    """goblin_warband is in hero_guild_perspective.hostile_groups → region is hostile."""
    result = classifier.classify(
        perspective_faction_id="hero_guild",
        controlling_faction_id="goblin_warband",
        population_faction_ids=[],
    )
    assert result.label == "hostile"
    assert result.source == "catalog_projection"


def test_wolf_den_threatened_from_hero_perspective(classifier):
    """
    wild_beast_pack is in hero_guild_perspective.contextual_threat_groups → label=threat.
    Region should be 'threatened', NOT 'hostile' — wildlife is not an unconditional enemy.
    """
    result = classifier.classify(
        perspective_faction_id="hero_guild",
        controlling_faction_id="wild_beast_pack",
        population_faction_ids=[],
    )
    assert result.label == "threatened"
    assert result.label != "hostile"
    assert result.source == "catalog_projection"


def test_merchant_road_contested_with_bandit_population(classifier):
    """
    Merchant controls the road (neutral from hero view), but bandits are present (hostile).
    Result: contested — neutral territory with hostile population.
    """
    result = classifier.classify(
        perspective_faction_id="hero_guild",
        controlling_faction_id="merchant_league",
        population_faction_ids=["bandit_company"],
    )
    assert result.label == "contested"
    assert result.source == "catalog_projection"
    assert "bandit_company" in result.contributing_factions


def test_allied_region_with_threat_population_is_threatened(classifier):
    """
    Town controls the region (ally) but wild beasts are present (contextual threat).
    Result: threatened — allied territory under wildlife pressure.
    """
    result = classifier.classify(
        perspective_faction_id="hero_guild",
        controlling_faction_id="town_council",
        population_faction_ids=["wild_beast_pack"],
    )
    assert result.label == "threatened"
    assert result.source == "catalog_projection"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_no_factions_returns_unknown(classifier):
    """No controlling faction and no populations → unknown."""
    result = classifier.classify(
        perspective_faction_id="hero_guild",
        controlling_faction_id=None,
        population_faction_ids=[],
    )
    assert result.label == "unknown"
    assert result.source == "no_faction_data"


def test_no_populations_defaults_to_none(classifier):
    """population_faction_ids defaults gracefully when omitted."""
    result = classifier.classify(
        perspective_faction_id="hero_guild",
        controlling_faction_id="town_council",
    )
    assert result.label == "safe"


# ---------------------------------------------------------------------------
# Legacy fallback
# ---------------------------------------------------------------------------

def test_legacy_fallback_monster_horde_faction(catalog):
    """
    Faction with no catalog perspective uses legacy bucket logic.
    'monster_horde' name maps to Faction.MONSTER_HORDE bucket → hostile.
    """
    classifier = RegionThreatClassifier(catalog)
    result = classifier.classify(
        perspective_faction_id="custom_unknown_faction",
        controlling_faction_id="monster_horde",
        population_faction_ids=[],
    )
    assert result.label == "hostile"
    assert result.source == "legacy_fallback"


# ---------------------------------------------------------------------------
# Read-only and determinism
# ---------------------------------------------------------------------------

def test_classification_does_not_mutate_catalog(catalog):
    """classify() must not modify the catalog's faction or perspective data."""
    factions_before = set(catalog.factions.keys())
    perspectives_before = set(catalog.perspectives.keys())

    classifier = RegionThreatClassifier(catalog)
    classifier.classify("hero_guild", "goblin_warband", ["bandit_company"])

    assert set(catalog.factions.keys()) == factions_before
    assert set(catalog.perspectives.keys()) == perspectives_before


def test_classification_deterministic(classifier):
    """Same inputs produce the same label on repeated calls."""
    result_a = classifier.classify(
        "hero_guild", "goblin_warband", ["wild_beast_pack"]
    )
    result_b = classifier.classify(
        "hero_guild", "goblin_warband", ["wild_beast_pack"]
    )
    assert result_a.label == result_b.label
    assert result_a.source == result_b.source
