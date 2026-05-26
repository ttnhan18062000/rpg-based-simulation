# Phase 3 Implementation Plan — Observatory Processing Pipeline

Phase 3 should focus on **end-to-end component flow**, not full data/rule coverage.

The goal is:

> Build the complete Observatory pipeline with minimal core data first.
> Later, add more metrics, policies, hard laws, balance rules, dashboards, and scenario-specific logic.

This follows the final roadmap’s staged direction: avoid jumping directly into heavy Redis/Kafka/out-of-process architecture before the core metrics, events, analyzer, and report pipeline are stable.

---

# Phase 3 Scope

## Main objective

Build a working flow:

```text id="obsm0o0"
simulation run
  -> record run metadata
  -> collect metric windows
  -> record semantic events
  -> record hard law violations
  -> analyze artifacts
  -> produce anomalies
  -> generate report
  -> expose results through CLI/API
```

## What Phase 3 should prove

```text id="obs6j0p"
[ ] We can run a scenario.
[ ] We can collect basic observability artifacts.
[ ] We can analyze the run after completion.
[ ] We can detect a few core anomalies.
[ ] We can generate a useful report.
[ ] We can inspect the run through a stable API/CLI.
```

## What Phase 3 should not try to finish

```text id="obs3dvj"
[ ] Full anomaly rule coverage.
[ ] Full balance profile coverage.
[ ] Full UI dashboard.
[ ] Live Redis/Kafka anomaly daemon.
[ ] ClickHouse/DuckDB warehouse.
[ ] All possible metrics.
[ ] All possible hard laws.
[ ] ML-based anomaly detection.
```

---

# Phase 3 Design Principle

The focus is **flow completeness**.

For every component, implement:

```text id="obskt5y"
minimal data model
minimal working integration
minimal tests
clear extension point
```

Avoid this:

```text id="obsia73"
building 50 rules before the rule engine is stable
building 100 metrics before the artifact format is stable
building advanced dashboards before the report data is reliable
adding external databases before local artifacts are proven
```

---

# Phase 3 Milestone List

```text id="obsza42"
Milestone 9  — Run Artifact Contract and Repository
Milestone 10 — Metric Window Recorder
Milestone 11 — Analysis Pipeline Orchestrator
Milestone 12 — Rule Engine Infrastructure with Core Rules
Milestone 13 — Evidence, Triage, and Report V2
Milestone 14 — Observatory CLI/API Access Layer
```

---

# Milestone 9 — Run Artifact Contract and Repository

## Goal

Create a stable artifact layout for every simulation run.

This is the foundation for post-run analysis. Without a stable run directory contract, analyzers, reports, CI, and future dashboards will drift.

---

## Problem

Right now, different observability outputs may exist separately:

```text id="obs3cot"
simulation_events.jsonl
metrics output
hard law violations
runtime status
report markdown
replay chunks
```

But the Observatory needs a standard contract:

```text id="obsnijc"
Given run_id, I know where every artifact lives.
```

---

## Target flow

```text id="obslrsz"
simulation starts
  -> RunArtifactRepository creates run directory
  -> run_manifest.json is written
  -> metrics/events/violations are written during run
  -> analyzer reads same directory
  -> report is written back to same directory
```

---

## Standard run directory

Recommended layout:

```text id="obsofvx"
data/runs/<run_id>/
  run_manifest.json
  simulation_events.jsonl
  metric_windows.jsonl
  hard_law_violations.jsonl
  runtime_summary.json
  anomalies.json
  anomaly_summary.md
  run_report.md
  run_report.json
  replay/
    manifest.json
    chunk_0000.json
  timelines/
    entity_<id>.json
```

For Phase 3, not every file must exist.

Minimum required:

```text id="obs5mp8"
run_manifest.json
simulation_events.jsonl
metric_windows.jsonl
hard_law_violations.jsonl
anomalies.json
run_report.md
run_report.json
```

---

## Components

```text id="obskbs6"
RunManifest
RunArtifactRepository
RunArtifactWriter
RunArtifactReader
ArtifactSchemaVersion
```

---

## `RunManifest` fields

Minimum fields:

```text id="obsmiu5"
run_id
scenario_name
scenario_type
seed
engine_version
observability_version
observability_mode
started_at
ended_at optional
ticks_requested
ticks_completed
status
artifact_schema_version
```

Optional later:

```text id="obskizq"
git_commit
profile_name
hardware_class
container_id
operator
notes
```

---

## Tasks

### 9.1 Define artifact schema version

Checklist:

```text id="obs12o3"
[x] Define artifact schema version, e.g. "observability_artifact_v1".
[x] Store schema version in run_manifest.json.
[x] Store schema version in report JSON.
[x] Add compatibility check in readers.
```
*Comment: Defined `observability_artifact_v1` inside Pydantic models. Reader enforces compatibility and raises ValueError on unsupported schema versions.*

Notes:

- This prevents future analyzer breakage when event fields change.
- Do not over-engineer migrations yet.

Acceptance:

```text id="obsf8j1"
[x] Analyzer rejects unsupported artifact schema with clear error.
[x] Analyzer accepts current schema.
```

