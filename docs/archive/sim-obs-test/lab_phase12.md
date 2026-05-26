# Phase 12 — Scenario Lab Workflow

Phase 11 builds the **Worldbuilding Foundation**:

```text
WorldSpec files
WorldRepository
WorldValidator
WorldCompiler
basic recipes
budget guardrails
```

Phase 12 should connect that into a usable workflow:

```text
WorldSpec
+ ScenarioSpec
+ ExperimentSpec
+ Observatory
+ Mining
= Scenario Lab
```

The goal:

> A user or tool can define a world, define what they want to test, run the simulation, collect observability data, analyze the result, and store everything for later comparison.

This is where worldbuilding becomes useful for debugging and balancing.

---

# Phase 12 Main Objective

Build a file-based **Scenario Lab Workflow**.

The workflow should support:

```text
1. Load world definition
2. Validate world
3. Compile world into simulation state
4. Attach scenario intent
5. Attach experiment settings
6. Run simulation
7. Record Observatory artifacts
8. Analyze run
9. Store lab result
10. Prepare for future comparison/mining
```

This phase should **not** yet build the full mutation/balance lab.

---

# Important separation

Phase 12 should formalize three specs:

```text
WorldSpec      = what world exists
ScenarioSpec   = what behavior we want to test
ExperimentSpec = how we run and observe it
```

## WorldSpec

Example:

```text
resource valley
village
regions
workers
shops
resource nodes
factions
quests
```

## ScenarioSpec

Example:

```text
test resource circulation
test pathing bottleneck
test faction war balance
test quest reward delivery
test strategic project churn
```

## ExperimentSpec

Example:

```text
run 100 seeds
100,000 ticks
LONG_RUN observability
generate baseline
run mining
retain artifacts
```

---

# Phase 12 Milestones

```text
Milestone 75 — ScenarioSpec Schema
Milestone 76 — ExperimentSpec Schema
Milestone 77 — LabRun Manifest and Artifact Layout
Milestone 78 — Scenario Lab Orchestrator
Milestone 79 — Observatory Integration
Milestone 80 — Lab Result Store
Milestone 81 — Lab CLI / Tooling
Milestone 82 — Resource, Storage, and Runtime Guardrails
Milestone 83 — Scenario Lab Test Strategy
```

---

# Milestone 75 — ScenarioSpec Schema

## Goal

Define the test intent separately from the world.

A world can be reused by many scenarios.

Example:

```text
world: village_sandbox_basic

scenario A:
  test resource economy

scenario B:
  test quest progression

scenario C:
  test combat invasion
```

---

## File layout

Recommended:

```text
data/scenarios/
  resource_economy_basic/
    scenario.yaml
  pathing_bottleneck_basic/
    scenario.yaml
  quest_chain_basic/
    scenario.yaml
```

---

## Minimal ScenarioSpec structure

```yaml
schema_version: scenariospec.v1
scenario_id: resource_economy_basic
name: Resource Economy Basic
world_id: resource_valley_basic
scenario_type: resource_economy

intent:
  primary_goal: validate_resource_circulation
  description: Ensure workers can harvest resources, return them, and keep production alive.

expected_behavior:
  hard_law_violations:
    max: 0
  resource_production_rate:
    min: 1
  stuck_entity_ratio:
    max: 0.10

required_signals:
  metrics:
    - resource_production_rate
    - active_worker_count
    - inventory_full_ratio
  events:
    - ResourceNodeDepleted
    - NavigationStuck
    - ResourceTargetSelected
  cognition:
    - current_project
    - active_blockers

allowed_anomalies:
  - NavigationStuckBasic

critical_anomalies:
  - HardLawViolationDetected
  - ResourceProductionZero

tags:
  - economy
  - workers
  - resources
```

---

## ScenarioSpec sections

```text
metadata
world reference
scenario type
intent
expected behavior
required signals
allowed anomalies
critical anomalies
observability needs
mining dimensions
tags
```

---

## Required validation

ScenarioSpec validator should check:

```text
scenario_id exists
world_id exists
scenario_type is known or explicitly custom
expected behavior fields are valid
required signals are known or marked experimental
critical anomalies are known
allowed anomalies are known
```

---

## Tests

Add:

```text
tests/unit/lab/test_scenariospec_schema.py
tests/unit/lab/test_scenariospec_validator.py
```

Required tests:

```text
[ ] valid ScenarioSpec loads
[ ] missing scenario_id is rejected
[ ] missing world_id is rejected
[ ] unknown world_id is rejected
[ ] invalid scenario_type is rejected or marked custom
[ ] invalid expected_behavior field is rejected
[ ] unknown required signal is warned or rejected by policy
[ ] critical anomaly list validates against known rules
```

