# Implementation Plan - Milestone 17: Baseline Generator

We will implement the pure-Python distribution analyzer and threshold generator for multi-run balance baselines.

## Proposed Changes

### Models & Repositories

#### [NEW] [baseline_generator.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/reporting/baseline_generator.py)
- **`DistributionSummary`**: Pydantic model for statistical summaries:
  - `count`: int
  - `min`: float
  - `max`: float
  - `mean`: float
  - `median`: float
  - `p10`: float
  - `p50`: float
  - `p90`: float
  - `p95`: float
  - `stddev`: float
- **`BaselineThresholdSpec`**: Recommended validation boundaries:
  - `metric_name`: str
  - `comparison_operator`: str  # "==", ">=", "<="
  - `threshold_value`: float
  - `is_custom_override`: bool
- **`BaselineConfig`**: Pydantic schema for `baseline.json`:
  - `baseline_id`: str
  - `scenario_name`: str
  - `scenario_type`: str
  - `created_at`: str
  - `source_sweep_id`: str
  - `run_count`: int
  - `accepted_run_count`: int
  - `excluded_run_ids`: List[str]
  - `exclusion_reasons`: Dict[str, str]
  - `is_weak_baseline`: bool
  - `metrics`: Dict[str, DistributionSummary]
  - `threshold_recommendations`: Dict[str, BaselineThresholdSpec]
  - `artifact_schema_version`: str = "baseline_v1"
- **`BaselineGenerator`**:
  - `generate_baseline(sweep_id, base_dir="data/run_sets", manual_exclude: List[str] = None, manual_include: List[str] = None) -> BaselineConfig`
    - Parses `run_index.jsonl` from `RunSetArtifactRepository`.
    - Filters completed runs only.
    - Excludes runs with hard law violations or status FAILED.
    - Resolves custom overrides.
    - Calculates statistics for health, criticals, warnings, violations, RSS memory peak, and latency percentiles.
    - Compiles auto-generated recommended thresholds.
    - Writes `baseline.json` into `data/run_sets/<sweep_id>/baseline.json`.

### CLI Integration

#### [MODIFY] [entry.py](file:///home/vboxuser/Work/rpg-based-simulation/src/cli/entry.py)
- Register `rpg-observe generate-baseline <sweep_id>`.