---

### 9.2 Implement `RunArtifactRepository`

Responsibilities:

```text id="obs57b8"
create run directory
resolve artifact paths
check required files
read manifest
write manifest
append JSONL records
write JSON outputs
write Markdown outputs
```

Checklist:

```text id="obspjuk"
[x] Create directory by run_id.
[x] Prevent accidental overwrite unless explicit.
[x] Provide path resolver for each artifact.
[x] Support reading existing run.
[x] Support writing analysis outputs.
[x] Handle missing optional files gracefully.
```
*Comment: Implemented full directory and path resolution contract in `RunArtifactRepository` with overwrite guards.*

Acceptance:

```text id="obszp9v"
[x] New run creates correct directory.
[x] Existing run can be reopened.
[x] Analyzer can locate input files through repository.
```

---

### 9.3 Add run lifecycle status

Statuses:

```text id="obsstuh"
CREATED
RUNNING
COMPLETED
FAILED
ANALYZED
REPORT_GENERATED
```

Checklist:

```text id="obs6cme"
[x] Status changes when run starts.
[x] Status changes when run completes.
[x] Status changes when analysis completes.
[x] Failure status includes reason.
```
*Comment: Manifest status transitions between CREATED -> RUNNING -> COMPLETED/FAILED automatically inside Kernel hook cycles.*

Acceptance:

```text id="obsac76"
[x] Interrupted run is distinguishable from completed run.
[x] Analyzer refuses incomplete run unless --allow-partial is used.
```

---

### 9.4 Connect EventRecorder and MetricWindowRecorder to repository

Checklist:

```text id="obsk9vj"
[x] EventRecorder writes to repository path.
[x] MetricWindowRecorder writes to repository path.
[x] HardLawMonitor writes violations to repository path.
[x] Writers can be disabled by observability mode.
```
*Comment: Integrated EventRecorder, MetricWindowRecorder, and HardLawMonitor to resolve paths from artifact repository directory.*

Acceptance:

```text id="obsfst4"
[x] One simulation run produces all minimum artifact files.
[x] Empty artifact files are still valid when no events/violations happen.
```

---

## Tests

Recommended tests:

```text id="obs6hww"
tests/unit/observability/test_run_artifact_repository.py
tests/integration/observability/test_run_artifact_flow.py
```

Required checks:

```text id="obsnrqc"
[x] Create run directory.
[x] Write/read manifest.
[x] Append/read JSONL artifact.
[x] Handle missing optional artifact.
[x] Reject unsupported schema version.
[x] Prevent accidental overwrite.
```
*Comment: Complete unit and integration test suites cover all required behavior and ensure zero RNG/performance drift.*

---

## Completion checklist

```text id="obshr35"
[x] Run artifact layout is defined.
[x] RunManifest exists.
[x] RunArtifactRepository exists.
[x] Event/metric/violation artifacts use repository paths.
[x] Analyzer can open run directory.
[x] Report generator can write back into run directory.
```

---

# Milestone 10 — Metric Window Recorder

## Goal

Record rolling metric windows for post-run analysis.

Prometheus is good for live metrics, but post-run analysis needs persisted metric windows.

This milestone creates a simple `metric_windows.jsonl` artifact.

---

## Problem

Post-run analyzer should not depend on Prometheus storage.

It should be able to analyze a run from local artifacts:

```text id="obs54s8"
metric_windows.jsonl
simulation_events.jsonl
hard_law_violations.jsonl
```

---

## Target flow

```text id="obsfaz0"
each tick produces runtime/world snapshot
  -> MetricWindowRecorder aggregates by window
  -> every N ticks, write one metric window record
  -> post-run analyzer reads metric_windows.jsonl
```

---

## Window sizes

Start with one default window:

```text id="obsj82o"
window_ticks = 100
```

Later add:

```text id="obsbs57"
100 ticks
1,000 ticks
10,000 ticks
whole run
```

Phase 3 only needs one or two.

Recommended Phase 3:

```text id="obsaseh"
short_window = 100 ticks
long_window = 1000 ticks
```

---

## Core metric window fields

Minimum required:

```text id="obs0j98"
run_id
window_start_tick
window_end_tick
ticks_observed
alive_entities_avg
active_entities_avg
gold_total_avg
tick_compute_ms_avg
tick_compute_ms_p95
memory_rss_bytes_avg
memory_rss_bytes_max
hard_law_violation_count
event_count
anomaly_candidate_count
```

Optional if already available:

```text id="obs44nx"
rejection_count
quest_active_count
quest_completed_count
governor_mode_dominant
worker_utilization_avg
queue_utilization_avg
```

Do not block the milestone if optional fields are missing.

---

## Components

```text id="obsr6ez"
MetricWindowRecorder
MetricWindowAccumulator
MetricWindowRecord
MetricWindowWriter
```

---

## Design logic

The metric recorder should not scan the world.

It should consume existing snapshots:

```text id="obs798v"
WorldMetrics
PressureSignals
RuntimeStatus
HardLawMonitor violation count
EventRecorder event count
```

The final roadmap confirms these sources are the right active V2 basis for metrics.

---

## Tasks