Anti-misdirection tests:

```text
[ ] ScenarioSpec validation does not compile the world
[ ] ScenarioSpec validation does not run the simulation
[ ] unknown future field is handled by explicit policy
```

---

# Milestone 76 — ExperimentSpec Schema

## Goal

Define how the scenario should be executed.

ScenarioSpec says:

```text
what we are testing
```

ExperimentSpec says:

```text
how we run it
```

---

## File layout

```text
data/experiments/
  resource_economy_100_seeds/
    experiment.yaml
  pathing_bottleneck_same_seed_repeat/
    experiment.yaml
```

---

## Minimal ExperimentSpec structure

```yaml
schema_version: experimentspec.v1
experiment_id: resource_economy_100_seeds
scenario_id: resource_economy_basic

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
```

---

## Experiment types

Support these first:

```text
single_run
multi_seed_sweep
same_seed_repeat
baseline_generation
baseline_comparison
```

Do not support mutation experiments yet.

---

## Required validation

ExperimentSpec validator should check:

```text
scenario_id exists
ticks > 0
seed list is not empty
repeat_count > 0
max_parallel_runs >= 1
observability mode is valid
budgets are valid
retention policy is valid
```

---

## Tests

Add:

```text
tests/unit/lab/test_experimentspec_schema.py
tests/unit/lab/test_experimentspec_validator.py
```

Required tests:

```text
[ ] valid ExperimentSpec loads
[ ] missing scenario_id is rejected
[ ] empty seed list is rejected
[ ] invalid tick count is rejected
[ ] invalid observability mode is rejected
[ ] max_parallel_runs below 1 is rejected
[ ] artifact budget below zero is rejected
```

Anti-misdirection tests:

```text
[ ] ExperimentSpec validation does not run simulation
[ ] same_seed_repeat requires repeat_count > 1
[ ] baseline_comparison requires baseline reference
```

---

# Milestone 77 — LabRun Manifest and Artifact Layout

## Goal

Create a stable file layout for lab executions.

This prevents later confusion when hundreds of runs exist.

---

## Recommended layout

```text
data/lab_runs/
  labrun_2026_001/
    lab_run_manifest.json
    world/
      world.yaml
      world_compile_report.json
    scenario/
      scenario.yaml
      scenario_validation_report.json
    experiment/
      experiment.yaml
      experiment_validation_report.json
    runs/
      run_001/
        run_manifest.json
        simulation_events.jsonl
        metric_windows.jsonl
        anomalies.json
        run_report.md
      run_002/
        ...
    analysis/
      lab_summary.json
      lab_summary.md
      comparison_report.json
      mining_report.json
    logs/
      lab_orchestrator.log
```

---

## LabRunManifest fields

```text
lab_run_id
world_id
scenario_id
experiment_id
status
started_at
ended_at
run_count
completed_run_count
failed_run_count
artifact_root
schema_versions
budgets
storage_usage_mb
```

Status values:

```text
CREATED
VALIDATING
COMPILING
RUNNING
ANALYZING
COMPLETED
FAILED
PARTIAL
CANCELLED
```

---

## Tests

Add:

```text
tests/unit/lab/test_labrun_manifest.py
tests/unit/lab/test_lab_artifact_layout.py
```

Required tests:

```text
[ ] lab run directory is created
[ ] manifest is written
[ ] manifest status updates
[ ] artifact paths are resolved safely
[ ] existing lab run is not overwritten accidentally
[ ] partial lab run is represented correctly
```

Security test:

```text
[ ] lab_run_id path traversal is rejected
```

---

# Milestone 78 — Scenario Lab Orchestrator

## Goal

Implement the central workflow controller.

Component:

```text
ScenarioLabOrchestrator
```

---

## Workflow

```text
1. Load WorldSpec
2. Validate WorldSpec
3. Load ScenarioSpec
4. Validate ScenarioSpec
5. Load ExperimentSpec
6. Validate ExperimentSpec
7. Compile world
8. Generate run matrix
9. Execute simulation runs
10. Run Observatory analysis
11. Store lab result
12. Write lab summary
```

---

## Important design

The orchestrator should call existing services.

It should not contain all logic itself.

```text
WorldRepository
WorldValidator
WorldCompiler
ScenarioSpecValidator
ExperimentSpecValidator
RunArtifactRepository
AnalysisPipeline
ScenarioSweeper / MiningExperimentController
LabResultStore
```

---

## Execution mode

Start with:

```text
sequential execution only
```

Reason:

```text
parallel execution complicates determinism, resource budgeting, logs, and storage
```

Parallel execution can be added later.

---

## Tests

Add:

```text
tests/unit/lab/test_scenario_lab_orchestrator.py
tests/integration/lab/test_scenario_lab_single_run_flow.py
tests/integration/lab/test_scenario_lab_multi_seed_flow.py
```

Required tests:

```text
[ ] orchestrator validates world before compilation
[ ] invalid world stops workflow
[ ] invalid scenario stops workflow
[ ] invalid experiment stops workflow
[ ] valid single-run lab completes
[ ] valid multi-seed lab completes
[ ] failed child run marks lab as PARTIAL or FAILED
[ ] lab summary is written
```

Anti-misdirection tests:

```text
[ ] orchestrator does not ignore validation errors
[ ] orchestrator does not silently skip failed runs
[ ] orchestrator does not overwrite existing lab run
```

---

# Milestone 79 — Observatory Integration

## Goal

Connect Scenario Lab to the Observatory artifacts and analysis.

The lab should not create a separate monitoring system.

It should reuse:

```text
RunArtifactRepository
MetricWindowRecorder
EventRecorder
AnalysisPipeline
RunReportGenerator
BaselineComparator
Mining pipeline later
```

---

## Integration behavior

For every run:

```text
compiled world state
  -> simulation run
  -> Observatory artifacts
  -> post-run analysis
  -> run report
```

For the whole lab:

```text
all run reports
  -> lab summary
  -> optional comparison
  -> optional mining
```

---

## Required lab-level summary

```text
lab_summary.json
lab_summary.md
```

Minimum fields:

```text
lab_run_id
world_id
scenario_id
experiment_id
total_runs
completed_runs
failed_runs
average_health_score
critical_count_total
warning_count_total
top_anomalies
worst_run_id
best_run_id
storage_usage_mb
```

---

## Required tests

Add:

```text
tests/integration/lab/test_lab_observatory_integration.py
```

Required tests:

```text
[ ] lab run creates Observatory artifacts per run
[ ] post-run analysis runs after each completed run
[ ] run report exists for each completed run
[ ] lab summary aggregates run reports
[ ] failed run is included in lab summary
[ ] missing run report is reported, not hidden
```

Anti-misdirection test:

```text
[ ] lab summary does not mark success when all child runs failed
```

---

# Milestone 80 — Lab Result Store

## Goal

Store lab results in file-based form for later review.

No database yet.

Component:

```text
LabResultStore
```

---

## Responsibilities

```text
list lab runs
load lab run manifest
load lab summary
load run reports
load validation reports
load compile reports
resolve artifact paths safely
```

---

## Index file

Recommended:

```text
data/lab_runs/lab_index.json
```

Each record:

```text
lab_run_id
world_id
scenario_id
experiment_id
status
started_at
ended_at
run_count
storage_usage_mb
summary_path
```

---

## Tests

Add:

```text
tests/unit/lab/test_lab_result_store.py
```

Required tests:

```text
[ ] lab result store lists lab runs
[ ] loads lab summary
[ ] loads run report by run id
[ ] handles missing summary clearly
[ ] rebuilds lab index from directories
[ ] path traversal blocked
```

---

# Milestone 81 — Lab CLI / Tooling

## Goal

Make the workflow usable.

Recommended commands:

```text
rpg-lab validate-world <world_id>
rpg-lab validate-scenario <scenario_id>
rpg-lab validate-experiment <experiment_id>
rpg-lab run <experiment_id>
rpg-lab status <lab_run_id>
rpg-lab report <lab_run_id>
rpg-lab list
rpg-lab inspect <lab_run_id>
```

Or under one CLI:

```text
rpg-observe lab run <experiment_id>
```

---

## CLI behavior

`run` should:

```text
load experiment
load scenario
load world
validate all
compile world
execute runs
analyze
store result
print lab_run_id
```

---

## Tests

Add:

```text
tests/cli/test_lab_cli.py
```

Required tests:

```text
[ ] validate-world command works
[ ] validate-scenario command works
[ ] validate-experiment command works
[ ] run command creates lab run
[ ] status command shows status
[ ] report command shows report path
[ ] invalid experiment returns non-zero
```

---

# Milestone 82 — Resource, Storage, and Runtime Guardrails

## Goal

Prevent the lab from accidentally generating too much work or too much data.

This is critical.

A lab workflow can easily run:

```text
100 seeds
100,000 ticks
LONG_RUN observability
full event recording
```

That can become expensive.

---

## Guardrail categories

```text
runtime budget
storage budget
entity count budget
event volume budget
parallelism budget
artifact retention budget
analysis time budget
```

---

## Budget check before run

Before execution, estimate:

```text
number of runs
total ticks
expected entity count
expected event volume
expected artifact size
expected runtime
```

Then classify:

```text
OK
WARNING
BLOCKED
```

---

## Example budget policy

