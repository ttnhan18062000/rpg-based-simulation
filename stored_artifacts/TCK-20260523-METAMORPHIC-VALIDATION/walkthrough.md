# Metamorphic Validation Rules - Walkthrough

We have successfully implemented **Milestone 87: Metamorphic Validation Rules** of the Mutation and Balance Lab (Phase 13). This completes the engine's capability to define and assert metamorphic relationships between mutated variants based on simulation metrics.

---

## 1. Key Accomplishments

### A. Metamorphic Engine and Rules (`src/lab/metamorphic.py`)
- Created a modular validation engine capable of asserting six metamorphic relation types:
  1. `monotonic_non_decreasing`: `compared_val >= baseline_val`
  2. `monotonic_non_increasing`: `compared_val <= baseline_val`
  3. `within_tolerance`: `abs(compared_val - baseline_val) <= tolerance`
  4. `expected_worse`: Evaluates whether a metric shifts in an unfavorable direction:
     - Metrics like `stuck_entity_ratio`, `inventory_full_ratio`, and `hard_law_violations` are worse if they **increase**.
     - Metrics like `resource_production_rate` and `active_worker_count` are worse if they **decrease**.
  5. `expected_better`: The inverse of `expected_worse` (improvement direction).
  6. `no_new_hard_law_violation`: Verifies that compared variant does not introduce new hard law violations relative to the baseline.
- **Robust Telemetry fallbacks**: Added clean handling for missing/null metric values and invalid numeric conversions, returning `status="INSUFFICIENT_DATA"` rather than crashing.
- **Evidence Strength**: Checks seed/run count and flags `weak_evidence=True` when either variant has `< 3` completed runs.

### B. Core Schema Integration (`src/lab/schema.py`, `src/lab/__init__.py`)
- Imported and integrated `MetamorphicComparisonResult` model into the `schema` layer.
- Exported the new components cleanly via the package initialization interface.

---

## 2. Verification

### A. Unit Tests (`tests/unit/lab/test_metamorphic_rules.py`)
Developed 11 detailed test cases verifying:
- Happy paths for monotonic increases/decreases.
- Tolerance boundaries and small variations.
- Expected worse/better mappings.
- Clean `INSUFFICIENT_DATA` response for missing metrics.
- `weak_evidence=True` flag for low run counts (< 3).
- Failure paths return `status="FAILED"` without engine or collection exceptions.

### B. Integration Tests (`tests/integration/lab/test_metamorphic_validation_flow.py`)
Validated real-world experiment expectations and mock metric matrices across multiple variants simultaneously, with 100% pass rates.

### Test execution summary:
```text
tests/unit/lab/test_metamorphic_rules.py::test_monotonic_non_decreasing_passes_when_metric_increases PASSED [ 38%]
tests/unit/lab/test_metamorphic_rules.py::test_monotonic_non_decreasing_fails_when_metric_decreases PASSED [ 39%]
tests/unit/lab/test_metamorphic_rules.py::test_monotonic_non_increasing_passes_when_metric_decreases PASSED [ 40%]
tests/unit/lab/test_metamorphic_rules.py::test_monotonic_non_increasing_fails_when_metric_increases PASSED [ 41%]
tests/unit/lab/test_metamorphic_rules.py::test_within_tolerance_handles_small_differences PASSED [ 42%]
tests/unit/lab/test_metamorphic_rules.py::test_expected_worse_passes_when_target_metric_worsens PASSED [ 43%]
tests/unit/lab/test_metamorphic_rules.py::test_no_new_hard_law_violation_fails_on_hard_law_violation PASSED [ 44%]
tests/unit/lab/test_metamorphic_rules.py::test_missing_metric_produces_insufficient_data PASSED [ 45%]
tests/unit/lab/test_missing_metric_is_not_treated_as_pass PASSED [ 46%]
tests/unit/lab/test_weak_baseline_is_marked_as_weak_evidence PASSED [ 47%]
tests/unit/lab/test_expected_worse_does_not_mean_engine_failure PASSED [ 48%]
tests/integration/lab/test_metamorphic_validation_flow.py::test_metamorphic_validation_flow PASSED [100%]
```

Total lab unit tests executed: **99 passed in 1.62s**