### 10.1 Define `MetricWindowRecord`

Checklist:

```text id="obs5c8x"
[x] Define required fields. # Completed in src/observability/reporting/metric_recorder.py
[x] Define optional fields. # Completed in src/observability/reporting/metric_recorder.py
[x] Include schema version. # Completed in src/observability/reporting/metric_recorder.py
[x] Include run_id. # Completed in src/observability/reporting/metric_recorder.py
[x] Ensure JSON-serializable. # Completed in src/observability/reporting/metric_recorder.py
```

Acceptance:

```text id="obsa8tl"
[x] Empty/minimal record can serialize. # Verified in tests/unit/observability/test_metric_window_recorder.py
[x] Full record can serialize. # Verified in tests/unit/observability/test_metric_window_recorder.py
```

---

### 10.2 Implement accumulator

Responsibilities:

```text id="obsqhnn"
collect per-tick snapshots
compute averages
compute max values
compute p95 for tick compute
count events/violations
flush on window boundary
```

Checklist:

```text id="obs5ejt"
[x] Accept tick snapshot. # Completed in src/observability/reporting/metric_recorder.py
[x] Track tick range. # Completed in src/observability/reporting/metric_recorder.py
[x] Compute avg. # Completed in src/observability/reporting/metric_recorder.py
[x] Compute max. # Completed in src/observability/reporting/metric_recorder.py
[x] Compute p95. # Completed in src/observability/reporting/metric_recorder.py
[x] Reset after flush. # Completed in src/observability/reporting/metric_recorder.py
[x] Handle missing snapshot safely. # Completed in src/observability/reporting/metric_recorder.py
```

Notes:

- Keep implementation simple.
- Do not introduce advanced histogram dependency yet.
- Exact p95 can be computed from per-window list since window is small.

Acceptance:

```text id="obs0v4a"
[x] 100 tick inputs produce one window record. # Verified in tests/unit/observability/test_metric_window_recorder.py
[x] p95 is deterministic. # Verified in tests/unit/observability/test_metric_window_recorder.py
[x] Missing optional values do not crash. # Verified in tests/unit/observability/test_metric_window_recorder.py
```

---

### 10.3 Write `metric_windows.jsonl`

Checklist:

```text id="obsos88"
[x] Append one JSON object per window. # Completed in src/observability/reporting/metric_recorder.py
[x] Flush on simulation end. # Completed in src/observability/reporting/metric_recorder.py
[x] Support partial final window. # Completed in src/observability/reporting/metric_recorder.py
[x] Track write errors. # Completed in src/observability/reporting/metric_recorder.py
[x] Respect observability mode. # Completed in src/observability/reporting/metric_recorder.py
```

Acceptance:

```text id="obsdvb6"
[x] Completed run has metric_windows.jsonl. # Verified in tests/integration/observability/test_metric_windows_flow.py
[x] File contains valid JSONL. # Verified in tests/integration/observability/test_metric_windows_flow.py
[x] Partial final window is not lost. # Verified in tests/integration/observability/test_metric_windows_flow.py
```

---

### 10.4 Integrate with engine run loop

Checklist:

```text id="obs7b4n"
[x] Hook recorder to latest tick snapshot. # Hooked in src/engine/kernel.py
[x] Keep overhead small. # Utilizes existing pre-calculated in-memory snapshots
[x] Avoid locks in hot path where possible. # Non-locking in-memory lists
[x] Do not call heavy analyzer from recorder. # Bounded local calculations
```

Acceptance:

```text id="obsr7qw"
[x] Recorder works during normal scenario run. # Verified in tests/integration/observability/test_metric_windows_flow.py
[x] Event-disabled mode still records metrics if configured. # Verified in tests/integration/observability/test_metric_windows_flow.py
[x] Metrics-disabled mode skips recorder cleanly. # Verified in tests/integration/observability/test_metric_windows_flow.py
```

---

## Tests

Recommended tests:

```text id="obsqfzz"
tests/unit/observability/test_metric_window_recorder.py
tests/integration/observability/test_metric_windows_artifact.py
```

Required checks:

```text id="obs87tb"
[x] Accumulator computes avg/max/p95.
[x] Window flush happens at expected tick.
[x] Partial final window flushes.
[x] JSONL output is valid.
[x] Missing optional fields are tolerated.
[x] Recorder does not scan world state.
```

---

## Completion checklist

```text id="obsb0mf"
[x] MetricWindowRecord exists.
[x] MetricWindowRecorder exists.
[x] metric_windows.jsonl is produced.
[x] Post-run analyzer can read metric windows.
[x] Metric recorder has bounded overhead.
```

---

# Milestone 11 — Analysis Pipeline Orchestrator

## Goal

Create the central orchestrator that runs post-run analysis.

This is the core of the Observatory processing flow.

---

## Problem

Without orchestration, every analyzer/report tool becomes separate and inconsistent.

We need one pipeline:

```text id="obsb759"
open run artifacts
load metadata
load events
load metric windows
load hard law violations
run analyzers
collect anomalies
run triage
generate report
write outputs
```

---

## Target flow

