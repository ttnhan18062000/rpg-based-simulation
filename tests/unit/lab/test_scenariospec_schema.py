# Compliance IDs: SCENARIO-TEST-001, SCENARIO-TEST-002, SCENARIO-TEST-003
import pytest
import yaml
from pathlib import Path
from pydantic import ValidationError
from src.lab.schema import (
    ScenarioSpec,
    IntentSpec,
    ExpectedLimitSpec,
    RequiredSignalsSpec,
    InvalidScenarioSpecError,
    load_scenario_spec_from_yaml
)

def test_valid_scenariospec_loads(tmp_path: Path):
    """Verify that a standard valid scenario spec loads cleanly."""
    raw_yaml = """
schema_version: scenariospec.v1
scenario_id: test_scenario_01
name: Test Scenario
world_id: test_world_01
scenario_type: resource_economy
intent:
  primary_goal: validate_economy
  description: A test description.
expected_behavior:
  resource_production_rate:
    min: 1.0
    max: 10.0
  hard_law_violations:
    max: 0.0
required_signals:
  metrics:
    - resource_production_rate
  events:
    - ResourceNodeDepleted
  cognition:
    - current_project
allowed_anomalies:
  - NavigationStuckBasic
critical_anomalies:
  - HardLawViolationDetected
tags:
  - unit_test
"""
    yaml_file = tmp_path / "scenario.yaml"
    yaml_file.write_text(raw_yaml)

    spec = load_scenario_spec_from_yaml(yaml_file)
    assert spec.schema_version == "scenariospec.v1"
    assert spec.scenario_id == "test_scenario_01"
    assert spec.intent.primary_goal == "validate_economy"
    assert spec.expected_behavior["resource_production_rate"].min == 1.0
    assert spec.expected_behavior["resource_production_rate"].max == 10.0
    assert spec.expected_behavior["hard_law_violations"].min is None
    assert spec.expected_behavior["hard_law_violations"].max == 0.0
    assert "resource_production_rate" in spec.required_signals.metrics
    assert "ResourceNodeDepleted" in spec.required_signals.events
    assert "current_project" in spec.required_signals.cognition
    assert "NavigationStuckBasic" in spec.allowed_anomalies
    assert "HardLawViolationDetected" in spec.critical_anomalies
    assert "unit_test" in spec.tags

def test_missing_id_and_world_id_rejected(tmp_path: Path):
    """Verify that omitting critical identifiers is rejected."""
    # Missing scenario_id
    raw_yaml_no_id = """
schema_version: scenariospec.v1
name: Test Scenario
world_id: test_world_01
scenario_type: resource_economy
intent:
  primary_goal: validate_economy
"""
    file_no_id = tmp_path / "no_id.yaml"
    file_no_id.write_text(raw_yaml_no_id)

    with pytest.raises(InvalidScenarioSpecError) as exc_info:
        load_scenario_spec_from_yaml(file_no_id)
    assert "Field required" in str(exc_info.value) or "scenario_id" in str(exc_info.value)

def test_invalid_limits_rejected():
    """Verify that malformed ExpectedLimitSpecs are rejected."""
    # 1. min > max should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        ExpectedLimitSpec(min=5.0, max=2.0)
    assert "min" in str(exc_info.value) and "cannot be greater than max" in str(exc_info.value)

    # 2. Neither min nor max provided should raise ValidationError
    with pytest.raises(ValidationError) as exc_info:
        ExpectedLimitSpec(min=None, max=None)
    assert "At least one of 'min' or 'max' limit must be specified" in str(exc_info.value)

def test_invalid_schema_version_rejected(tmp_path: Path):
    """Verify that incorrect schema version is blocked."""
    raw_yaml = """
schema_version: scenariospec.v2_invalid
scenario_id: test_scenario_01
name: Test Scenario
world_id: test_world_01
scenario_type: resource_economy
intent:
  primary_goal: validate_economy
"""
    yaml_file = tmp_path / "scenario_v2.yaml"
    yaml_file.write_text(raw_yaml)

    with pytest.raises(InvalidScenarioSpecError) as exc_info:
        load_scenario_spec_from_yaml(yaml_file)
    assert "schema_version must strictly be 'scenariospec.v1'" in str(exc_info.value)

def test_future_fields_preserved(tmp_path: Path):
    """Verify that unknown future fields are successfully preserved under extra fields."""
    raw_yaml = """
schema_version: scenariospec.v1
scenario_id: test_scenario_01
name: Test Scenario
world_id: test_world_01
scenario_type: resource_economy
intent:
  primary_goal: validate_economy
future_field_abc: "some_value"
another_extra_nested:
  sub_key: 42
"""
    yaml_file = tmp_path / "future.yaml"
    yaml_file.write_text(raw_yaml)

    spec = load_scenario_spec_from_yaml(yaml_file)
    assert spec.model_extra["future_field_abc"] == "some_value"
    assert spec.model_extra["another_extra_nested"]["sub_key"] == 42
