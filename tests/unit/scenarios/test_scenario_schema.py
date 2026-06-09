import pytest
from pydantic import ValidationError

from src.scenarios.schema import SimulationScenarioDefinition, ALLOWED_INITIAL_CONDITION_CATEGORIES

pytestmark = pytest.mark.scenario_setup


def _make(**kw) -> SimulationScenarioDefinition:
    defaults = dict(
        id="test_scenario",
        world_composition="frontier_core_composition",
        perspective="hero_perspective",
    )
    defaults.update(kw)
    return SimulationScenarioDefinition(**defaults)


def test_valid_scenario_constructs():
    s = _make()
    assert s.id == "test_scenario"
    assert s.world_composition == "frontier_core_composition"
    assert s.perspective == "hero_perspective"
    assert s.focus_modules == []
    assert s.initial_conditions == {}
    assert s.setup_tags == []
    assert s.display_name is None


def test_valid_scenario_with_all_fields():
    s = _make(
        display_name="Frontier Battle",
        focus_modules=["wolf_den_near_forest"],
        initial_conditions={"region_pressure": 0.8, "faction_activity": "high"},
        setup_tags=["debug", "combat_heavy"],
    )
    assert s.display_name == "Frontier Battle"
    assert "wolf_den_near_forest" in s.focus_modules
    assert s.initial_conditions["region_pressure"] == 0.8


def test_unknown_top_level_field_fails():
    with pytest.raises(ValidationError):
        SimulationScenarioDefinition(
            id="bad",
            world_composition="x",
            perspective="y",
            observability_config={"metrics": []},  # forbidden
        )


def test_unknown_initial_condition_key_fails():
    with pytest.raises(ValidationError):
        _make(initial_conditions={"unknown_category": 1.0})


def test_multiple_unknown_initial_condition_keys_fail():
    with pytest.raises(ValidationError):
        _make(initial_conditions={"telemetry": True, "scorecard": "high"})


def test_all_allowed_initial_condition_categories_pass():
    conditions = {cat: "high" for cat in ALLOWED_INITIAL_CONDITION_CATEGORIES}
    s = _make(initial_conditions=conditions)
    assert len(s.initial_conditions) == len(ALLOWED_INITIAL_CONDITION_CATEGORIES)


def test_no_observability_or_reporting_fields():
    s = _make()
    field_names = set(s.model_fields_set | set(s.model_dump().keys()))
    forbidden = {"metrics", "scorecard", "telemetry", "observability", "reporting", "post_run"}
    assert not (forbidden & field_names)


def test_scenario_is_immutable():
    s = _make()
    with pytest.raises(Exception):
        s.id = "changed"  # type: ignore[misc]


def test_empty_id_fails():
    with pytest.raises(ValidationError):
        _make(id="")


def test_empty_world_composition_fails():
    with pytest.raises(ValidationError):
        _make(world_composition="")


def test_empty_perspective_fails():
    with pytest.raises(ValidationError):
        _make(perspective="")
