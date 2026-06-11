"""
Tests for ScenarioTemplateDefinition and ScenarioTemplateRegistry.

Verifies:
- All 10 templates are defined and loadable
- Template validates matching initial conditions correctly
- Unsupported initial condition key fails
- Templates contain no action scripts (structural fields only)
- Scenario with matching template passes
- Scenario with unsupported condition fails
- Scenario without template_id is unaffected
- Unknown template_id in scenario raises error
"""

from __future__ import annotations

import pytest

from src.scenarios.templates import (
    ScenarioTemplateDefinition,
    ScenarioTemplateRegistry,
    get_scenario_template_registry,
)
from src.scenarios.schema import SimulationScenarioDefinition


_EXPECTED_TEMPLATE_IDS = {
    "territorial_pressure",
    "raider_conflict",
    "trade_route_risk",
    "resource_recovery",
    "settlement_defense",
    "cult_ritual_pressure",
    "undead_containment",
    "wildlife_intrusion",
    "caravan_escort",
    "mine_reopening",
}


# ---------------------------------------------------------------------------
# Registry and template loading
# ---------------------------------------------------------------------------

def test_all_ten_templates_registered():
    registry = get_scenario_template_registry()
    found = set(registry.all_ids())
    missing = _EXPECTED_TEMPLATE_IDS - found
    assert not missing, f"Missing templates: {missing}"


def test_each_template_has_required_fields():
    registry = get_scenario_template_registry()
    for tid in _EXPECTED_TEMPLATE_IDS:
        t = registry.get(tid)
        assert t is not None
        assert t.id == tid
        assert isinstance(t.required_world_features, list)
        assert isinstance(t.required_perspective_types, list)
        assert isinstance(t.allowed_initial_conditions, frozenset)
        assert isinstance(t.allowed_focus_modules, list)


def test_templates_contain_no_behavior_scripts():
    """Templates must only carry structural constraints — no action scripts."""
    registry = get_scenario_template_registry()
    forbidden_fields = {"actions", "scripts", "behavior", "commands", "triggers"}
    for tid in _EXPECTED_TEMPLATE_IDS:
        t = registry.get(tid)
        template_fields = set(type(t).model_fields.keys())
        overlap = template_fields & forbidden_fields
        assert not overlap, f"Template {tid!r} has forbidden behavior fields: {overlap}"


# ---------------------------------------------------------------------------
# Registry.validate_scenario
# ---------------------------------------------------------------------------

def test_validate_scenario_passes_allowed_conditions():
    registry = get_scenario_template_registry()
    error = registry.validate_scenario(
        "territorial_pressure",
        frozenset({"region_pressure", "faction_activity"}),
    )
    assert error is None


def test_validate_scenario_fails_unsupported_condition():
    registry = get_scenario_template_registry()
    # "resource_scarcity" is not in territorial_pressure.allowed_initial_conditions
    error = registry.validate_scenario(
        "territorial_pressure",
        frozenset({"region_pressure", "resource_scarcity"}),
    )
    assert error is not None
    assert "resource_scarcity" in error


def test_validate_scenario_unknown_template_returns_error():
    registry = get_scenario_template_registry()
    error = registry.validate_scenario("nonexistent_template", frozenset())
    assert error is not None
    assert "nonexistent_template" in error


def test_validate_scenario_empty_conditions_always_passes():
    registry = get_scenario_template_registry()
    for tid in _EXPECTED_TEMPLATE_IDS:
        error = registry.validate_scenario(tid, frozenset())
        assert error is None, f"Empty conditions should pass for {tid!r}: {error}"


# ---------------------------------------------------------------------------
# SimulationScenarioDefinition with template_id
# ---------------------------------------------------------------------------

def test_scenario_with_valid_template_passes():
    scenario = SimulationScenarioDefinition(
        id="test_territorial",
        world_composition="base_world",
        perspective="hero_guild",
        template_id="territorial_pressure",
        initial_conditions={"region_pressure": 0.7},
    )
    assert scenario.template_id == "territorial_pressure"


def test_scenario_with_unsupported_condition_for_template_fails():
    with pytest.raises(ValueError, match="Template validation failed"):
        SimulationScenarioDefinition(
            id="test_bad",
            world_composition="base_world",
            perspective="hero_guild",
            template_id="territorial_pressure",
            initial_conditions={"resource_scarcity": 0.5},
        )


def test_scenario_without_template_id_is_unaffected():
    """Scenarios without template_id must not fail due to template validation."""
    scenario = SimulationScenarioDefinition(
        id="free_scenario",
        world_composition="base_world",
        perspective="hero_guild",
        initial_conditions={"region_pressure": 0.5, "spawn_bias": 2},
    )
    assert scenario.template_id is None


def test_scenario_with_unknown_template_id_fails():
    with pytest.raises(ValueError, match="not found in registry"):
        SimulationScenarioDefinition(
            id="bad_template",
            world_composition="base_world",
            perspective="hero_guild",
            template_id="does_not_exist",
        )
