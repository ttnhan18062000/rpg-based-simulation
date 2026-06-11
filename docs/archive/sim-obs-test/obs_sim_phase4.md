---
status: archive
authority: P2
audience: historical
layer: engine
original_date: unknown
---

# Phase 4 Implementation Plan — Multi-Run Baseline and Balance Analysis

Phase 3 created the **single-run Observatory flow**:

```text
simulation run
  -> artifacts
  -> metric windows
  -> semantic events
  -> anomaly rules
  -> triage
  -> report
  -> CLI/API access
```

Phase 4 should extend this into **multi-run analysis**:

```text
many runs
  -> compare seeds
  -> generate baseline
  -> detect abnormal runs
  -> detect balance drift
  -> produce scenario-level report
```

This phase should still avoid heavy infrastructure. No ClickHouse, Kafka, Redis, or full live anomaly daemon yet. The final clarification report recommends staged delivery, with post-run/local analysis before heavier out-of-process streaming.

---

# Phase 4 Goal

## Main objective

Build a working system that can answer:

```text
Across many runs of the same scenario, what is normal?
Which run is abnormal?
Which seed exposes bad logic?
Which metric is unstable?
Which scenario looks unbalanced?
```

This is where the Observatory starts supporting **balancing** and **deep simulation validation**.

---

# Phase 4 Should Include

```text
1. Scenario run matrix
2. Scenario sweeper
3. Multi-run artifact index
4. Baseline generator
5. Baseline comparator
6. Minimal balance envelope config
7. Scenario-level report
8. CI-friendly pass/fail gate
```

---

# Phase 4 Should Not Include Yet

```text
1. Full balance rule library
2. ML anomaly detection
3. ClickHouse / large event warehouse
4. Live anomaly daemon
5. Full UI dashboard
6. Automatic stat tuning
7. Auto-fixing simulation behavior
```

The goal is still **component flow first**, with minimal useful data.

---

# Phase 4 Milestones

```text
Milestone 15 — Scenario Run Matrix and Sweeper
Milestone 16 — Multi-Run Artifact Index
Milestone 17 — Baseline Generator
Milestone 18 — Baseline Comparator and Drift Detector
Milestone 19 — Minimal Balance Envelope Config
Milestone 20 — Scenario-Level Report and CI Gate
```

---

# Milestone 15 — Scenario Run Matrix and Sweeper

> [!NOTE]
> **Verification & Implementation Note (May 2026)**:
> - **Status**: **100% COMPLIANT & VERIFIED**
> - **Components**: `ScenarioSweepConfig` (validation/bounds check via Pydantic), `ScenarioRunSpec`, `RunSetManifest`, and `ScenarioSweeper` implemented in `src/observability/sweeper.py`.
> - **Execution Mode**: Executes programmatic sweep matrices sequentially under `ObservabilityConfig.set_override_mode(...)` to ensure correct isolation of multi-seed run artifacts.
> - **Tests**: 100% pass rates in `tests/unit/observability/test_sweep_config.py`, `tests/unit/observability/test_scenario_sweeper.py`, and `tests/integration/observability/test_sweep_execution_flow.py`.

## Goal

Run the same scenario across multiple seeds/configurations automatically.

This is the foundation for baseline analysis.

A single long run can show one failure. A sweep shows whether the failure is rare, common, seed-specific, or systematic.

---

## Target flow

```text
sweep config
  -> generate run matrix
  -> execute scenario N times
  -> collect run artifacts
  -> write run_set_manifest.json
```

---

## Example run matrix

```text
scenario: RESOURCE_ECONOMY_1000
seeds: [1, 2, 3, 4, 5]
ticks: 50000
observability_mode: LONG_RUN
profile: default
```

The sweeper should produce:

```text
run RESOURCE_ECONOMY_1000 seed=1
run RESOURCE_ECONOMY_1000 seed=2
run RESOURCE_ECONOMY_1000 seed=3
run RESOURCE_ECONOMY_1000 seed=4
run RESOURCE_ECONOMY_1000 seed=5
```

Each run still produces the Phase 3 artifact directory.

---

## Components

```text
ScenarioSweepConfig
ScenarioRunSpec
ScenarioSweeper
RunSetManifest
SweepExecutor
SweepResult
```

---

## Minimal `ScenarioSweepConfig`

Fields:

