# Metamorphic Validation Rules - Test Plan

## 1. Unit Tests
File path: `tests/unit/lab/test_metamorphic_rules.py`

### Test Cases
- **`test_monotonic_non_decreasing_passes_on_increase`**:
  - Verifies that `monotonic_non_decreasing` passes when the compared metric value is greater than or equal to the baseline value.
- **`test_monotonic_non_decreasing_fails_on_decrease`**:
  - Verifies that `monotonic_non_decreasing` fails when the compared metric value is less than the baseline value.
- **`test_monotonic_non_increasing_passes_on_decrease`**:
  - Verifies that `monotonic_non_increasing` passes when the compared metric value is less than or equal to the baseline value.
- **`test_monotonic_non_increasing_fails_on_increase`**:
  - Verifies that `monotonic_non_increasing` fails when the compared metric value is greater than the baseline value.
- **`test_within_tolerance_handles_small_differences`**:
  - Verifies that `within_tolerance` passes when `abs(compared - baseline) <= tolerance` and fails when it is greater.
- **`test_expected_worse_passes_on_worse`**:
  - Verifies that `expected_worse` passes when metrics shift in unfavorable directions (e.g. `stuck_entity_ratio` increases or `resource_production_rate` decreases).
- **`test_expected_worse_fails_on_better`**:
  - Verifies that `expected_worse` fails when metrics shift in favorable directions.
- **`test_expected_better_passes_on_better`**:
  - Verifies that `expected_better` passes when metrics shift in favorable directions.
- **`test_expected_better_fails_on_worse`**:
  - Verifies that `expected_better` fails when metrics shift in unfavorable directions.
- **`test_no_new_hard_law_violation_fails_on_increase`**:
  - Verifies that `no_new_hard_law_violation` fails when compared variant's violations count is greater than the baseline's count.
- **`test_missing_metric_produces_insufficient_data`**:
  - Verifies that missing metrics yield `INSUFFICIENT_DATA` cleanly.
- **`test_weak_baseline_is_marked_as_weak_evidence`**:
  - Verifies that `weak_evidence=True` is flagged when either variant has `run_count < 3`.
- **`test_expected_worse_does_not_mean_engine_failure`**:
  - Verifies that rule evaluation failure returns a `FAILED` result cleanly without raising engine exceptions.

---

## 2. Integration Tests
File path: `tests/integration/lab/test_metamorphic_validation_flow.py`

### Test Cases
- **`test_metamorphic_validation_flow`**:
  - Validates a full end-to-end evaluation flow using mock sweep metrics derived from scenario/experiment spec formats, confirming that all rules are integrated, executed, and aggregated correctly in a final summary scorecard.
