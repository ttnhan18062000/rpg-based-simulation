"""
Tests for ScenarioWorldFeatureValidator.

Verifies:
- Feature present in composition → pass
- Required feature missing from composition → fail with scenario/feature in error
- Focus module missing from composition → fail
- Required perspective missing from composition → fail
- Validation is deterministic
- Empty provided_features (composition doesn't declare features) → no feature errors
"""

from __future__ import annotations

import pytest

from src.scenarios.schema import SimulationScenarioDefinition
from src.scenarios.feature_validator import ScenarioWorldFeatureValidator, ValidationResult
from src.worldassembly.schema import WorldCompositionSpec, ModuleRefSpec


def _make_composition(
    world_id: str = "test_world",
    provided_features: list[str] | None = None,
    module_ids: list[str] | None = None,
    perspectives: list[str] | None = None,
) -> WorldCompositionSpec:
    module_refs = [
        {"module_id": mid, "enabled": True, "order": i}
        for i, mid in enumerate(module_ids or [])
    ]
    return WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id=world_id,
        name="Test Composition",
        module_refs=module_refs,
        provided_features=provided_features or [],
        default_perspectives=perspectives or [],
    )


def _make_scenario(
    scenario_id: str = "test_scenario",
    perspective: str = "hero_guild",
    focus_modules: list[str] | None = None,
    template_id: str | None = None,
) -> SimulationScenarioDefinition:
    return SimulationScenarioDefinition(
        id=scenario_id,
        world_composition="test_world",
        perspective=perspective,
        focus_modules=focus_modules or [],
        template_id=template_id,
    )


validator = ScenarioWorldFeatureValidator()


# ---------------------------------------------------------------------------
# Feature validation
# ---------------------------------------------------------------------------

def test_required_feature_present_passes():
    comp = _make_composition(provided_features=["ecology_module", "faction_territory"])
    scenario = _make_scenario(template_id="territorial_pressure")
    result = validator.validate(scenario, comp)
    assert result.ok, result.errors


def test_required_feature_missing_fails():
    # territorial_pressure requires faction_territory, ecology_module
    comp = _make_composition(provided_features=["ecology_module"])  # faction_territory missing
    scenario = _make_scenario(template_id="territorial_pressure")
    result = validator.validate(scenario, comp)
    assert not result.ok
    assert any("faction_territory" in e for e in result.errors)
    assert scenario.id in result.errors[0]


def test_empty_provided_features_skips_feature_check():
    """If composition declares no provided_features, feature requirement check is skipped."""
    comp = _make_composition(provided_features=[])
    scenario = _make_scenario(template_id="territorial_pressure")
    result = validator.validate(scenario, comp)
    # Feature check is skipped when composition doesn't declare features
    feature_errors = [e for e in result.errors if "required world feature" in e.lower() or "faction_territory" in e]
    assert not feature_errors


def test_no_template_id_skips_feature_check():
    """Scenario with no template_id has no required_world_features to check."""
    comp = _make_composition(provided_features=["ecology_module"])
    scenario = _make_scenario()
    result = validator.validate(scenario, comp)
    assert result.ok, result.errors


# ---------------------------------------------------------------------------
# Focus module validation
# ---------------------------------------------------------------------------

def test_focus_module_present_passes():
    comp = _make_composition(module_ids=["territory_control", "faction_influence"])
    scenario = _make_scenario(focus_modules=["territory_control"])
    result = validator.validate(scenario, comp)
    assert result.ok, result.errors


def test_focus_module_missing_fails():
    comp = _make_composition(module_ids=["ecology_module"])
    scenario = _make_scenario(focus_modules=["territory_control"])
    result = validator.validate(scenario, comp)
    assert not result.ok
    assert any("territory_control" in e for e in result.errors)
    assert scenario.id in result.errors[0]


def test_empty_module_refs_skips_focus_module_check():
    """If composition has no module_refs, focus module check is skipped."""
    comp = _make_composition(module_ids=[])
    scenario = _make_scenario(focus_modules=["territory_control"])
    result = validator.validate(scenario, comp)
    module_errors = [e for e in result.errors if "territory_control" in e]
    assert not module_errors


# ---------------------------------------------------------------------------
# Perspective validation
# ---------------------------------------------------------------------------

def test_perspective_present_passes():
    comp = _make_composition(perspectives=["hero_guild", "merchant_league"])
    scenario = _make_scenario(perspective="hero_guild")
    result = validator.validate(scenario, comp)
    assert result.ok, result.errors


def test_perspective_missing_fails():
    comp = _make_composition(perspectives=["merchant_league"])
    scenario = _make_scenario(perspective="hero_guild")
    result = validator.validate(scenario, comp)
    assert not result.ok
    assert any("hero_guild" in e for e in result.errors)


def test_empty_perspectives_skips_perspective_check():
    """If composition declares no default_perspectives, perspective check is skipped."""
    comp = _make_composition(perspectives=[])
    scenario = _make_scenario(perspective="hero_guild")
    result = validator.validate(scenario, comp)
    perspective_errors = [e for e in result.errors if "hero_guild" in e]
    assert not perspective_errors


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_validation_is_deterministic():
    comp = _make_composition(provided_features=["ecology_module"], module_ids=["ecology_module"])
    scenario = _make_scenario(template_id="territorial_pressure", focus_modules=["ecology_module"])
    result_a = validator.validate(scenario, comp)
    result_b = validator.validate(scenario, comp)
    assert result_a.ok == result_b.ok
    assert result_a.errors == result_b.errors
