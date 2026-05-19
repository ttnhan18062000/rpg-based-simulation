# Test Plan - Milestone 12: Rule Engine Infrastructure with Core Rules

## Unit Tests (`tests/unit/observability/test_rule_engine.py`)
- **Registry and Config validation**:
  - Test registration and disabled rule behavior.
  - Test custom thresholds correctly overrides default parameters from the config dictionary.
- **Rule statuses and skips**:
  - Test rule skipping when a required signal (e.g. `metric_windows`) is missing.
  - Test rule skipping when scenario types do not match.

## Unit Tests (`tests/unit/observability/test_core_rules.py`)
- **Five Core Rules validation**:
  - `HardLawViolationDetected`: verify positive (violation found) and negative (no violation) outcomes.
  - `NavigationStuckBasic`: verify positive (stuck path) and negative (moving path) outcomes.
  - `QuestStalledBasic`: verify positive (stalled quest) and negative (completed quest) outcomes.
  - `ResourceProductionZero`: verify economy freeze warning/error conditions and missing-signal skip states.
  - `GovernorDegradedTooLong`: verify degraded pressure conditions and missing-signal skip states.

## Integration Tests (`tests/integration/observability/test_rule_engine_pipeline.py`)
- **AnalysisPipeline Integration**:
  - Run the `AnalysisPipeline` with `RuleEngine` registered.
  - Assert that all core rules evaluate against standard run outputs, creating correct deterministic anomaly orders and saving them inside `anomalies.json`.