```text id="obs6bnv"
AnalysisPipeline.run(run_id)
  -> Load RunContext
  -> Load EventStream
  -> Load MetricWindows
  -> Load Violations
  -> Run RuleEngine
  -> Run TriageEngine
  -> Run ReportGenerator
  -> Save artifacts
```

---

## Components

```text id="obsecds"
AnalysisPipeline
AnalysisContext
AnalysisInputLoader
AnalysisOutputWriter
AnalyzerRegistry
AnalysisResult
```

---

## `AnalysisContext`

Minimum fields:

```text id="obsb3vz"
run_manifest
events
metric_windows
hard_law_violations
observability_mode
scenario_type
rule_config
```

Do not load huge state snapshots in Phase 3.

---

## `AnalysisResult`

Minimum fields:

```text id="obsl49f"
run_id
status
anomaly_count
critical_count
warning_count
health_score
output_paths
errors
```

---

## Tasks

### 11.1 Implement `AnalysisInputLoader`

Checklist:

```text id="obskycp"
[x] Load run_manifest.json.
[x] Load simulation_events.jsonl.
[x] Load metric_windows.jsonl.
[x] Load hard_law_violations.jsonl.
[x] Handle missing optional files.
[x] Validate schema version.
```

*Comment: Fully implemented in `AnalysisInputLoader`. Loads run manifest using standard repository methods, and processes events, metric windows, and hard law violations. Gracefully tolerates missing optional files.*

Acceptance:

```text id="obsfsis"
[x] Can load completed run.
[x] Can load run with no events.
[x] Can report missing required artifact clearly.
```

---

### 11.2 Implement analyzer registry

Responsibilities:

```text id="obsffgh"
register analyzers
run analyzers in stable order
collect outputs
handle analyzer failures
```

Initial analyzers:

```text id="obsmm0o"
HardLawAnalyzer
BasicMovementAnalyzer
BasicEconomyAnalyzer
BasicQuestAnalyzer
BasicRuntimeAnalyzer
```

Each analyzer can be small.

Checklist:

```text id="obs2tel"
[x] Analyzer interface exists.
[x] Registry can run analyzers.
[x] Analyzer failure is captured.
[x] Pipeline continues or fails based on severity.
```

*Comment: Registry implemented in `AnalyzerRegistry` with pre-registered initial analyzers. Stable execution order is preserved, and exceptions are gracefully contained within `AnalysisResult.errors` without crashing the pipeline.*

Acceptance:

```text id="obs69w9"
[x] Registry runs multiple analyzers.
[x] Failed analyzer is reported in AnalysisResult.
```

---

### 11.3 Implement pipeline execution

Checklist:

```text id="obs968b"
[x] Build AnalysisContext.
[x] Run analyzers.
[x] Collect anomaly candidates.
[x] Send anomalies to triage.
[x] Send final data to report generator.
[x] Write anomalies.json.
[x] Write run_report.md and run_report.json.
[x] Update run manifest status.
```

*Comment: Fully implemented in `AnalysisPipeline.run()`. Compiles full execution scores, health score deduction metrics, triggers `RunReportGenerator` for structured report compilation, and advances the manifest status state to `ANALYZED`.*

Acceptance:

```text id="obsua4s"
[x] One command analyzes a completed run.
[x] Outputs are written to run directory.
[x] Analysis status is visible in manifest.
```

---

### 11.4 Add partial-run mode

A long simulation may fail before completion.

The analyzer should support:

```text id="obsruu4"
--allow-partial
```

Checklist:

```text id="obso1dj"
[x] Refuse partial run by default.
[x] Allow partial run when explicitly enabled.
[x] Mark report as partial.
[x] Avoid false confidence in partial reports.
```

*Comment: Handled via `allow_partial` argument. If a run has incomplete or running status, the loader raises ValueError by default. When enabled, a CAUTION header warning is prepended to the top of `run_report.md` to prevent false confidence.*

Acceptance:

```text id="obsjwtf"
[x] Incomplete run gives clear error.
[x] Partial mode generates clearly marked partial report.
```

---

## Tests

Recommended tests:

```text id="obsy8z7"
tests/unit/observability/test_analysis_pipeline.py
tests/integration/observability/test_analysis_pipeline_flow.py
```

Required checks:

```text id="obsdtxa"
[x] Pipeline loads artifacts.
[x] Pipeline handles empty events.
[x] Pipeline runs registered analyzers.
[x] Pipeline writes anomalies.json.
[x] Pipeline writes report outputs.
[x] Pipeline updates manifest status.
[x] Pipeline supports partial mode.
```

---

## Completion checklist

```text id="obsb41u"
[x] AnalysisPipeline exists.
[x] Input loader exists.
[x] Analyzer registry exists.
[x] Pipeline writes outputs.
[x] Manifest status updates.
[x] One command can analyze a run.
```

---

# Milestone 12 — Rule Engine Infrastructure with Core Rules

## Goal

Implement the rule engine infrastructure with only a small set of core rules.

The purpose is not coverage. The purpose is to prove:

```text id="obspwop"
events + metrics + rules -> anomalies
```

---

## Core idea

Rules should be data-driven enough to evolve, but simple enough for Phase 3.

