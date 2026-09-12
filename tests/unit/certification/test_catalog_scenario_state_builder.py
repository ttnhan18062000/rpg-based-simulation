"""
Unit tests for CatalogScenarioStateBuilder.

Verifies that the catalog-native scenario construction path (ScenarioSetupResolver
→ WorldEntitySpawner → AuthoritativeState) works end-to-end without touching
the legacy ArenaInjector / build_scenario_state() path.
"""

from __future__ import annotations

import inspect

import pytest

from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.scenarios.schema import SimulationScenarioDefinition
from src.scenarios.catalog_state_builder import CatalogScenarioStateBuilder, CatalogScenarioBuildResult
from src.core.state import AuthoritativeState
from src.certification.models import ScenarioExpectations
from src.scenarios.resolver import ResolvedScenarioSetup

pytestmark = pytest.mark.worldassembly


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
def wolf_scenario():
    return SimulationScenarioDefinition(
        id="wolf_territory_pressure",
        world_composition="frontier_living_world",
        perspective="hero_guild_perspective",
        focus_modules=["wolf_den_near_forest"],
        initial_conditions={},
    )


@pytest.fixture(scope="module")
def wolf_result(catalog, module_repo, wolf_scenario):
    builder = CatalogScenarioStateBuilder(catalog, module_repo)
    return builder.build(wolf_scenario)


# ---------------------------------------------------------------------------
# Architecture guard
# ---------------------------------------------------------------------------

def test_builder_does_not_import_legacy_arena_builder():
    """CatalogScenarioStateBuilder must not import from certification.scenarios."""
    import src.scenarios.catalog_state_builder as mod
    source = inspect.getsource(mod)
    assert "certification.scenarios" not in source, (
        "CatalogScenarioStateBuilder must not import from src.certification.scenarios"
    )


def test_builder_does_not_use_entity_generator():
    """CatalogScenarioStateBuilder must not use EntityGenerator (legacy path)."""
    import src.scenarios.catalog_state_builder as mod
    source = inspect.getsource(mod)
    assert "EntityGenerator" not in source


# ---------------------------------------------------------------------------
# Functional tests
# ---------------------------------------------------------------------------

def test_build_produces_authoritative_state(wolf_result):
    """Build result contains an AuthoritativeState."""
    assert isinstance(wolf_result, CatalogScenarioBuildResult)
    assert isinstance(wolf_result.state, AuthoritativeState)


def test_build_state_has_entities(wolf_result):
    """AuthoritativeState has at least one entity."""
    assert len(wolf_result.state.entities) > 0


def test_build_state_tick_zero(wolf_result):
    """State starts at tick 0."""
    assert wolf_result.state.tick == 0


def test_build_result_contains_setup_and_expectations(wolf_result, wolf_scenario):
    """Result carries setup and expectations alongside state."""
    assert isinstance(wolf_result.setup, ResolvedScenarioSetup)
    assert wolf_result.setup.scenario_id == wolf_scenario.id
    assert wolf_result.setup.perspective_id == wolf_scenario.perspective
    assert isinstance(wolf_result.expectations, ScenarioExpectations)


def test_archetype_entities_carry_archetype_id(wolf_result, catalog, module_repo, wolf_scenario):
    """
    Entities whose profile has archetype_id must carry it in identity.properties
    (set by ArchetypeEntityFactory via WorldEntitySpawner archetype-native path).

    TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE: a profile can now expand
    into `profile.count` entities, so positional-index alignment between ctx.entities and
    wolf_result.state.entities no longer holds -- group by the real population_id tag instead.
    """
    ctx = wolf_result.setup.world_bundle.compile_context
    archetype_profiles = {k: p for k, p in ctx.entities.items() if p.archetype_id}
    assert archetype_profiles, "wolf_territory_pressure must have archetype-backed profiles"

    by_population: dict[str, list] = {}
    for entity in wolf_result.state.entities.values():
        pop_id = (entity.identity.properties or {}).get("population_id")
        by_population.setdefault(pop_id, []).append(entity)

    for key, profile in archetype_profiles.items():
        members = by_population.get(key, [])
        assert len(members) == profile.count, (
            f"Population {key!r}: expected {profile.count} entities tagged population_id="
            f"{key!r}, found {len(members)}"
        )
        for entity in members:
            props = entity.identity.properties or {}
            assert props.get("archetype_id") == profile.archetype_id, (
                f"Entity {entity.id} (profile {key!r}): expected archetype_id="
                f"{profile.archetype_id!r} in identity.properties"
            )


def test_tick_zero_entities_alive(wolf_result):
    """All spawned entities start alive."""
    for eid, entity in wolf_result.state.entities.items():
        assert entity.combat.alive, f"Entity {eid} must be alive at tick 0"
