"""
Integration tests for ScenarioSetupResolver.

Happy-path tests that require full WorldAssemblyResolver.assemble() are marked xfail
due to a pre-existing CatalogValidator issue (CAT-REL-099 moon_cult_ruins / apprentice_mage)
that blocks assembly regardless of which composition is used. Error-path and structural
tests do not require assembly and pass unconditionally.
"""

import pytest

pytestmark = pytest.mark.scenario_setup

from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.scenarios.schema import SimulationScenarioDefinition
from src.scenarios.resolver import (
    ScenarioSetupResolver,
    ResolvedScenarioSetup,
    StateSetupModifier,
)

_PREEXISTING_CAT_BUG = pytest.mark.xfail(
    reason="Pre-existing CAT-REL-099: moon_cult_ruins references non-existent population "
    "'apprentice_mage'; CatalogValidator sweeps entire catalog and blocks assembly.",
    strict=False,
)


@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def module_repo():
    repo = WorldModuleRepository()
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def resolver(catalog, module_repo):
    return ScenarioSetupResolver(catalog, module_repo)


def _frontier_scenario(**kw) -> SimulationScenarioDefinition:
    defaults = dict(
        id="test_frontier",
        world_composition="frontier_living_world",
        perspective="hero_guild_perspective",
    )
    defaults.update(kw)
    return SimulationScenarioDefinition(**defaults)


# ---------------------------------------------------------------------------
# Happy-path tests (require full assembly — xfail due to pre-existing defect)
# ---------------------------------------------------------------------------

@_PREEXISTING_CAT_BUG
def test_resolver_produces_resolved_setup(resolver):
    scenario = _frontier_scenario()
    setup = resolver.resolve(scenario)
    assert isinstance(setup, ResolvedScenarioSetup)
    assert setup.scenario_id == "test_frontier"
    assert setup.world_bundle is not None


@_PREEXISTING_CAT_BUG
def test_perspective_preserved_in_output(resolver):
    scenario = _frontier_scenario(perspective="hero_guild_perspective")
    setup = resolver.resolve(scenario)
    assert setup.perspective_id == "hero_guild_perspective"


@_PREEXISTING_CAT_BUG
def test_empty_initial_conditions_produces_no_modifiers(resolver):
    scenario = _frontier_scenario(id="empty_cond", initial_conditions={})
    setup = resolver.resolve(scenario)
    assert setup.initial_state_modifiers == []


@_PREEXISTING_CAT_BUG
def test_initial_conditions_become_modifiers_via_full_resolve(resolver):
    scenario = _frontier_scenario(
        id="modifiers_test",
        initial_conditions={"region_pressure": 0.8, "faction_activity": "high"},
    )
    setup = resolver.resolve(scenario)
    by_type = {m.modifier_type: m for m in setup.initial_state_modifiers}
    assert by_type["region_pressure"].parameters["value"] == 0.8
    assert by_type["faction_activity"].parameters["value"] == "high"


# ---------------------------------------------------------------------------
# Modifier-conversion unit tests (no assembly — always pass)
# ---------------------------------------------------------------------------

def test_modifier_conversion_maps_each_condition(resolver):
    """_build_modifiers is tested directly — no assembly required."""
    conditions = {"region_pressure": 0.8, "faction_activity": "high", "spawn_bias": 2}
    modifiers = resolver._build_modifiers(conditions)
    assert len(modifiers) == 3
    by_type = {m.modifier_type: m for m in modifiers}
    assert by_type["region_pressure"].parameters == {"value": 0.8}
    assert by_type["faction_activity"].parameters == {"value": "high"}
    assert by_type["spawn_bias"].parameters == {"value": 2}


def test_empty_conditions_produce_empty_modifier_list(resolver):
    assert resolver._build_modifiers({}) == []


def test_state_setup_modifier_is_frozen():
    m = StateSetupModifier(modifier_type="region_pressure", parameters={"value": 0.5})
    with pytest.raises(Exception):
        m.modifier_type = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Error-path tests (fail before assembly — always pass)
# ---------------------------------------------------------------------------

def test_invalid_composition_fails_with_scenario_id(resolver):
    scenario = _frontier_scenario(
        id="bad_comp_scenario",
        world_composition="nonexistent_composition_xyz",
    )
    with pytest.raises(ValueError, match="bad_comp_scenario"):
        resolver.resolve(scenario)


def test_invalid_perspective_fails_with_scenario_id(resolver):
    scenario = _frontier_scenario(
        id="bad_persp_scenario",
        perspective="totally_invalid_perspective",
    )
    with pytest.raises(ValueError, match="bad_persp_scenario"):
        resolver.resolve(scenario)


# ---------------------------------------------------------------------------
# Structural / boundary tests
# ---------------------------------------------------------------------------

def test_resolver_does_not_import_observability():
    import ast
    import inspect
    import src.scenarios.resolver as mod

    source = inspect.getsource(mod)
    tree = ast.parse(source)
    forbidden = ("observability", "reporting", "telemetry", "scorecard", "metrics")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", "") or ""
            for alias in getattr(node, "names", []):
                full = f"{module}.{alias.name or ''}".lower().strip(".")
                for prefix in forbidden:
                    assert prefix not in full, f"Forbidden import: {full}"