```text
sweep_id
scenario_name
scenario_type
seeds
ticks
observability_mode
profile_name optional
max_parallel_runs
stop_on_first_critical
output_dir
```

Keep it simple.

Do not add full YAML balance profile integration yet.

---

## Minimal `RunSetManifest`

Fields:

```text
sweep_id
scenario_name
scenario_type
started_at
ended_at
status
run_ids
seed_by_run_id
ticks_requested
completed_count
failed_count
artifact_schema_version
```

---

## Tasks

### 15.1 Define sweep config model

Checklist:

```text
[ ] Define required fields.
[ ] Validate seeds are non-empty.
[ ] Validate ticks > 0.
[ ] Validate max_parallel_runs >= 1.
[ ] Validate scenario_type is known or explicitly "custom".
[ ] Validate output directory.
```

Notes:

- Start with JSON config or Python config.
- YAML can come later.
- Do not block this milestone on a full scenario authoring system.

Acceptance:

```text
[ ] Valid sweep config loads successfully.
[ ] Invalid empty seed list is rejected.
[ ] Invalid tick count is rejected.
```

---

### 15.2 Generate run matrix

Checklist:

```text
[ ] Convert sweep config into individual run specs.
[ ] Assign unique run_id per seed.
[ ] Preserve scenario name/type.
[ ] Preserve observability mode.
[ ] Preserve tick count.
[ ] Write run matrix preview.
```

Acceptance:

```text
[ ] 5 seeds produce 5 run specs.
[ ] Run IDs are stable or traceable.
[ ] Each run spec contains seed/tick/scenario metadata.
```

---

### 15.3 Implement sequential sweep execution

Start with sequential execution.

Do not implement parallel execution first.

Checklist:

```text
[ ] Execute runs one by one.
[ ] Create artifact directory per run.
[ ] Wait for each run to complete.
[ ] Record run status.
[ ] Continue on failure unless stop_on_first_critical is true.
[ ] Write run_set_manifest.json.
```

Notes:

- Sequential execution is slower but safer.
- Parallel execution can be added later after artifact isolation is stable.

Acceptance:

```text
[ ] Sweeper can execute at least 3 seeds.
[ ] Each run produces Phase 3 artifacts.
[ ] Sweep manifest lists all run IDs.
```

---

### 15.4 Add failure handling

Checklist:

```text
[ ] Mark failed run in run_set_manifest.
[ ] Store failure reason.
[ ] Continue sweep when configured.
[ ] Stop sweep on critical when configured.
[ ] Preserve partial artifacts.
```

Acceptance:

```text
[ ] One failed seed does not corrupt the whole sweep.
[ ] Sweep status clearly says PARTIAL / FAILED / COMPLETED.
```

---

### 15.5 Add minimal CLI command

Command:

```text
rpg-observe sweep <sweep_config.json>
```

Checklist:

```text
[ ] Load sweep config.
[ ] Show run matrix summary.
[ ] Execute sweep.
[ ] Print sweep_id and output path.
```

Acceptance:

```text
[ ] Developer can run a multi-seed sweep from CLI.
```

---

## Tests

Recommended files:

```text
tests/unit/observability/test_sweep_config.py
tests/unit/observability/test_scenario_sweeper.py
tests/integration/observability/test_sweep_execution_flow.py
```

Required checks:

```text
[ ] Sweep config validation works.
[ ] Run matrix generation works.
[ ] Sequential sweep creates multiple runs.
[ ] Failed run is recorded.
[ ] Sweep manifest is written.
```

---

## Completion checklist

```text
[ ] ScenarioSweepConfig exists.
[ ] ScenarioSweeper exists.
[ ] RunSetManifest exists.
[ ] Sequential multi-seed sweep works.
[ ] Sweep CLI exists.
[ ] Sweep produces multiple Phase 3 run artifacts.
```

---

# Milestone 16 — Multi-Run Artifact Index

> [!NOTE]
> **Verification & Implementation Note (May 2026)**:
> - **Status**: **100% COMPLIANT & VERIFIED**
> - **Components**: `RunIndexRecord`, `SweepSummary`, and `RunSetArtifactRepository` in `src/observability/reporting/run_set_repository.py`.
> - **Directory Layout**: Properly stores files in standard structure:
>   - `run_set_manifest.json`
>   - `run_index.jsonl` (line-separated JSON records containing health, tick completion, and anomaly count per run)
>   - `sweep_summary.json` (aggregate sweep stats, worst/best run identification, and common anomaly metrics)
> - **Tests**: Fully verified by sweep indexer tests.