A rule consumes:

```text id="obsmq65"
events
metric windows
hard law violations
run metadata
```

A rule produces:

```text id="obszl8i"
AnomalyRecord
```

---

## Components

```text id="obs72tu"
RuleEngine
RuleRegistry
RuleContext
RuleResult
AnomalyRecord
RuleConfig
```

---

## `AnomalyRecord` fields

Minimum fields:

```text id="obsrl5n"
anomaly_id
rule_id
severity
domain
message
tick_start
tick_end
affected_entity_ids
affected_resource_ids
affected_region_ids
affected_quest_ids
evidence
suggested_causes
```

Keep fields optional and sparse.

---

## Rule execution model

```text id="obs3f51"
for each registered rule:
    if rule applies to scenario_type:
        evaluate context
        return zero or more anomalies
```

Rules must be deterministic.

---

## Core Phase 3 rules

Implement only these first:

```text id="obsdnak"
HardLawViolationDetected
NavigationStuckBasic
QuestStalledBasic
ResourceProductionZero
GovernorDegradedTooLong
```

### Rule 1 — `HardLawViolationDetected`

Input:

```text id="obsr1w1"
hard_law_violations.jsonl
InvariantViolation SimulationEvent
```

Condition:

```text id="obsc7hz"
any hard law violation exists
```

Severity:

```text id="obs3jtk"
CRITICAL or ERROR
```

Purpose:

```text id="obsb94p"
Prove hard law monitor integrates with analyzer/report.
```

---

### Rule 2 — `NavigationStuckBasic`

Input:

```text id="obsl01z"
NavigationStuck events
or metric window stuck count if available
```

Condition:

```text id="obsetav"
entity stuck_ticks >= threshold
```

Severity:

```text id="obs33tl"
WARNING
```

Purpose:

```text id="obs9ref"
Catch obvious movement liveness failure.
```

---

### Rule 3 — `QuestStalledBasic`

Input:

```text id="obsqde3"
QuestStarted
QuestCompleted
QuestRewardDelivered
metric windows if available
```

Condition:

```text id="obs4k2w"
quest started but not completed after threshold
```

Severity:

```text id="obsfgnn"
WARNING
```

Purpose:

```text id="obsnuyx"
Catch basic quest liveness failure.
```

---

### Rule 4 — `ResourceProductionZero`

Input:

```text id="obs9ggm"
metric_windows.resource_produced_count optional
ResourceNodeDepleted / Harvest events optional
```

Condition:

```text id="obs5wt0"
resource production == 0 for N windows
and scenario_type in resource_economy or mixed_sandbox
```

Severity:

```text id="obs2elw"
ERROR if active workers > 0 is available
WARNING otherwise
```

Purpose:

```text id="obs80v8"
Catch economy freeze.
```

Note:

- If `resource_produced_count` is not available yet, rule should report `SKIPPED_MISSING_SIGNAL`, not fail.
- This is important to avoid drift.

---

### Rule 5 — `GovernorDegradedTooLong`

Input:

```text id="obs97vm"
metric_windows.governor_mode_dominant
GovernorModeChanged events
```

Condition:

```text id="obs41go"
governor mode DEGRADED/SURVIVAL for more than threshold windows
```

Severity:

```text id="obs0zul"
WARNING or ERROR
```

Purpose:

```text id="obsr3zd"
Catch runtime pressure instability.
```

---

## Rule status

Each rule execution should produce status:

```text id="obspzr9"
PASSED
FAILED
SKIPPED_MISSING_SIGNAL
SKIPPED_SCENARIO_TYPE
ERROR
```

This is important.

A rule missing required data should not fake a result.

---

## Tasks

### 12.1 Define rule interface

Checklist:

```text id="obs67p8"
[x] Rule has rule_id.
[x] Rule declares required signals.
[x] Rule declares scenario types.
[x] Rule has evaluate(context).
[x] Rule returns anomalies and status.
```
*Comment: Defined the BaseRule interface in rules_engine.py with rule_id, required_signals, valid_scenarios, and the evaluate lifecycle. Handles missing signals and scenario-specific skips cleanly via rule outcome states.*

Acceptance:

```text id="obs7yj1"
[x] Rule can be registered.
[x] Rule can be skipped when signal missing.
```

---

### 12.2 Implement `RuleEngine`

Checklist:

```text id="obsb3gq"
[x] Load rule registry.
[x] Load rule config.
[x] Evaluate rules deterministically.
[x] Collect anomalies.
[x] Collect rule statuses.
[x] Sort output stably.
```
*Comment: Built the RuleEngine and RuleRegistry in rules_engine.py. Loads rules config from JSON blocks, executes rules deterministically, collects and sorts outcomes, and outputs comprehensive AnomalyRecords.*

Acceptance:

```text id="obsovxg"
[x] Same input produces same anomaly order.
[x] Missing data produces skipped status.
```

---

### 12.3 Implement core rules

Checklist:

