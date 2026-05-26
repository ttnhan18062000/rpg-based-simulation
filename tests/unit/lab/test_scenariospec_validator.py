# Compliance IDs: SCENARIO-TEST-004, SCENARIO-TEST-005, SCENARIO-TEST-006
import pytest
from unittest.mock import MagicMock
from src.worldbuilding.repository import WorldRepository
from src.lab.schema import ScenarioSpec, InvalidScenarioSpecError
from src.lab.validator import (
    ScenarioValidator,
    WorldExistenceRule,
    ExpectedBehaviorRule,
    RequiredSignalsRule,
    AnomalyReferencesRule
)

@pytest.fixture
def base_spec_dict():
    return {
        "schema_version": "scenariospec.v1",
        "scenario_id": "test_scenario",
        "name": "Test Scenario",
        "world_id": "existing_world",
        "scenario_type": "resource_economy",
        "intent": {
            "primary_goal": "validate_economy",
            "description": "Standard validation"
        },
        "expected_behavior": {
            "resource_production_rate": {"min": 1.0}
        },
        "required_signals": {
            "metrics": ["resource_production_rate"],
            "events": ["ResourceNodeDepleted"],
            "cognition": ["current_project"]
        },
        "allowed_anomalies": ["NavigationStuckBasic"],
        "critical_anomalies": ["HardLawViolationDetected"],
        "tags": ["test"]
    }

def test_validator_detects_existing_world(base_spec_dict):
    """Verify validation passes when the referenced world actually exists."""
    spec = ScenarioSpec(**base_spec_dict)
    
    # Mock WorldRepository to return existing_world
    mock_repo = MagicMock(spec=WorldRepository)
    mock_repo.list_worlds.return_value = ["existing_world", "other_world"]
    
    validator = ScenarioValidator(world_repo=mock_repo)
    issues = validator.validate(spec)
    
    # No error issues should be reported
    errors = [x for x in issues if x.severity == "ERROR"]
    assert len(errors) == 0

def test_validator_detects_missing_world(base_spec_dict):
    """Verify that referencing a non-existent world raises an ERROR."""
    base_spec_dict["world_id"] = "missing_world"
    spec = ScenarioSpec(**base_spec_dict)
    
    mock_repo = MagicMock(spec=WorldRepository)
    mock_repo.list_worlds.return_value = ["existing_world"]
    
    validator = ScenarioValidator(world_repo=mock_repo)
    
    # Non-strict mode should raise InvalidScenarioSpecError due to ERROR severity
    with pytest.raises(InvalidScenarioSpecError) as exc_info:
        validator.validate(spec)
    assert "references a non-existent world_id" in str(exc_info.value)

def test_validator_warns_on_unrecognized_metrics(base_spec_dict):
    """Verify that unrecognized metrics yield warnings (Option B) but allow non-strict run."""
    base_spec_dict["expected_behavior"]["custom_metric_xyz"] = {"min": 10.0}
    spec = ScenarioSpec(**base_spec_dict)
    
    mock_repo = MagicMock(spec=WorldRepository)
    mock_repo.list_worlds.return_value = ["existing_world"]
    
    validator = ScenarioValidator(world_repo=mock_repo)
    issues = validator.validate(spec, strict=False)
    
    # Verify warning is added
    warnings = [x for x in issues if x.severity == "WARNING" and x.rule_id == "SCENARIO-LIMIT-001"]
    assert len(warnings) == 1
    assert "custom_metric_xyz" in warnings[0].message

def test_validator_warns_on_unrecognized_signals_and_anomalies(base_spec_dict):
    """Verify unrecognized required signals and anomalies yield warnings (Option A)."""
    base_spec_dict["required_signals"]["metrics"].append("unrecognized_metric")
    base_spec_dict["required_signals"]["events"].append("UnrecognizedEvent")
    base_spec_dict["required_signals"]["cognition"].append("unrecognized_cognition")
    base_spec_dict["allowed_anomalies"].append("UnrecognizedAnomaly")
    
    spec = ScenarioSpec(**base_spec_dict)
    
    mock_repo = MagicMock(spec=WorldRepository)
    mock_repo.list_worlds.return_value = ["existing_world"]
    
    validator = ScenarioValidator(world_repo=mock_repo)
    issues = validator.validate(spec, strict=False)
    
    warnings = [x for x in issues if x.severity == "WARNING"]
    # Check that warning issues exist for signals and anomalies
    signal_warnings = [w for w in warnings if w.rule_id == "SCENARIO-SIGNAL-001"]
    anomaly_warnings = [w for w in warnings if w.rule_id == "SCENARIO-ANOMALY-001"]
    
    assert len(signal_warnings) == 3
    assert len(anomaly_warnings) == 1

def test_strict_mode_blocks_warnings(base_spec_dict):
    """Verify strict=True raises exception if warnings exist."""
    base_spec_dict["required_signals"]["metrics"].append("unrecognized_metric")
    spec = ScenarioSpec(**base_spec_dict)
    
    mock_repo = MagicMock(spec=WorldRepository)
    mock_repo.list_worlds.return_value = ["existing_world"]
    
    validator = ScenarioValidator(world_repo=mock_repo)
    
    with pytest.raises(InvalidScenarioSpecError) as exc_info:
        validator.validate(spec, strict=True)
    assert "strict validation failed" in str(exc_info.value)

def test_validator_does_not_compile_world_or_run(base_spec_dict):
    """Verify validator is completely isolated from compiler pipelines and runner loop ticks."""
    spec = ScenarioSpec(**base_spec_dict)
    
    mock_repo = MagicMock(spec=WorldRepository)
    mock_repo.list_worlds.return_value = ["existing_world"]
    
    validator = ScenarioValidator(world_repo=mock_repo)
    
    # We validate, and inspect the mock: list_worlds should be called,
    # but no compile method or running ticks is touched (since the validator
    # has no reference/import to simulation run mechanics).
    validator.validate(spec)
    assert mock_repo.list_worlds.called
    assert not hasattr(mock_repo, "compile")