## Goal

Create an index that lets the Observatory find and compare many runs.

Phase 3 can inspect one run. Phase 4 needs to inspect a group of runs.

---

## Problem

Without a run index, multi-run analysis becomes manual:

```text
open run 1
open run 2
open run 3
compare manually
```

We need:

```text
given sweep_id
  -> find all run_ids
  -> load reports
  -> load anomalies
  -> load metric windows
  -> summarize results
```

---

## Target files

Inside sweep directory:

```text
data/run_sets/<sweep_id>/
  run_set_manifest.json
  run_index.jsonl
  sweep_summary.json
  baseline.json
  baseline_comparison.json
  sweep_report.md
```

Each row in `run_index.jsonl` should reference one run.

---

## Components

```text
RunIndexRecord
RunSetArtifactRepository
MultiRunArtifactReader
RunSetSummaryBuilder
```

---

## Minimal `RunIndexRecord`

Fields:

```text
sweep_id
run_id
seed
scenario_name
scenario_type
status
ticks_completed
health_score
critical_count
warning_count
hard_law_violation_count
artifact_path
```

Optional later:

```text
final_hash
compute_p95
memory_peak
stuck_ratio
quest_completion_rate
combat_win_rate_by_faction
```

---

## Tasks

### 16.1 Define run-set artifact layout

Checklist:

```text
[ ] Define data/run_sets/<sweep_id>/ layout.
[ ] Define run_set_manifest.json.
[ ] Define run_index.jsonl.
[ ] Define sweep_summary.json.
[ ] Add schema version.
```

Acceptance:

```text
[ ] Run-set repository can create and reopen sweep directory.
```

---

### 16.2 Build run index from completed runs

Checklist:

```text
[ ] Read each run manifest.
[ ] Read each run_report.json if available.
[ ] Read anomalies.json if available.
[ ] Extract core summary fields.
[ ] Write one RunIndexRecord per run.
```

Acceptance:

```text
[ ] Run index includes all sweep runs.
[ ] Missing report is marked clearly.
[ ] Failed runs are included, not hidden.
```

---

### 16.3 Build sweep summary

Minimum summary:

```text
total_runs
completed_runs
failed_runs
average_health_score
critical_run_count
warning_run_count
worst_run_id
best_run_id
most_common_anomaly_rule_ids
```

Checklist:

```text
[ ] Compute completed/failed counts.
[ ] Compute health score average.
[ ] Identify worst run.
[ ] Count anomaly rule IDs.
[ ] Write sweep_summary.json.
```

Acceptance:

```text
[ ] Sweep summary generated from run index.
[ ] Worst run can be identified.
```

---

### 16.4 Add CLI commands

Commands:

```text
rpg-observe list-sweeps
rpg-observe inspect-sweep <sweep_id>
```

Checklist:

```text
[ ] List available sweeps.
[ ] Show sweep status.
[ ] Show run count.
[ ] Show worst run.
[ ] Show most common anomalies.
```

Acceptance:

```text
[ ] Developer can inspect sweep without opening raw files.
```

---

## Tests

Recommended files:

```text
tests/unit/observability/test_run_set_repository.py
tests/unit/observability/test_run_index_builder.py
tests/integration/observability/test_multi_run_index_flow.py
```

Required checks:

```text
[ ] Run-set directory is created.
[ ] Run index is built from run manifests.
[ ] Failed runs are preserved.
[ ] Sweep summary identifies worst run.
[ ] Missing report does not crash index builder.
```

---

## Completion checklist

```text
[ ] RunSetArtifactRepository exists.
[ ] RunIndexRecord exists.
[ ] run_index.jsonl is generated.
[ ] sweep_summary.json is generated.
[ ] CLI can inspect sweep.
```

---

# Milestone 17 — Baseline Generator

> [!NOTE]
> **Verification & Implementation Note (May 2026)**:
> - **Status**: **100% COMPLIANT & VERIFIED**
> - **Components**: `DistributionSummary`, `BaselineThresholdSpec`, `BaselineConfig`, and `BaselineGenerator` in `src/observability/reporting/baseline_generator.py`.
> - **Algorithms**: Computes p10, p50, p90, p95, min, max, mean, standard deviation deterministically in pure Python without NumPy or third-party performance libraries.
> - **Exclusion Logic**: Automatically filters out runs marked as `FAILED`, runs with any hard law violations, or critical runs (health_score < 60.0). Developer manual overrides (`manual_exclude` and `manual_include`) are supported.
> - **Weak Baselines**: Accurately flags baselines constructed with < 5 accepted runs as `is_weak_baseline: true` with lowered statistical confidence.