```text id="obs30tn"
[x] HardLawViolationDetected.
[x] NavigationStuckBasic.
[x] QuestStalledBasic.
[x] ResourceProductionZero.
[x] GovernorDegradedTooLong.
```
*Comment: Coded all 5 core post-run rules (HardLawViolationDetected, NavigationStuckBasic, QuestStalledBasic, ResourceProductionZero, GovernorDegradedTooLong) with exhaustive tests checking positive, negative, and missing-signal execution paths.*

Acceptance:

```text id="obsaayf"
[x] Each rule has synthetic positive test.
[x] Each rule has negative/no-anomaly test.
[x] Each rule handles missing signal.
```

---

### 12.4 Add minimal rule config

Start with simple local config:

```text id="obsdkgx"
config/observability/rules_core.json
```

Fields:

```text id="obsmivc"
enabled
thresholds
scenario_types
severity_override optional
```

Do not introduce full balance YAML yet.

Checklist:

```text id="obsjw0w"
[x] Rule thresholds configurable.
[x] Rule can be disabled.
[x] Defaults work without config file.
```
*Comment: Integrated simple local rules_core.json config loading support with robust default fallbacks. Tested dynamic threshold configuration and enabled/disabled state gates.*

Acceptance:

```text id="obsnbz8"
[x] Tests can lower threshold.
[x] Disabled rule does not emit anomaly.
```

---

## Tests

Recommended tests:

```text id="obsf0u6"
tests/unit/observability/test_rule_engine.py
tests/unit/observability/test_core_rules.py
tests/integration/observability/test_rule_engine_pipeline.py
```

Required checks:

```text id="obs2pjh"
[x] Rule registry works.
[x] Rule config overrides threshold.
[x] Missing signal returns skipped status.
[x] Hard law violation emits anomaly.
[x] Stuck event emits anomaly.
[x] Quest stall emits anomaly.
[x] Resource production missing data skips cleanly.
[x] Rule output order is deterministic.
```
*Comment: Verified and validated 100% correct behavior via test_rule_engine.py, test_core_rules.py, and test_rule_engine_pipeline.py.*

---

## Completion checklist

```text id="obsk6lx"
[x] RuleEngine exists.
[x] AnomalyRecord exists.
[x] Rule statuses exist.
[x] Five core rules exist.
[x] Rules can skip missing data.
[x] anomalies.json is produced.
```

---

# Milestone 13 — Evidence, Triage, and Report V2

## Goal

Make anomaly outputs useful, not just noisy.

The report should answer:

```text id="obso8mu"
What happened?
Where?
Who was affected?
What evidence supports it?
What should we investigate?
```

---

## Problem

A raw anomaly list is not enough.

Bad output:

```text id="obsmd0l"
NavigationStuck: 100 entities
```

Good output:

```text id="obs1l4p"
Cluster: NavigationStuck near forest_3
Affected: 100 entities
Evidence:
- 82 targeted resource_node_91
- 67 had repeated movement failures
- stuck duration p95 = 1200 ticks
Suggested causes:
- stale resource target
- pathing blockage
- node crowding
```

Phase 3 should implement a basic triage engine.

---

## Components

```text id="obsmi0t"
TriageEngine
EvidenceBuilder
AnomalyCluster
InvestigationHint
ReportV2Renderer
```

---

## Core triage dimensions

Start with:

```text id="obs8dj1"
rule_id
severity
entity_id
region_id
resource_id
quest_id
tick range
```

Later add:

```text id="obs29s3"
faction
building
shop
project
combat engagement
```

---

## Tasks

### 13.1 Implement evidence builder

Responsibilities:

```text id="obsgp9a"
attach supporting events
attach metric window values
attach hard law details
attach timeline snippets if available
```

Checklist:

```text id="obs8saf"
[ ] Evidence includes source artifact name.
[ ] Evidence includes tick range.
[ ] Evidence includes affected IDs.
[ ] Evidence is compact.
[ ] Evidence is JSON-serializable.
```

Acceptance:

```text id="obs17w1"
[ ] Hard law anomaly includes violation evidence.
[ ] Stuck anomaly includes event/timeline evidence.
```

---

### 13.2 Implement basic clustering

Cluster by:

```text id="obs3dlh"
same rule_id
same severity
same region/resource/quest when available
overlapping tick range
```

Checklist:

```text id="obsb4or"
[ ] Group similar anomalies.
[ ] Count affected entities.
[ ] Pick top evidence samples.
[ ] Preserve individual anomaly records.
```

Acceptance:

```text id="obs40ew"
[ ] 100 stuck entities become one cluster plus details.
[ ] Cluster output is deterministic.
```

---

### 13.3 Implement investigation hints

Start with static hint mapping.

Example:

```text id="obs4tr3"
NavigationStuckBasic:
  - check movement legality
  - check occupancy blocking
  - check target reachability
  - check stale resource selection

ResourceProductionZero:
  - check active resource nodes
  - check worker target selection
  - check inventory full loop
  - check shop/storage return logic
```

Checklist:

```text id="obspl7z"
[ ] Hint mapping exists.
[ ] Each core rule has hints.
[ ] Report shows hints.
```

Acceptance:

```text id="obsm93f"
[ ] Every core anomaly has at least one investigation hint.
```

---

### 13.4 Upgrade report generator

Report V2 sections:

```text id="obs7gbz"
1. Executive Summary
2. Run Metadata
3. Health Score
4. Rule Execution Summary
5. Hard Law Violations
6. Anomaly Clusters
7. Evidence Samples
8. Flagged Entity Timelines
9. Runtime Metrics Summary
10. Recommended Investigation Points
11. Missing Signals / Skipped Rules
```

Important addition:

```text id="obsnb4c"
Missing Signals / Skipped Rules
```

This prevents drift. If a rule cannot run because data is missing, the report should say so.

Checklist:

```text id="obs0a3d"
[ ] Add rule status table.
[ ] Add skipped rule section.
[ ] Add anomaly clusters.
[ ] Add evidence samples.
[ ] Add investigation hints.
```

Acceptance:

```text id="obsxkk5"
[ ] Report is useful even with only core rules.
[ ] Report clearly says what data was missing.
```

---

## Tests

Recommended tests:

```text id="obs0wa6"
tests/unit/observability/test_triage_engine.py
tests/unit/observability/test_evidence_builder.py
tests/integration/observability/test_report_v2.py
```

Required checks:

```text id="obsz37e"
[ ] Similar anomalies cluster.
[ ] Evidence attaches correctly.
[ ] Investigation hints appear.
[ ] Skipped rules appear in report.
[ ] Report JSON and Markdown are consistent.
```

---

## Completion checklist

```text id="obs54dx"
[ ] TriageEngine exists.
[ ] EvidenceBuilder exists.
[ ] Anomaly clusters exist.
[ ] Investigation hints exist.
[ ] Report V2 includes skipped rules.
[ ] Report V2 includes evidence and clusters.
```

---

# Milestone 14 — Observatory CLI/API Access Layer

## Goal

Make the Observatory usable by developers without opening raw files manually.

Phase 3 should provide basic commands and read APIs.

Not full UI yet.

---

## Components

```text id="obs8oeq"
Observability CLI commands
Read-only FastAPI endpoints
Run index
Artifact browser
```

---

## CLI commands

Recommended commands:

```text id="obsqlc9"
rpg-observe list-runs
rpg-observe inspect <run_id>
rpg-observe analyze <run_id>
rpg-observe report <run_id>
rpg-observe show-anomalies <run_id>
rpg-observe show-timeline <run_id> <entity_id>
```

Use current project CLI style if one already exists.

---

## API endpoints

Recommended read-only endpoints:

```text id="obsrz7h"
GET /observability/runs
GET /observability/runs/{run_id}
GET /observability/runs/{run_id}/report
GET /observability/runs/{run_id}/anomalies
GET /observability/runs/{run_id}/metric-windows
GET /observability/runs/{run_id}/timeline/{entity_id}
```

No write/control API yet except optional analyze trigger.

---

## Design logic

API should read artifacts through `RunArtifactRepository`.

```text id="obsdfx0"
API
  -> RunArtifactRepository
      -> run_manifest.json
      -> anomalies.json
      -> run_report.md
      -> metric_windows.jsonl
      -> timelines/
```

Do not query engine internals.

Do not depend on simulation being live.

---

## Tasks

### 14.1 Implement run index

Checklist:

```text id="obsypjz"
[ ] Scan data/runs.
[ ] Load manifests.
[ ] Sort by started_at.
[ ] Show status.
[ ] Handle corrupted runs gracefully.
```

Acceptance:

```text id="obs6zl4"
[ ] list-runs shows completed/analyzed runs.
[ ] Corrupted run does not crash listing.
```

---

### 14.2 Implement CLI

Checklist:

```text id="obsfx37"
[ ] list-runs command.
[ ] inspect command.
[ ] analyze command.
[ ] report command.
[ ] show-anomalies command.
[ ] show-timeline command.
```

Acceptance:

```text id="obsoz23"
[ ] Developer can run analysis from CLI.
[ ] Developer can read report path from CLI.
[ ] Developer can inspect anomalies without opening JSON manually.
```

---

### 14.3 Implement read-only API

Checklist:

```text id="obs0kru"
[ ] Add observability router.
[ ] Add run list endpoint.
[ ] Add run detail endpoint.
[ ] Add anomalies endpoint.
[ ] Add report endpoint.
[ ] Add metric windows endpoint.
[ ] Add timeline endpoint.
```

Acceptance:

```text id="obs7ti9"
[ ] API returns JSON for run data.
[ ] Report endpoint returns Markdown or structured JSON.
[ ] Missing run returns 404.
[ ] Missing optional artifact returns clear response.
```

---

### 14.4 Add access guard

This is internal tooling, but still avoid unsafe exposure.

Checklist:

```text id="obsb3oy"
[ ] Read-only by default.
[ ] No arbitrary file path access.
[ ] Only read under data/runs.
[ ] Sanitize run_id.
```

Acceptance:

```text id="obsmxku"
[ ] Path traversal is impossible.
[ ] API cannot read arbitrary server files.
```

---

## Tests

Recommended tests:

```text id="obsjizc"
tests/cli/test_observe_cli.py
tests/api/test_observability_api.py
```

Required checks:

```text id="obsghv1"
[ ] CLI list-runs works.
[ ] CLI analyze works.
[ ] CLI report works.
[ ] API list runs works.
[ ] API get anomalies works.
[ ] API path traversal is blocked.
[ ] Missing run returns 404.
```

---

## Completion checklist

```text id="obszwl6"
[ ] CLI exists.
[ ] Read-only API exists.
[ ] Developer can analyze a run.
[ ] Developer can inspect anomalies.
[ ] Developer can open report.
[ ] API only reads from artifact repository.
```

---

# Phase 3 Integration Flow

At the end of Phase 3, the full flow should be:

```text id="obsw3cu"
1. Start scenario run.
2. RunArtifactRepository creates run directory.
3. RunManifest is written.
4. EventRecorder writes simulation_events.jsonl.
5. MetricWindowRecorder writes metric_windows.jsonl.
6. HardLawMonitor writes hard_law_violations.jsonl.
7. Simulation completes.
8. AnalysisPipeline loads run artifacts.
9. RuleEngine evaluates core rules.
10. TriageEngine groups anomalies.
11. EvidenceBuilder attaches supporting data.
12. ReportGenerator writes run_report.md and run_report.json.
13. CLI/API exposes run outputs.
```

This is the important part.

Even with only five rules and ten metrics, the Observatory is now a real system.

---

# Phase 3 Minimal Data Coverage

## Minimum events

```text id="obs2nmd"
EntityKilled
QuestStarted
QuestCompleted
ResourceNodeDepleted
GovernorModeChanged
InvariantViolation
NavigationStuck
```

## Minimum metric windows

```text id="obs9s69"
alive_entities_avg
gold_total_avg
tick_compute_ms_avg
tick_compute_ms_p95
memory_rss_bytes_avg
event_count
hard_law_violation_count
governor_mode_dominant
```

## Minimum rules

```text id="obsq3bt"
HardLawViolationDetected
NavigationStuckBasic
QuestStalledBasic
ResourceProductionZero
GovernorDegradedTooLong
```

## Minimum reports

```text id="obs0slj"
run metadata
health score
rule status
anomaly clusters
evidence samples
skipped rules
investigation hints
```

This is enough for functional completeness.

---

# Phase 3 Performance Rules

To protect engine performance:

```text id="obsfc9k"
[ ] Analyzer never runs inside tick path.
[ ] Report generator never runs inside tick path.
[ ] Rule engine only runs post-run in Phase 3.
[ ] Metric windows flush every N ticks, not every field every tick.
[ ] Event artifacts are JSONL append-only.
[ ] All buffers are bounded.
[ ] Missing data causes skipped rules, not extra scans.
```

---

# Phase 3 CI Strategy

## Required CI groups

```text id="obsjzg0"
observability-artifacts
observability-analysis
observability-report
observability-api
observability-parity
```

## Must-pass tests

```text id="obs9ysp"
[ ] run artifact repository tests
[ ] metric window recorder tests
[ ] analysis pipeline tests
[ ] rule engine tests
[ ] report V2 tests
[ ] CLI/API tests
[ ] observability enabled/disabled parity tests
```

## Perf smoke

```text id="obsv527"
[ ] Scenario with observability OFF
[ ] Same scenario with observability LIGHT
[ ] Compare tick compute p95
[ ] Overhead under configured threshold
```

---

# Phase 3 Final Acceptance Criteria

Phase 3 is complete when:

```text id="obs7qu4"
[ ] Every simulation run has a standard artifact directory.
[ ] Metric windows are persisted.
[ ] Event artifacts are persisted.
[ ] Hard law violations are persisted.
[ ] AnalysisPipeline can analyze a run from artifacts.
[ ] RuleEngine can run core rules.
[ ] Missing signals are reported as skipped, not hidden.
[ ] TriageEngine clusters anomalies.
[ ] EvidenceBuilder attaches useful evidence.
[ ] RunReport V2 is generated.
[ ] CLI/API can inspect runs.
[ ] No heavy analysis runs inside the engine tick path.
[ ] Observability overhead remains acceptable.
```

---

# Recommended execution order

```text id="obsli95"
1. Milestone 9  — Run Artifact Contract and Repository
2. Milestone 10 — Metric Window Recorder
3. Milestone 11 — Analysis Pipeline Orchestrator
4. Milestone 12 — Rule Engine Infrastructure with Core Rules
5. Milestone 13 — Evidence, Triage, and Report V2
6. Milestone 14 — Observatory CLI/API Access Layer
```

Reason:

```text id="obs2qbo"
Artifacts first.
Then metric windows.
Then pipeline.
Then rules.
Then triage/report.
Then access layer.
```

This avoids drift because every later component depends on the artifact contract.

---

# Phase 4 Preview

Only after Phase 3 works, move to:

```text id="obsyv60"
Phase 4 — Multi-Run and Baseline Analysis
```

That phase should add:

```text id="obs7ioy"
scenario sweeper
multi-seed run comparison
baseline generation
balance envelope config
DuckDB/Parquet optional
scenario health distribution
```

Do not start Phase 4 until Phase 3 proves the local single-run Observatory flow works end to end.
