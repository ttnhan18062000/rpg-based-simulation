---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE4-M18
artifact_type: plan
tags: [sim, obs, phase4, m18]
---

# Implementation Plan - Milestone 18: Baseline Comparator and Drift Detector

We will implement the baseline comparison engine, outlier runs locator, and statistical drift analyzer.

## Proposed Changes

### Models & Repositories

#### [NEW] [baseline_comparator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/reporting/baseline_comparator.py)
- **`MetricComparison`**: Pydantic model for individual metrics:
  - `metric_name`: str
  - `baseline_value`: float
  - `actual_value`: float
  - `status`: str  # "PASS" | "WARNING" | "FAIL" | "INSUFFICIENT_DATA"
  - `message`: str
- **`ComparisonResult`**: Pydantic model for single-run comparisons:
  - `comparison_id`: str
  - `baseline_id`: str
  - `run_id`: str
  - `status`: str  # "PASS" | "WARNING" | "FAIL" | "INSUFFICIENT_DATA"
  - `metric_comparisons`: Dict[str, MetricComparison]
  - `failed_metrics`: List[str]
  - `warning_metrics`: List[str]
  - `summary`: str
- **`DriftMetricSummary`**: Pydantic model for distribution drifts:
  - `metric_name`: str
  - `baseline_mean`: float
  - `sweep_mean`: float
  - `drift_direction`: str  # "DEGRADED" | "IMPROVED" | "STABLE"
  - `magnitude`: float
- **`SweepComparisonResult`**: Pydantic model for sweep comparisons:
  - `comparison_id`: str
  - `baseline_id`: str
  - `sweep_id`: str
  - `status`: str  # "PASS" | "WARNING" | "FAIL" | "INSUFFICIENT_DATA"
  - `run_statuses`: Dict[str, str]
  - `outlier_runs`: List[str]
  - `drifts`: Dict[str, DriftMetricSummary]
  - `summary`: str
- **`BaselineComparator`**:
  - `compare_run(run_id, baseline_path, run_dir="data/runs") -> ComparisonResult`
    - Compares individual run metrics against baseline thresholds.
    - Saves `baseline_comparison.json`.
  - `compare_sweep(sweep_id, baseline_path, base_dir="data/run_sets") -> SweepComparisonResult`
    - Compares multi-run sweep records against baseline thresholds.
    - Compiles drift summaries and flags outlying seeds.
    - Saves `sweep_baseline_comparison.json`.

### CLI Integration

#### [MODIFY] [entry.py](file:///home/vboxuser/Work/rpg-based-simulation/src/cli/entry.py)
- Register `rpg-observe compare-run <run_id> --baseline <baseline_json>`.
- Register `rpg-observe compare-sweep <sweep_id> --baseline <baseline_json>`.
- Return exit code 1 if comparison results in status `FAIL`.