## Goal

Generate a baseline from many successful runs of the same scenario.

A baseline defines what is “normal” for that scenario.

---

## Important mindset

Do not predict exact outcomes.

Do not say:

```text
entity 42 should have 300 gold after 2 hours
```

Say:

```text
for RESOURCE_ECONOMY_1000, normal stuck ratio p95 is below 0.12
normal health score p10 is above 75
normal critical anomaly count is 0
```

Baseline should work with distributions.

---

## Target flow

```text
run index + reports + metric windows
  -> compute metric distributions
  -> write baseline.json
```

---

## Components

```text
BaselineGenerator
BaselineMetricSpec
BaselineRecord
BaselineRepository
DistributionSummary
```

---

## Minimal baseline metrics

Start with core data only:

```text
health_score
critical_count
warning_count
hard_law_violation_count
tick_compute_ms_p95
memory_rss_bytes_max
event_count
anomaly_count
```

Add later when available:

```text
stuck_entity_ratio
resource_production_rate
quest_completion_rate
combat_duration_p95
faction_win_rate
inventory_full_ratio
goal_churn_rate
```

---

## `DistributionSummary`

For each metric:

```text
count
min
max
mean
median
p10
p50
p90
p95
stddev
```

---

## `baseline.json`

Minimum structure:

```text
baseline_id
scenario_name
scenario_type
created_at
source_sweep_id
run_count
accepted_run_count
excluded_run_ids
metrics
threshold_recommendations
artifact_schema_version
```

---

## Tasks

### 17.1 Select eligible runs

Checklist:

```text
[ ] Include completed runs only.
[ ] Exclude runs with critical hard law violations by default.
[ ] Allow manual include/exclude override.
[ ] Record excluded run IDs and reasons.
```

Acceptance:

```text
[ ] Failed runs are not silently included.
[ ] Exclusion reasons are visible.
```

---

### 17.2 Compute distribution summaries

Checklist:

```text
[ ] Compute summaries for core metrics.
[ ] Handle missing metric values.
[ ] Require minimum run count.
[ ] Mark weak baseline when run count is too small.
```

Suggested minimum:

```text
minimum_run_count = 5 for development baseline
minimum_run_count = 30 for useful balance baseline
minimum_run_count = 100 for stronger statistical confidence
```

Acceptance:

```text
[ ] Baseline can be generated from 5 runs.
[ ] Baseline marks itself as weak when sample size is low.
```

---

### 17.3 Generate threshold recommendations

Initial simple rules:

```text
critical_count must equal 0
hard_law_violation_count must equal 0
health_score should be >= p10
tick_compute_ms_p95 should be <= p95 * tolerance
memory_rss_bytes_max should be <= p95 * tolerance
anomaly_count should be <= p95 * tolerance
```

Checklist:

```text
[ ] Generate recommended thresholds.
[ ] Mark recommendations as auto-generated.
[ ] Allow human override later.
```

Acceptance:

```text
[ ] baseline.json includes recommended thresholds.
[ ] Report says thresholds are generated from data.
```

---

### 17.4 Save baseline artifact

Checklist:

```text
[ ] Write baseline.json.
[ ] Store in run_set directory.
[ ] Optionally copy to scenario baseline directory.
[ ] Include source sweep ID.
```

Acceptance:

```text
[ ] Baseline can be loaded by comparator.
```

---

### 17.5 Add CLI command

Command:

```text
rpg-observe generate-baseline <sweep_id>
```

Checklist:

```text
[ ] Load sweep.
[ ] Generate baseline.
[ ] Print baseline path.
[ ] Warn if sample size is weak.
```

Acceptance:

```text
[ ] Developer can generate baseline from sweep.
```

---

## Tests

Recommended files:

```text
tests/unit/observability/test_baseline_generator.py
tests/integration/observability/test_baseline_generation_flow.py
```

Required checks:

```text
[ ] Completed runs are included.
[ ] Failed runs are excluded.
[ ] Distribution summaries are correct.
[ ] Weak baseline is marked.
[ ] Threshold recommendations are generated.
[ ] baseline.json is written.
```

