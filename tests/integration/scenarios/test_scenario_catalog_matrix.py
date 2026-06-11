"""
Catalog matrix integration test — proves the scenario authoring model works across
8 distinct simulation setups.

Per-scenario assertions (Phase 41.3 acceptance criteria):
  - Scenario loads (schema validates)
  - Template validates when template_id is declared
  - Composition resolves (composition YAML found and parsed)
  - Perspective resolves (present in composition.default_perspectives when declared)
  - Initial conditions normalise (no unknown keys)
  - Setup modifiers are produced
  - No simulation script is embedded in the definition

Test is parametrized over the full 8-scenario matrix.
"""

from __future__ import annotations

import pytest

from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.scenarios.schema import SimulationScenarioDefinition
from src.scenarios.resolver import ScenarioSetupResolver, StateSetupModifier
from src.scenarios.feature_validator import ScenarioWorldFeatureValidator

pytestmark = pytest.mark.scenario_setup

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Scenario matrix
# All initial_condition keys use ALLOWED_INITIAL_CONDITION_CATEGORIES.
# All perspectives are declared in the corresponding composition's default_perspectives.
# ---------------------------------------------------------------------------

_SCENARIO_MATRIX = [
    pytest.param(
        dict(
            id="wolf_territory_pressure",
            world_composition="frontier_living_world",
            perspective="hero_guild_perspective",
            focus_modules=["wolf_den_near_forest"],
            initial_conditions={"territorial_intrusion": 0.8, "region_pressure": 0.6},
            template_id="territorial_pressure",
        ),
        id="wolf_territory_pressure",
    ),
    pytest.param(
        dict(
            id="goblin_camp_pressure",
            world_composition="frontier_living_world",
            perspective="goblin_warband_perspective",
            focus_modules=["goblin_camp_conflict"],
            initial_conditions={"faction_activity": 0.7, "region_pressure": 0.5},
            template_id="raider_conflict",
        ),
        id="goblin_camp_pressure",
    ),
    pytest.param(
        dict(
            id="merchant_trade_route_risk",
            world_composition="frontier_living_world",
            perspective="hero_guild_perspective",
            focus_modules=["bandit_road_trade_pressure"],
            initial_conditions={"trade_route_risk": 0.6, "faction_activity": 0.5},
            template_id="trade_route_risk",
        ),
        id="merchant_trade_route_risk",
    ),
    pytest.param(
        dict(
            id="old_mine_recovery",
            world_composition="frontier_living_world",
            perspective="hero_guild_perspective",
            focus_modules=["old_mine_resource_loop"],
            initial_conditions={"resource_scarcity": 0.7, "danger_level_override": 0.4},
            template_id="mine_reopening",
        ),
        id="old_mine_recovery",
    ),
    pytest.param(
        dict(
            id="undead_battlefield_containment",
            world_composition="frontier_living_world",
            perspective="hero_guild_perspective",
            focus_modules=["undead_battlefield"],
            initial_conditions={"region_pressure": 0.8, "danger_level_override": 0.7},
            template_id="undead_containment",
        ),
        id="undead_battlefield_containment",
    ),
    pytest.param(
        dict(
            id="moon_cult_ruins_pressure",
            world_composition="frontier_living_world",
            perspective="hero_guild_perspective",
            focus_modules=["undead_battlefield"],
            initial_conditions={"region_pressure": 0.6, "faction_activity": 0.5},
            template_id="cult_ritual_pressure",
        ),
        id="moon_cult_ruins_pressure",
    ),
    pytest.param(
        dict(
            id="settlement_defense",
            world_composition="frontier_living_world",
            perspective="hero_guild_perspective",
            focus_modules=["frontier_village_core"],
            initial_conditions={"region_pressure": 0.5, "spawn_bias": 1, "danger_level_override": 0.4},
            template_id="settlement_defense",
        ),
        id="settlement_defense",
    ),
    pytest.param(
        dict(
            id="forest_warden_patrol",
            world_composition="frontier_extended",
            perspective="hero_guild_perspective",
            focus_modules=["forest_warden_grove"],
            initial_conditions={"territorial_intrusion": 0.5, "population_alertness": 0.6},
            template_id="wildlife_intrusion",
        ),
        id="forest_warden_patrol",
    ),
]


# ---------------------------------------------------------------------------
# Matrix tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("scenario_kwargs", _SCENARIO_MATRIX)
def test_scenario_loads(scenario_kwargs):
    """Schema validates — SimulationScenarioDefinition constructs without error."""
    scenario = SimulationScenarioDefinition(**scenario_kwargs)
    assert scenario.id == scenario_kwargs["id"]


@pytest.mark.parametrize("scenario_kwargs", _SCENARIO_MATRIX)
def test_scenario_template_validates(scenario_kwargs):
    """If template_id is set, template registry validates initial conditions."""
    if scenario_kwargs.get("template_id") is None:
        pytest.skip("No template_id in this scenario")
    # Construction itself triggers template validation (validator in model)
    scenario = SimulationScenarioDefinition(**scenario_kwargs)
    assert scenario.template_id is not None


@pytest.mark.parametrize("scenario_kwargs", _SCENARIO_MATRIX)
def test_scenario_composition_resolves(resolver, scenario_kwargs):
    """World composition file found and parsed successfully."""
    scenario = SimulationScenarioDefinition(**scenario_kwargs)
    setup = resolver.resolve(scenario)
    assert setup.world_bundle is not None


@pytest.mark.parametrize("scenario_kwargs", _SCENARIO_MATRIX)
def test_scenario_perspective_resolves(resolver, scenario_kwargs):
    """Perspective ID is accepted by the resolver."""
    scenario = SimulationScenarioDefinition(**scenario_kwargs)
    setup = resolver.resolve(scenario)
    assert setup.perspective_id == scenario.perspective


@pytest.mark.parametrize("scenario_kwargs", _SCENARIO_MATRIX)
def test_scenario_initial_conditions_normalise(scenario_kwargs):
    """Initial condition keys are all in ALLOWED_INITIAL_CONDITION_CATEGORIES."""
    from src.scenarios.schema import ALLOWED_INITIAL_CONDITION_CATEGORIES
    scenario = SimulationScenarioDefinition(**scenario_kwargs)
    unknown = set(scenario.initial_conditions) - ALLOWED_INITIAL_CONDITION_CATEGORIES
    assert not unknown, f"Unknown initial condition keys: {unknown}"


@pytest.mark.parametrize("scenario_kwargs", _SCENARIO_MATRIX)
def test_scenario_produces_setup_modifiers(resolver, scenario_kwargs):
    """Resolver produces at least one StateSetupModifier for scenarios with initial_conditions."""
    scenario = SimulationScenarioDefinition(**scenario_kwargs)
    setup = resolver.resolve(scenario)
    if scenario.initial_conditions:
        assert len(setup.initial_state_modifiers) > 0
        assert all(isinstance(m, StateSetupModifier) for m in setup.initial_state_modifiers)


@pytest.mark.parametrize("scenario_kwargs", _SCENARIO_MATRIX)
def test_scenario_has_no_behavior_scripts(scenario_kwargs):
    """Scenario definition must not contain action scripts or scripted behavior."""
    scenario = SimulationScenarioDefinition(**scenario_kwargs)
    fields = set(type(scenario).model_fields.keys())
    forbidden = {"actions", "scripts", "behavior", "commands", "triggers", "dialog", "event_chain"}
    assert not (fields & forbidden), f"Scenario has behavior script fields: {fields & forbidden}"