```yaml
budgets:
  max_runs: 100
  max_total_ticks: 10000000
  max_parallel_runs: 1
  max_total_artifact_mb: 5000
  max_runtime_minutes: 240
```

---

## Required behavior

```text
WARNING:
  show warning but allow with --confirm

BLOCKED:
  refuse unless --force and profile allows it
```

For CI profile:

```text
force should not be allowed
```

---

## Tests

Add:

```text
tests/unit/lab/test_lab_budget_guardrails.py
```

Required tests:

```text
[ ] small experiment passes budget check
[ ] huge run count triggers warning/block
[ ] huge total ticks triggers warning/block
[ ] artifact budget estimate triggers warning
[ ] CI profile blocks oversized experiment
[ ] local profile requires confirmation for warning
[ ] force flag is audited
```

Anti-misdirection tests:

```text
[ ] budget warning appears in lab summary
[ ] blocked experiment does not create partial run artifacts
```

---

# Milestone 83 — Scenario Lab Test Strategy

## Goal

Prevent the Scenario Lab from becoming fake-complete.

The biggest danger is:

```text
files exist
CLI works
but generated worlds are invalid
or Observatory analysis is disconnected
or reports are misleading
```

So tests must validate full flow, not only file loading.

---

# Required test groups

## 1. Spec tests

```text
WorldSpec
ScenarioSpec
ExperimentSpec
```

Validate shape and schema.

## 2. Validation tests

```text
world validation
scenario validation
experiment validation
budget validation
```

Validate meaning.

## 3. Compilation tests

```text
WorldSpec -> AuthoritativeState
```

Validate actual engine state.

## 4. Run tests

```text
compiled state -> simulation run
```

Validate runtime compatibility.

## 5. Observatory tests

```text
simulation run -> artifacts -> analysis -> report
```

Validate observability integration.

## 6. Lab workflow tests

```text
experiment -> lab_run -> summary
```

Validate end-to-end.

---

# Mandatory end-to-end smoke test

Add:

```text
tests/integration/lab/test_lab_e2e_smoke.py
```

Flow:

```text
1. load resource_valley_basic world
2. load resource_economy_basic scenario
3. load tiny experiment: 2 seeds, 10 ticks
4. validate all
5. compile world
6. run simulations
7. generate run artifacts
8. run analysis
9. generate lab summary
```

Assertions:

```text
[ ] lab_run_manifest.json exists
[ ] world_compile_report.json exists
[ ] each run has run_manifest.json
[ ] each completed run has run_report.json
[ ] lab_summary.json exists
[ ] lab summary includes completed/failed counts
[ ] no validation ERROR is ignored
```

---

# Phase 12 End-to-End Flow

At the end of Phase 12:

```text
1. User/tool creates WorldSpec.
2. User/tool creates ScenarioSpec.
3. User/tool creates ExperimentSpec.
4. Lab validates all specs.
5. Lab compiles world.
6. Lab executes simulation runs.
7. Observatory records artifacts.
8. AnalysisPipeline generates reports.
9. Lab aggregates results.
10. Lab stores manifest, reports, and summaries.
11. User can inspect lab results later.
```

---

# Minimal Phase 12 example set

Create these sample specs:

```text
worlds:
  resource_valley_basic
  combat_arena_basic
  village_sandbox_basic

scenarios:
  resource_economy_basic
  combat_balance_basic
  peaceful_village_basic

experiments:
  resource_economy_single_run
  resource_economy_5_seed_sweep
  combat_balance_single_run
```

Keep them small.

Do not start with huge long-run specs.

---

# What Phase 12 should not do yet

```text
scenario mutation system
balance lab matrix
automatic baseline evolution
AI-generated worlds
visual editor
database result store
full experiment scheduler
distributed execution
```

Those belong later.

---

# Final acceptance criteria for Phase 12

```text
[ ] ScenarioSpec schema exists.
[ ] ExperimentSpec schema exists.
[ ] LabRun manifest exists.
[ ] ScenarioLabOrchestrator exists.
[ ] Lab can validate world + scenario + experiment.
[ ] Lab can compile world.
[ ] Lab can execute a small experiment.
[ ] Lab can produce Observatory artifacts.
[ ] Lab can generate lab summary.
[ ] Lab results are stored file-based.
[ ] Lab CLI can run and inspect experiments.
[ ] Resource/storage guardrails exist.
[ ] End-to-end smoke lab test passes.
```

# My recommendation

Phase 12 should be named:

```text
Scenario Lab Workflow
```

It is the bridge between:

```text
Worldbuilding Foundation
```

and:

```text
Automated Balancing / Mining Lab
```

Do not make it too smart yet.

Make it reliable:

```text
validate
compile
run
observe
analyze
store
```

That is the core workflow.