---

## Completion checklist

```text
[ ] BaselineGenerator exists.
[ ] baseline.json is produced.
[ ] Distribution summaries are included.
[ ] Failed/critical runs are excluded by default.
[ ] Weak baseline is marked.
[ ] CLI can generate baseline.
```

---

# Milestone 18 — Baseline Comparator and Drift Detector

> [!NOTE]
> **Verification & Implementation Note (May 2026)**:
> - **Status**: **100% COMPLIANT & VERIFIED**
> - **Components**: `MetricComparison`, `ComparisonResult`, `DriftMetricSummary`, `SweepComparisonResult`, and `BaselineComparator` in `src/observability/reporting/baseline_comparator.py`.
> - **Comparison Flow**:
>   - *Single Run*: Evaluates health_score, p95 tick latency, peak memory RSS, and anomaly count against baseline.
>   - *Sweep Comparison*: Aggregates run-level evaluations, identifies outliers (e.g. run health < baseline p10, run RSS > baseline p95), and computes statistical drift indicators showing mean metric shifts ("DEGRADED" | "IMPROVED" | "STABLE") and magnitude.
> - **CLI Integration**: Full exit code validation (returns `1` on FAIL and `0` on PASS/WARNING).

## Goal

Compare a new run or sweep against a baseline.

This is how you detect regression, balance drift, and strange behavior.

---

## Target flows

### Single run comparison

```text
run_report.json + baseline.json
  -> baseline_comparison.json
  -> pass/fail/warn
```

### Sweep comparison

```text
run_index.jsonl + baseline.json
  -> sweep_baseline_comparison.json
  -> identify outlier seeds
```

---

## Components

```text
BaselineComparator
DriftDetector
OutlierDetector
ComparisonResult
MetricComparison
```

---

## Comparison types

### Hard threshold

Example:

```text
critical_count must equal 0
```

### Baseline envelope

Example:

```text
health_score >= baseline.health_score.p10
```

### Tolerance envelope

Example:

```text
tick_compute_ms_p95 <= baseline.tick_compute_ms_p95.p95 * 1.10
```

### Outlier detection

Example:

```text
run stuck_ratio > baseline stuck_ratio p95
```

---

## Minimal comparison metrics

Use only metrics available from Phase 3:

```text
health_score
critical_count
warning_count
hard_law_violation_count
tick_compute_ms_p95
memory_rss_bytes_max
event_count
anomaly_count
```

Do not block on domain-specific metrics.

---

## Tasks

### 18.1 Define comparison result model

Fields:

```text
comparison_id
baseline_id
run_id optional
sweep_id optional
status
metric_comparisons
failed_metrics
warning_metrics
outlier_runs
summary
```

Statuses:

```text
PASS
WARNING
FAIL
INSUFFICIENT_DATA
```

Checklist:

```text
[ ] Define stable result schema.
[ ] Include baseline reference.
[ ] Include evidence per metric.
```

Acceptance:

```text
[ ] Comparison result serializes to JSON.
```

---

### 18.2 Implement single-run comparison

Checklist:

```text
[ ] Load baseline.
[ ] Load run report JSON.
[ ] Compare core metrics.
[ ] Mark pass/warning/fail.
[ ] Write baseline_comparison.json.
```

Acceptance:

```text
[ ] Run with critical_count > 0 fails.
[ ] Run below health score envelope warns or fails.
[ ] Missing metric gives INSUFFICIENT_DATA, not fake pass.
```

---

### 18.3 Implement sweep comparison

Checklist:

```text
[ ] Load run index.
[ ] Compare each run to baseline.
[ ] Identify outlier runs.
[ ] Count pass/warn/fail.
[ ] Write sweep_baseline_comparison.json.
```

Acceptance:

```text
[ ] Worst outlier run is identified.
[ ] Sweep status is derived from run statuses.
```

---

### 18.4 Add drift detector

Simple Phase 4 drift rules:

```text
critical_count increased above zero
health_score distribution shifted down
tick_compute_ms_p95 shifted up
memory_rss_bytes_max shifted up
anomaly_count distribution shifted up
```

Checklist:

```text
[ ] Compare sweep distribution to baseline distribution.
[ ] Mark drift direction.
[ ] Include magnitude.
```

Acceptance:

```text
[ ] Comparator can say health score degraded.
[ ] Comparator can say performance got worse.
```

---

### 18.5 Add CLI commands

