# Compliance IDs: EXPERIMENT-TEST-004, EXPERIMENT-TEST-005, EXPERIMENT-TEST-006
import pytest
from unittest.mock import MagicMock
from src.lab.schema import ExperimentSpec, InvalidExperimentSpecError
from src.lab.repository import ScenarioRepository
from src.lab.validator import (
    ExperimentValidator,
    ScenarioExistenceRule,
    ExperimentParameterRule,
    ExperimentObservabilityRule
)

@pytest.fixture
def base_exp_dict():
    return {
        "schema_version": "experimentspec.v1",
        "experiment_id": "test_experiment",
        "scenario_id": "existing_scenario",
        "experiment_type": "single_run",
        "run": {
            "ticks": 5000,
            "seeds": [42],
            "repeat_count": 1,
            "max_parallel_runs": 1
        },
        "observability": {
            "mode": "STANDARD",
            "record_events": True,
            "record_metric_windows": True,
            "record_cognition": False
        },
        "analysis": {
            "run_post_analysis": True,
            "generate_report": True,
            "run_mining": False,
            "compare_baseline": False
        },
        "retention": {
            "keep_raw_events": True,
            "keep_reports": True,
            "max_artifact_mb": 500
        },
        "budgets": {
            "max_runtime_minutes": 60,
            "max_total_artifact_mb": 2000
        }
    }

def test_scenario_existence_checks(base_exp_dict):
    """Verify validation passes when the referenced scenario exists, and errors when missing."""
    spec = ExperimentSpec(**base_exp_dict)

    # 1. Scenario exists
    mock_scenario_repo = MagicMock(spec=ScenarioRepository)
    mock_scenario_repo.list_scenarios.return_value = ["existing_scenario", "other_scenario"]

    validator = ExperimentValidator(scenario_repo=mock_scenario_repo)
    issues = validator.validate(spec)
    assert len([x for x in issues if x.severity == "ERROR"]) == 0

    # 2. Scenario is missing
    base_exp_dict["scenario_id"] = "missing_scenario"
    spec_missing = ExperimentSpec(**base_exp_dict)
    
    with pytest.raises(InvalidExperimentSpecError) as exc_info:
        validator.validate(spec_missing)
    assert "references a non-existent scenario_id" in str(exc_info.value)

def test_same_seed_repeat_constraints(base_exp_dict):
    """Verify that same_seed_repeat type validates repeat_count and warns on multiple seeds."""
    base_exp_dict["experiment_type"] = "same_seed_repeat"
    base_exp_dict["run"]["repeat_count"] = 1  # Invalid: must be > 1
    base_exp_dict["run"]["seeds"] = [42, 43]  # Triggers warning
    
    spec = ExperimentSpec(**base_exp_dict)
    
    mock_scenario_repo = MagicMock(spec=ScenarioRepository)
    mock_scenario_repo.list_scenarios.return_value = ["existing_scenario"]
    validator = ExperimentValidator(scenario_repo=mock_scenario_repo)
    
    # 1. Non-strict: Should error on repeat_count <= 1
    with pytest.raises(InvalidExperimentSpecError) as exc_info:
        validator.validate(spec, strict=False)
    assert "requires repeat_count to be greater than 1" in str(exc_info.value)

    # 2. Correct repeat_count, checks warning for multiple seeds
    base_exp_dict["run"]["repeat_count"] = 5
    spec_warn = ExperimentSpec(**base_exp_dict)
    issues = validator.validate(spec_warn, strict=False)
    
    warnings = [x for x in issues if x.severity == "WARNING"]
    assert len(warnings) == 1
    assert "typically runs a single seed" in warnings[0].message

def test_baseline_comparison_constraints(base_exp_dict):
    """Verify that baseline_comparison type requires compare_baseline=True and a baseline_id."""
    base_exp_dict["experiment_type"] = "baseline_comparison"
    # Invalid: compare_baseline is False, and baseline_id is None
    spec = ExperimentSpec(**base_exp_dict)
    
    mock_scenario_repo = MagicMock(spec=ScenarioRepository)
    mock_scenario_repo.list_scenarios.return_value = ["existing_scenario"]
    validator = ExperimentValidator(scenario_repo=mock_scenario_repo)
    
    with pytest.raises(InvalidExperimentSpecError) as exc_info:
        validator.validate(spec)
    assert "requires analysis.compare_baseline to be set to True" in str(exc_info.value)

    # Correct compare_baseline but missing baseline_id
    base_exp_dict["analysis"]["compare_baseline"] = True
    spec_no_id = ExperimentSpec(**base_exp_dict)
    with pytest.raises(InvalidExperimentSpecError) as exc_info:
        validator.validate(spec_no_id)
    assert "requires analysis.baseline_id to be specified" in str(exc_info.value)

    # Fully valid baseline_comparison
    base_exp_dict["analysis"]["baseline_id"] = "baseline_01"
    spec_valid = ExperimentSpec(**base_exp_dict)
    issues = validator.validate(spec_valid)
    assert len([x for x in issues if x.severity == "ERROR"]) == 0

def test_observability_modes_enforcement(base_exp_dict):
    """Verify that invalid observability modes are rejected."""
    base_exp_dict["observability"]["mode"] = "INVALID_MODE_XYZ"
    spec = ExperimentSpec(**base_exp_dict)
    
    mock_scenario_repo = MagicMock(spec=ScenarioRepository)
    mock_scenario_repo.list_scenarios.return_value = ["existing_scenario"]
    validator = ExperimentValidator(scenario_repo=mock_scenario_repo)
    
    with pytest.raises(InvalidExperimentSpecError) as exc_info:
        validator.validate(spec)
    assert "Observability mode 'INVALID_MODE_XYZ' is invalid" in str(exc_info.value)

def test_validator_strict_mode(base_exp_dict):
    """Verify that strict=True turns warnings into exceptions."""
    base_exp_dict["experiment_type"] = "same_seed_repeat"
    base_exp_dict["run"]["repeat_count"] = 5
    base_exp_dict["run"]["seeds"] = [42, 43]  # Triggers warning
    spec = ExperimentSpec(**base_exp_dict)
    
    mock_scenario_repo = MagicMock(spec=ScenarioRepository)
    mock_scenario_repo.list_scenarios.return_value = ["existing_scenario"]
    validator = ExperimentValidator(scenario_repo=mock_scenario_repo)
    
    # 1. Non-strict passes
    issues = validator.validate(spec, strict=False)
    assert len([x for x in issues if x.severity == "WARNING"]) == 1
    
    # 2. Strict raises exception
    with pytest.raises(InvalidExperimentSpecError) as exc_info:
        validator.validate(spec, strict=True)
    assert "Experiment strict validation failed" in str(exc_info.value)

def test_no_execution_side_effects(base_exp_dict):
    """Verify validation runs without executing engine loops or side effects."""
    spec = ExperimentSpec(**base_exp_dict)
    
    mock_scenario_repo = MagicMock(spec=ScenarioRepository)
    mock_scenario_repo.list_scenarios.return_value = ["existing_scenario"]
    validator = ExperimentValidator(scenario_repo=mock_scenario_repo)
    
    validator.validate(spec)
    assert mock_scenario_repo.list_scenarios.called
    assert not hasattr(mock_scenario_repo, "run")
