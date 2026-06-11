---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260523-METAMORPHIC-VALIDATION
artifact_type: investigation
tags: [metamorphic, validation]
---

# Metamorphic Validation Rules - Investigation

## 1. Context and Mechanics
Metamorphic testing is a powerful methodology for validating complex simulations where a single deterministic oracle is impossible or hard to define. Instead of verifying that output exactly equals a specific value, metamorphic relations define how outputs should shift when inputs are systematically mutated.

In the Scenario Lab:
- **Inputs**: base world, base scenario, and applied mutations defining a variant configuration.
- **Outputs**: observability metrics aggregated from simulation sweep execution (e.g. `resource_production_rate`, `stuck_entity_ratio`, `hard_law_violations`).

---

## 2. Metamorphic Rule Design

We will support the following six metamorphic rule comparison types defined in the phase requirements:

### A. Monotonic Non-Decreasing (`monotonic_non_decreasing`)
- **Semantic Meaning**: The metric value for the compared variant should remain the same or increase compared to the baseline variant.
- **Formula**: `compared_value >= baseline_value`
- **Pass Condition**: `compared_value >= baseline_value`

### B. Monotonic Non-Increasing (`monotonic_non_increasing`)
- **Semantic Meaning**: The metric value for the compared variant should remain the same or decrease compared to the baseline variant.
- **Formula**: `compared_value <= baseline_value`
- **Pass Condition**: `compared_value <= baseline_value`

### C. Within Tolerance (`within_tolerance`)
- **Semantic Meaning**: The metric value should remain near the baseline within a designated absolute tolerance band.
- **Formula**: `abs(compared_value - baseline_value) <= tolerance`
- **Pass Condition**: `abs(compared_value - baseline_value) <= tolerance` (defaults to `0.0` if no tolerance is specified)

### D. Expected Worse (`expected_worse`)
- **Semantic Meaning**: The mutation is expected to intentionally worsen the condition monitored by the metric.
- **Definition of "Worse"**:
  - We map standard metrics to their unfavorable direction:
    - `stuck_entity_ratio` -> Worse = **Higher** (increase in stuck agents)
    - `inventory_full_ratio` -> Worse = **Higher**
    - `hard_law_violations` -> Worse = **Higher**
    - `resource_production_rate` -> Worse = **Lower** (decrease in production rate)
    - `active_worker_count` -> Worse = **Lower**
    - Any other custom metric -> Defaults to **Lower** as worse.
- **Pass Condition**: `compared_value` shifts in the worsening direction relative to `baseline_value`.

### E. Expected Better (`expected_better`)
- **Semantic Meaning**: The mutation is expected to intentionally improve the condition monitored by the metric.
- **Definition of "Better"**:
  - Opposite of the worsening directions:
    - `stuck_entity_ratio` -> Better = **Lower**
    - `inventory_full_ratio` -> Better = **Lower**
    - `hard_law_violations` -> Better = **Lower**
    - `resource_production_rate` -> Better = **Higher**
    - `active_worker_count` -> Better = **Higher**
    - Any other custom metric -> Defaults to **Higher** as better.
- **Pass Condition**: `compared_value` shifts in the improving direction relative to `baseline_value`.

### F. No New Hard Law Violation (`no_new_hard_law_violation`)
- **Semantic Meaning**: The compared variant must not introduce any new hard law violations compared to the baseline.
- **Pass Condition**: `compared_violations <= baseline_violations` or `compared_violations == 0`.

---

## 3. Data Flow and API Structure

### MetamorphicRule
A lightweight domain class (or wrapper/extension of `ExpectedRelationshipSpec`) representing the rule to evaluate.

### MetamorphicComparisonResult
Represents the outcome of a metamorphic comparison.
Fields:
- `rule_id`: str (ID of the evaluated expected relationship)
- `status`: str (one of `"PASSED"`, `"FAILED"`, `"INSUFFICIENT_DATA"`)
- `weak_evidence`: bool (flag set to true if either variant has insufficient seed runs, e.g. `< 3` runs)
- `baseline_value`: Optional[float]
- `compared_value`: Optional[float]
- `message`: str (explaining the decision, error, or missing telemetry)

### MetamorphicRuleEngine
Evaluates a collection of rules against loaded variant metrics.
Input:
- `expected_relationships`: list of `ExpectedRelationshipSpec`
- `variant_metrics`: A dictionary of variant ID to a dictionary of metric names and their aggregated values, and optionally run metadata (e.g. `run_count`).
  Example:
  ```python
  {
      "base": {
          "run_count": 5,
          "resource_production_rate": 12.4,
          "stuck_entity_ratio": 0.05,
          "hard_law_violations": 0
      },
      "var_1": {
          "run_count": 5,
          "resource_production_rate": 8.1,
          "stuck_entity_ratio": 0.12,
          "hard_law_violations": 1
      }
  }
  ```

---

## 4. Stability and Resilience
- **Missing Telemetry**: If a rule monitors a metric name that is absent from either the baseline or compared variant's metrics dict, the engine returns a result with `status="INSUFFICIENT_DATA"` rather than crashing or returning `FAILED` or `PASSED`.
- **Zero/None Handling**: Handles `None` values or divide-by-zero bounds gracefully.
- **Evidence Strength**: Checks the `run_count` (number of completed seeds) for each variant. If either `run_count` is missing or is `< 3`, it marks the outcome as `weak_evidence = True`.