Commands:

```text
rpg-observe compare-run <run_id> --baseline <baseline.json>
rpg-observe compare-sweep <sweep_id> --baseline <baseline.json>
```

Checklist:

```text
[ ] Single run comparison works.
[ ] Sweep comparison works.
[ ] Exit code supports CI.
```

Acceptance:

```text
[ ] CI can fail when comparison status is FAIL.
```

---

## Tests

Recommended files:

```text
tests/unit/observability/test_baseline_comparator.py
tests/integration/observability/test_baseline_comparison_flow.py
```

Required checks:

```text
[ ] Critical violation fails comparison.
[ ] Good run passes comparison.
[ ] Missing metric produces insufficient data.
[ ] Sweep comparison identifies outlier.
[ ] Drift detector flags downward health score shift.
[ ] CLI returns failing exit code on FAIL.
```

---

## Completion checklist

```text
[ ] BaselineComparator exists.
[ ] Single-run comparison works.
[ ] Sweep comparison works.
[ ] Drift detection works.
[ ] CI-compatible exit code exists.
```

---

# Milestone 19 — Minimal Balance Envelope Config

> [!NOTE]
> **Verification & Implementation Note (May 2026)**:
> - **Status**: **100% COMPLIANT & VERIFIED**
> - **Components**: `ExpectationValue`, `BalanceEnvelope`, and `BalanceEnvelopeLoader` in `src/observability/reporting/balance_envelope.py`.
> - **Constraints**: Custom balance envelopes define min, max, equals, max_multiplier_from_baseline, and min_multiplier_from_baseline limits with custom severity mapping (PASS, WARNING, FAIL).
> - **Gating Logic**: Multipliers are evaluated dynamically against baseline parameters (`allowed_max = baseline_value * max_multiplier_from_baseline`), yielding custom-severity gating breaches integrated directly into the `BaselineComparator`.

## Goal

Introduce scenario-specific expectations without building a full designer-facing balance system yet.

This is the first version of “what does balanced mean?”

---

## Important principle

Balance config should be minimal and optional.

Do not migrate all profile/config systems yet.

The final report proposes YAML balance profile loading eventually, but for this phase we should only add enough config to support baseline comparison and scenario expectations.

---

## Target flow

```text
balance_envelope.json
  -> analyzer/comparator
  -> scenario-specific rule thresholds
```

---

## Components

```text
BalanceEnvelope
BalanceEnvelopeLoader
ScenarioExpectation
MetricExpectation
```

---

## Minimal config format

Example:

```text
scenario_name: RESOURCE_ECONOMY_1000
scenario_type: resource_economy
expectations:
  critical_count:
    max: 0
    severity: FAIL
  hard_law_violation_count:
    max: 0
    severity: FAIL
  health_score:
    min: 75
    severity: WARNING
  tick_compute_ms_p95:
    max_multiplier_from_baseline: 1.10
    severity: WARNING
```

Use JSON first if easier.

YAML later.

---

## Expectation types

Support only:

```text
min
max
equals
max_multiplier_from_baseline
min_multiplier_from_baseline
```

Do not add complex expressions yet.

---

## Tasks

### 19.1 Define balance envelope schema

Checklist:

```text
[ ] Scenario name.
[ ] Scenario type.
[ ] Metric expectations.
[ ] Severity per expectation.
[ ] Optional baseline dependency.
[ ] Schema version.
```

Acceptance:

```text
[ ] Valid envelope loads.
[ ] Invalid envelope is rejected clearly.
```

---

### 19.2 Integrate envelope with comparator

Checklist:

```text
[ ] Comparator loads envelope if provided.
[ ] Envelope overrides default thresholds.
[ ] Baseline still used for distribution fields.
[ ] Missing metric produces insufficient data.
```

Acceptance:

```text
[ ] Health score min threshold works.
[ ] Critical count max threshold works.
[ ] Baseline multiplier works.
```

---

### 19.3 Integrate envelope with rule engine

For Phase 4, only use envelope for thresholds.

Checklist:

```text
[ ] Rule config can receive scenario_type.
[ ] Rule thresholds can be overridden by envelope.
[ ] Disabled rules remain disabled.
```

Acceptance:

```text
[ ] Resource scenario uses resource thresholds.
[ ] Combat scenario can use different threshold later.
```

---

### 19.4 Add CLI support

Commands:

```text
rpg-observe compare-run <run_id> --baseline <baseline.json> --envelope <envelope.json>
```

Checklist:

```text
[ ] Envelope path accepted.
[ ] Comparison includes envelope name.
[ ] Report shows active expectations.
```

Acceptance:

```text
[ ] Developer can compare run using explicit scenario envelope.
```

---

## Tests

Recommended files:

```text
tests/unit/observability/test_balance_envelope.py
tests/integration/observability/test_balance_envelope_comparison.py
```

Required checks:

```text
[ ] Valid envelope loads.
[ ] Invalid metric expectation rejected.
[ ] Envelope threshold overrides default.
[ ] Missing metric is insufficient data.
[ ] Baseline multiplier expectation works.
```

---

## Completion checklist

```text
[ ] BalanceEnvelope exists.
[ ] BalanceEnvelopeLoader exists.
[ ] Comparator uses envelope.
[ ] Rule engine can receive envelope thresholds.
[ ] CLI accepts envelope path.
```

---

# Milestone 20 — Scenario-Level Report and CI Gate

> [!NOTE]
> **Verification & Implementation Note (May 2026)**:
> - **Status**: **100% COMPLIANT & VERIFIED**
> - **Components**: `CIGateResult` and `SweepReportGenerator` in `src/observability/reporting/sweep_report.py`.
> - **Reports Generated**:
>   - `sweep_report.md`: Complete 12-section Markdown report featuring executive summaries with color-coded status badges, run distribution, baseline references, outliers, performance drift metrics, memory drift metrics, health distributions, and recommended debug points.
>   - `sweep_report.json` and `ci_gate_result.json`: Machine-readable structured validation indices containing all drifts, outliers, and exit parameters.
> - **CI Gate subcommands**: `rpg-observe gate <sweep_id> --baseline <baseline_path> [--envelope <envelope_path>] [--warn-as-fail] [--insufficient-as-fail]` is fully wired inside `src/cli/entry.py` and returns non-zero status code `1` in CI environments upon gate validation failure.

## Goal

Generate a report for the whole sweep/baseline comparison.

This turns multi-run analysis into something useful for developers and CI.

---

## Target outputs

```text
sweep_report.md
sweep_report.json
baseline_comparison.json
ci_gate_result.json
```

---

## Report sections

```text
1. Executive Summary
2. Sweep Metadata
3. Run Distribution
4. Baseline Summary
5. Comparison Result
6. Outlier Seeds
7. Most Common Anomalies
8. Performance Drift
9. Memory Drift
10. Health Score Distribution
11. Failed Expectations
12. Recommended Investigation Points
```

---

## CI gate result

Minimum fields:

```text
status
failed_metrics
warning_metrics
failed_runs
outlier_runs
baseline_id
sweep_id
message
```

Statuses:

```text
PASS
WARNING
FAIL
INSUFFICIENT_DATA
```

---

## Tasks

### 20.1 Generate sweep report data

Checklist:

```text
[ ] Load sweep summary.
[ ] Load run index.
[ ] Load baseline.
[ ] Load comparison result.
[ ] Compute distribution summaries.
[ ] Identify worst seeds.
[ ] Identify common anomalies.
```

Acceptance:

```text
[ ] Report data object includes all required sections.
```

---

### 20.2 Generate Markdown report

Checklist:

```text
[ ] Render executive summary.
[ ] Render run distribution.
[ ] Render health score distribution.
[ ] Render outlier seeds.
[ ] Render failed expectations.
[ ] Render investigation points.
```

Acceptance:

```text
[ ] sweep_report.md is readable.
[ ] Worst seed and failed metrics are visible near top.
```

---

### 20.3 Generate JSON report

Checklist:

```text
[ ] Stable JSON schema.
[ ] Include comparison result.
[ ] Include CI gate status.
[ ] Include links/paths to run reports.
```

Acceptance:

```text
[ ] sweep_report.json can be parsed by CI.
```

---

### 20.4 Implement CI gate

Checklist:

```text
[ ] Gate reads comparison result.
[ ] FAIL status returns non-zero exit code.
[ ] WARNING status can be configured to pass or fail.
[ ] INSUFFICIENT_DATA behavior is configurable.
```

Acceptance:

```text
[ ] CI can fail on hard law violation.
[ ] CI can fail on baseline regression.
[ ] CI can warn on weak baseline.
```

---

### 20.5 Add CLI command

Command:

