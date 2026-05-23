# Compliance IDs: EXPERIMENT-TEST-001, EXPERIMENT-TEST-002, EXPERIMENT-TEST-003
import pytest
import yaml
from pathlib import Path
from pydantic import ValidationError
from src.lab.schema import (
    ExperimentSpec,
    ExperimentRunSpec,
    ExperimentObservabilitySpec,
    ExperimentAnalysisSpec,
    ExperimentRetentionSpec,
    ExperimentBudgetsSpec,
    InvalidExperimentSpecError,
    load_experiment_spec_from_yaml
)

def test_valid_experimentspec_loads(tmp_path: Path):
    """Verify that a standard valid experiment spec loads cleanly."""
    raw_yaml = """
schema_version: experimentspec.v1
experiment_id: resource_economy_100_seeds
scenario_id: resource_economy_basic
experiment_type: multi_seed_sweep

run:
  ticks: 100000
  seeds: [1, 2, 3, 4, 5]
  repeat_count: 1
  max_parallel_runs: 1

observability:
  mode: LONG_RUN
  record_events: true
  record_metric_windows: true
  record_cognition: false

analysis:
  run_post_analysis: true
  generate_report: true
  run_mining: false
  compare_baseline: false

retention:
  keep_raw_events: true
  keep_reports: true
  max_artifact_mb: 500

budgets:
  max_runtime_minutes: 60
  max_total_artifact_mb: 2000
"""
    yaml_file = tmp_path / "experiment.yaml"
    yaml_file.write_text(raw_yaml)

    spec = load_experiment_spec_from_yaml(yaml_file)
    assert spec.schema_version == "experimentspec.v1"
    assert spec.experiment_id == "resource_economy_100_seeds"
    assert spec.scenario_id == "resource_economy_basic"
    assert spec.experiment_type == "multi_seed_sweep"
    
    assert spec.run.ticks == 100000
    assert spec.run.seeds == [1, 2, 3, 4, 5]
    assert spec.run.repeat_count == 1
    assert spec.run.max_parallel_runs == 1
    
    assert spec.observability.mode == "LONG_RUN"
    assert spec.observability.record_events is True
    assert spec.observability.record_metric_windows is True
    assert spec.observability.record_cognition is False
    
    assert spec.analysis.run_post_analysis is True
    assert spec.analysis.generate_report is True
    assert spec.analysis.compare_baseline is False
    assert spec.analysis.baseline_id is None
    
    assert spec.retention.max_artifact_mb == 500
    assert spec.budgets.max_runtime_minutes == 60
    assert spec.budgets.max_total_artifact_mb == 2000

def test_missing_required_fields(tmp_path: Path):
    """Verify that omitting critical identifiers or blocks is rejected."""
    raw_yaml_no_scenario = """
schema_version: experimentspec.v1
experiment_id: resource_economy_100_seeds
experiment_type: multi_seed_sweep
run:
  ticks: 100000
  seeds: [1]
"""
    file_no_scenario = tmp_path / "no_scenario.yaml"
    file_no_scenario.write_text(raw_yaml_no_scenario)

    with pytest.raises(InvalidExperimentSpecError) as exc_info:
        load_experiment_spec_from_yaml(file_no_scenario)
    assert "scenario_id" in str(exc_info.value) or "Field required" in str(exc_info.value)

def test_invalid_types_or_budgets(tmp_path: Path):
    """Verify that incorrect experiment type or negative budgets are rejected."""
    raw_yaml_invalid_type = """
schema_version: experimentspec.v1
experiment_id: exp_01
scenario_id: scenario_01
experiment_type: invalid_type_mode
run:
  ticks: 100000
  seeds: [1]
observability:
  mode: LONG_RUN
analysis:
  run_post_analysis: true
retention:
  keep_raw_events: true
budgets:
  max_runtime_minutes: -10
"""
    file_invalid = tmp_path / "invalid.yaml"
    file_invalid.write_text(raw_yaml_invalid_type)

    with pytest.raises(InvalidExperimentSpecError) as exc_info:
        load_experiment_spec_from_yaml(file_invalid)
    error_str = str(exc_info.value)
    assert "experiment_type" in error_str or "max_runtime_minutes" in error_str

def test_extra_fields_preserved(tmp_path: Path):
    """Verify that unknown future fields are successfully preserved under extra fields."""
    raw_yaml = """
schema_version: experimentspec.v1
experiment_id: exp_01
scenario_id: scenario_01
experiment_type: single_run
future_config_key: "future_val"
run:
  ticks: 5000
  seeds: [1]
observability:
  mode: STANDARD
analysis:
  run_post_analysis: true
retention:
  max_artifact_mb: 100
budgets:
  max_runtime_minutes: 5
"""
    yaml_file = tmp_path / "future.yaml"
    yaml_file.write_text(raw_yaml)

    spec = load_experiment_spec_from_yaml(yaml_file)
    assert spec.model_extra["future_config_key"] == "future_val"
