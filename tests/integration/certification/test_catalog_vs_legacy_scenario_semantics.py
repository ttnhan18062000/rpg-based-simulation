"""
Migration comparison test: catalog-built vs. legacy-built scenario semantics.

Verifies that the catalog-native construction path and the legacy V2EntityBuilder
path both satisfy the same semantic contract. Does NOT require identical entity
counts, hashes, or entity IDs — only that both produce valid, tickable states
with the same structural guarantees.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pytest

from src.certification.harness import CertificationHarness
from src.certification.models import ScenarioExpectations
from src.certification.scenarios import build_scenario_state, get_scenario_expectations
from src.config.profiles import PROD_SMALL
from src.content.repository import CatalogRepository
from src.core.state import AuthoritativeState, EntityState
from src.scenarios.catalog_state_builder import CatalogScenarioStateBuilder
from src.scenarios.schema import SimulationScenarioDefinition
from src.worldmodules.repository import WorldModuleRepository

pytestmark = [pytest.mark.integration, pytest.mark.slow]


@dataclass
class ScenarioSemantics:
    """Semantic summary of a built scenario state."""

    label: str
    entity_count: int
    alive_count: int
    entities_with_positive_hp: int
    entities_with_positive_atk: int
    archetype_sourced_count: int  # entities with archetype_id in properties


def _extract_semantics(label: str, state: AuthoritativeState) -> ScenarioSemantics:
    entities = list(state.entities.values())
    return ScenarioSemantics(
        label=label,
        entity_count=len(entities),
        alive_count=sum(1 for e in entities if e.combat.alive),
        entities_with_positive_hp=sum(1 for e in entities if e.combat.hp > 0),
        entities_with_positive_atk=sum(1 for e in entities if e.combat.atk > 0),
        archetype_sourced_count=sum(
            1 for e in entities if (e.identity.properties or {}).get("archetype_id")
        ),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def legacy_state():
    return build_scenario_state("COMBAT_ARENA_5V5")


@pytest.fixture(scope="module")
def legacy_expectations():
    return get_scenario_expectations("COMBAT_ARENA_5V5")


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
def catalog_build_result(catalog, module_repo):
    scenario = SimulationScenarioDefinition(
        id="goblin_camp_pressure",
        world_composition="frontier_living_world",
        perspective="hero_guild_perspective",
        focus_modules=["goblin_camp_conflict"],
        initial_conditions={},
    )
    return CatalogScenarioStateBuilder(catalog, module_repo).build(scenario, seed=42)


@pytest.fixture(scope="module")
def legacy_sem(legacy_state):
    return _extract_semantics("COMBAT_ARENA_5V5", legacy_state)


@pytest.fixture(scope="module")
def catalog_sem(catalog_build_result):
    return _extract_semantics("CATALOG_ARENA_SMALL", catalog_build_result.state)


# ---------------------------------------------------------------------------
# Per-path structural checks
# ---------------------------------------------------------------------------

def test_legacy_state_has_entities(legacy_sem):
    assert legacy_sem.entity_count > 0


def test_catalog_state_has_entities(catalog_sem):
    assert catalog_sem.entity_count > 0


def test_legacy_entities_alive_at_tick_zero(legacy_sem):
    assert legacy_sem.alive_count == legacy_sem.entity_count


def test_catalog_entities_alive_at_tick_zero(catalog_sem):
    assert catalog_sem.alive_count == catalog_sem.entity_count


def test_legacy_entities_have_positive_combat_stats(legacy_sem):
    assert legacy_sem.entities_with_positive_hp == legacy_sem.entity_count
    assert legacy_sem.entities_with_positive_atk == legacy_sem.entity_count


def test_catalog_entities_have_positive_combat_stats(catalog_sem):
    assert catalog_sem.entities_with_positive_hp == catalog_sem.entity_count
    assert catalog_sem.entities_with_positive_atk == catalog_sem.entity_count


def test_catalog_entities_have_archetype_sourcing(catalog_sem):
    """At least one catalog entity carries archetype_id — proves archetype-native path was used."""
    assert catalog_sem.archetype_sourced_count > 0


# ---------------------------------------------------------------------------
# Tick execution (bounded)
# ---------------------------------------------------------------------------

def test_legacy_scenario_can_tick(legacy_state, legacy_expectations, tmp_path):
    harness = CertificationHarness(PROD_SMALL, output_dir=str(tmp_path / "legacy"))
    result = harness.run_scenario("COMBAT_ARENA_5V5", legacy_state, legacy_expectations, ticks=3)
    assert result.conformance_passed, (
        f"Legacy scenario failed: {result.failure_kind} — {result.failure_reason}"
    )


def test_catalog_scenario_can_tick(catalog_build_result, tmp_path):
    harness = CertificationHarness(PROD_SMALL, output_dir=str(tmp_path / "catalog"))
    result = harness.run_scenario(
        "CATALOG_ARENA_SMALL",
        catalog_build_result.state,
        catalog_build_result.expectations,
        ticks=3,
    )
    assert result.conformance_passed, (
        f"Catalog scenario failed: {result.failure_kind} — {result.failure_reason}"
    )


# ---------------------------------------------------------------------------
# Semantic comparison (non-identical paths, shared contract)
# ---------------------------------------------------------------------------

def test_semantic_comparison_report(legacy_sem, catalog_sem):
    """
    Both paths must satisfy the same structural contract.
    Entity counts need NOT match — paths produce different compositions.
    Differences are reported clearly on failure.
    """
    failures = []

    if legacy_sem.entity_count == 0:
        failures.append(f"Legacy: 0 entities")
    if catalog_sem.entity_count == 0:
        failures.append(f"Catalog: 0 entities")

    if legacy_sem.alive_count != legacy_sem.entity_count:
        failures.append(
            f"Legacy: {legacy_sem.entity_count - legacy_sem.alive_count} entities not alive at tick 0"
        )
    if catalog_sem.alive_count != catalog_sem.entity_count:
        failures.append(
            f"Catalog: {catalog_sem.entity_count - catalog_sem.alive_count} entities not alive at tick 0"
        )

    if legacy_sem.entities_with_positive_hp < legacy_sem.entity_count:
        failures.append(f"Legacy: {legacy_sem.entity_count - legacy_sem.entities_with_positive_hp} entities with hp ≤ 0")
    if catalog_sem.entities_with_positive_hp < catalog_sem.entity_count:
        failures.append(f"Catalog: {catalog_sem.entity_count - catalog_sem.entities_with_positive_hp} entities with hp ≤ 0")

    if failures:
        report = "\n".join(f"  - {f}" for f in failures)
        raise AssertionError(
            f"Semantic comparison failed:\n{report}\n"
            f"  Legacy: {legacy_sem}\n"
            f"  Catalog: {catalog_sem}"
        )
