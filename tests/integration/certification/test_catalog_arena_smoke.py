"""
CATALOG_ARENA_SMALL — integration smoke test.

Proves the catalog-backed construction path produces a fully executable
simulation state. Uses CatalogScenarioStateBuilder to build a goblin
camp pressure scenario, then runs 3 ticks via CertificationHarness.

This is not a replacement for COMBAT_ARENA_5V5 or existing arena stress tests.
"""

from __future__ import annotations

import pytest

from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.scenarios.schema import SimulationScenarioDefinition
from src.scenarios.catalog_state_builder import CatalogScenarioStateBuilder
from src.certification.harness import CertificationHarness
from src.certification.models import ScenarioExpectations
from src.config.profiles import PROD_SMALL

pytestmark = [pytest.mark.integration, pytest.mark.slow]

_SCENARIO_LABEL = "CATALOG_ARENA_SMALL"


@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def module_repo():
    repo = WorldModuleRepository("data/content/world_modules")
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def catalog_scenario():
    return SimulationScenarioDefinition(
        id="goblin_camp_pressure",
        world_composition="frontier_living_world",
        perspective="hero_guild_perspective",
        focus_modules=["goblin_camp_conflict"],
        initial_conditions={},
    )


@pytest.fixture(scope="module")
def build_result(catalog, module_repo, catalog_scenario):
    builder = CatalogScenarioStateBuilder(catalog, module_repo)
    return builder.build(catalog_scenario, seed=42)


# ---------------------------------------------------------------------------
# State construction checks
# ---------------------------------------------------------------------------

def test_catalog_arena_small_builds(build_result):
    """CatalogScenarioStateBuilder produces a non-empty AuthoritativeState."""
    assert len(build_result.state.entities) > 0


def test_catalog_arena_small_has_two_factions(build_result):
    """
    State contains entities from at least two distinct factions.
    frontier_living_world includes goblin_warband + town_council faction modules.
    """
    faction_ids = set()
    for entity in build_result.state.entities.values():
        props = entity.identity.properties or {}
        fid = props.get("faction_id")
        if fid:
            faction_ids.add(fid)
    assert len(faction_ids) >= 2, (
        f"Expected ≥2 faction_ids in identity.properties, got: {faction_ids}"
    )


def test_catalog_arena_small_entities_have_archetype_source(build_result):
    """
    Entities whose profiles carry archetype_id have it recorded in identity.properties.
    No direct enemy source truth (legacy enemy IDs) are required.
    """
    archetype_entities = [
        e for e in build_result.state.entities.values()
        if (e.identity.properties or {}).get("archetype_id")
    ]
    assert archetype_entities, (
        "At least one entity must have archetype_id in identity.properties"
    )


# ---------------------------------------------------------------------------
# Runtime execution check
# ---------------------------------------------------------------------------

def test_catalog_arena_small_can_tick(build_result, tmp_path):
    """
    CertificationHarness can run 3 ticks without error on a catalog-built state.
    """
    harness = CertificationHarness(PROD_SMALL, output_dir=str(tmp_path))
    result = harness.run_scenario(
        _SCENARIO_LABEL,
        build_result.state,
        build_result.expectations,
        ticks=3,
    )
    assert result.conformance_passed, (
        f"CATALOG_ARENA_SMALL failed after 3 ticks: "
        f"failure_kind={result.failure_kind}, reason={result.failure_reason}"
    )