```text
rpg-observe gate <sweep_id> --baseline <baseline.json> --envelope <envelope.json>
```

Checklist:

```text
[ ] Runs comparison.
[ ] Generates sweep report.
[ ] Writes CI gate result.
[ ] Exits with correct code.
```

Acceptance:

```text
[ ] One command can be used in CI.
```

---

## Tests

Recommended files:

```text
tests/unit/observability/test_sweep_report_generator.py
tests/unit/observability/test_ci_gate.py
tests/integration/observability/test_scenario_level_report_flow.py
```

Required checks:

```text
[ ] Sweep report generated.
[ ] JSON report generated.
[ ] CI gate passes on good sweep.
[ ] CI gate fails on critical metric.
[ ] Warning behavior configurable.
[ ] Insufficient data behavior configurable.
```

---

## Completion checklist

```text
[ ] Sweep report generator exists.
[ ] CI gate exists.
[ ] Sweep report Markdown exists.
[ ] Sweep report JSON exists.
[ ] CI exit code works.
[ ] Outlier seeds and failed expectations are visible.
```

---

# Phase 4 End-to-End Flow

At the end of Phase 4, the flow should be:

```text
1. Developer defines sweep config.
2. ScenarioSweeper runs the same scenario across seeds.
3. Each run produces Phase 3 artifacts.
4. RunSetArtifactRepository indexes all runs.
5. BaselineGenerator creates baseline.json.
6. BaselineComparator compares new runs/sweeps against baseline.
7. BalanceEnvelope optionally adjusts expectations.
8. SweepReportGenerator creates scenario-level report.
9. CI gate passes/fails based on comparison result.
```

---

# Minimal Data Coverage for Phase 4

## Minimal sweep dimensions

```text
scenario_name
scenario_type
seed
ticks
observability_mode
```

## Minimal baseline metrics

```text
health_score
critical_count
warning_count
hard_law_violation_count
tick_compute_ms_p95
memory_rss_bytes_max
event_count
anomaly_count
```

## Minimal envelope expectations

```text
critical_count == 0
hard_law_violation_count == 0
health_score >= threshold
tick_compute_ms_p95 <= baseline tolerance
memory_rss_bytes_max <= baseline tolerance
```

## Minimal CI gate

```text
FAIL if hard law violation exists
FAIL if critical anomaly exists
WARNING if health score below envelope
WARNING if performance p95 above baseline tolerance
```

---

# Phase 4 Performance Rules

Since Phase 4 is post-run and multi-run focused:

```text
[ ] No baseline generation runs inside tick path.
[ ] No sweep report generation runs inside tick path.
[ ] No multi-run comparison runs inside tick path.
[ ] Sweeper runs scenarios as isolated runs.
[ ] Parallel runs are disabled initially.
[ ] Artifact loading is bounded and streaming where possible.
```

---

# Phase 4 Final Acceptance Criteria

Phase 4 is complete when:

```text
[ ] ScenarioSweeper can run multiple seeds.
[ ] Run-set artifact layout exists.
[ ] Run index is generated.
[ ] Sweep summary is generated.
[ ] Baseline can be generated from completed runs.
[ ] Baseline marks weak sample size.
[ ] New run/sweep can be compared against baseline.
[ ] Minimal balance envelope can override expectations.
[ ] Scenario-level report is generated.
[ ] CI gate can pass/fail based on comparison.
[ ] All outputs are local artifacts with stable schema.
```

---

# Recommended Execution Order

```text
1. Milestone 15 — Scenario Run Matrix and Sweeper
2. Milestone 16 — Multi-Run Artifact Index
3. Milestone 17 — Baseline Generator
4. Milestone 18 — Baseline Comparator and Drift Detector
5. Milestone 19 — Minimal Balance Envelope Config
6. Milestone 20 — Scenario-Level Report and CI Gate
```

Reason:

```text
sweeps create data
index organizes data
baseline defines normal
comparator detects drift
envelope adds scenario intent
CI gate enforces release quality
```

---

# Phase 5 Preview

After Phase 4 works, continue to:

```text
Phase 5 — Live Observatory and Developer Inspection
```

That phase should add:

```text
WebSocket event streaming
live run inspection API
focused entity subscription
live anomaly counters
basic Observatory UI
optional Redis/NATS stream adapter
```

Do not start Phase 5 until Phase 4 proves that the offline/batch Observatory can detect useful issues from real runs.
