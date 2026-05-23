# Test Plan — Milestone 75: ScenarioSpec Schema

This test plan defines the automated and E2E verification requirements for the `src.lab` schema, pluggable validation rules, and file-based repository.

## 1. Schema Tests (`tests/unit/lab/test_scenariospec_schema.py`)
- **`test_valid_scenariospec_loads`**:
  - Load a standard YAML scenario spec, assert that all fields parse correctly and attributes are successfully mapped.
- **`test_missing_id_and_world_id_rejected`**:
  - Verify that omitting `scenario_id` or `world_id` raises a clean Pydantic validation error or loader domain error.
- **`test_invalid_limits_rejected`**:
  - Asserts that creating `ExpectedLimitSpec` with `min > max` raises a validation error.
  - Asserts that creating `ExpectedLimitSpec` with neither `min` nor `max` specified raises a validation error.
- **`test_extra_fields_preserved`**:
  - Asserts that arbitrary future fields added to a YAML are preserved in `model_extra`.

## 2. Validator Tests (`tests/unit/lab/test_scenariospec_validator.py`)
- **`test_validator_detects_existing_world`**:
  - Setup a mock/in-memory `WorldRepository` containing `"valid_world"`. Validate a spec targeting `"valid_world"`. Check that no `SCENARIO-REF-001` error is emitted.
- **`test_validator_detects_missing_world`**:
  - Validate a spec targeting `"missing_world"`. Verify that an `ERROR` with code `SCENARIO-REF-001` is emitted.
- **`test_validator_warns_on_unrecognized_metrics`**:
  - Provide a metric under `expected_behavior` that is not in `STANDARD_METRICS`. Verify that a `WARNING` is added but compilation/validation is not blocked.
- **`test_validator_warns_on_unrecognized_signals`**:
  - Provide unrecognized metrics/events/cognition keys. Asserts `SCENARIO-SIGNAL-001` warnings are produced.
- **`test_validator_warns_on_unrecognized_anomalies`**:
  - Provide unrecognized anomalies in `allowed_anomalies` or `critical_anomalies`. Asserts `SCENARIO-ANOMALY-001` warnings are produced.
- **`test_strict_mode_blocks_warnings`**:
  - Run the validator in `strict=True` mode on a spec containing warning issues. Assert that it raises `InvalidScenarioSpecError`.
- **`test_validator_does_not_compile_world_or_run`**:
  - Assert that calling `validator.validate()` does not call compiler pipelines or execute simulation loop ticks.

## 3. Repository Tests (`tests/unit/lab/test_scenario_repository.py`)
- **`test_repository_lists_and_loads_scenarios`**:
  - Save a scenario to a temporary repository directory, list it, load it, and assert semantic equality.
- **`test_repository_index_rebuild`**:
  - Save multiple scenarios, rebuild the index, and verify `scenario_index.json` has correct keys, health statuses, and tags.
- **`test_repository_path_traversal_guards`**:
  - Assert that loading or saving a scenario with paths containing `../` or absolute escalations raising `PermissionError`.
