# Phase 9 — Simulation Mining and AI-Assisted Investigation

Yes, Phase 9 should exist.

After Phase 8, the system can already observe, analyze, explain, review, and baseline simulation behavior. Phase 9 should use that foundation to answer:

> We ran hundreds of long simulations.
> What should engineers investigate first?

This phase should combine:

1. **large-scale simulation runs**
2. **data engineering pipeline**
3. **deterministic mining logic**
4. **evidence pack generation**
5. **AI Agent investigation**
6. **engineering backlog generation**

The AI Agent should not replace deterministic analysis. It should sit **on top of structured data and evidence**.

The final feasibility roadmap already supports this direction because it recommends staged artifacts, post-run analysis, reports, baselines, and optional analytical storage before heavier live infrastructure.

---

# Core principle

Do not feed the AI Agent raw chaos.

Bad flow:

```text
hundreds of runs
  -> dump all files to AI
  -> ask “what is wrong?”
```

Good flow:

```text
hundreds of runs
  -> build structured dataset
  -> run deterministic mining
  -> generate evidence packs
  -> ask AI Agent to prioritize and explain
  -> engineers review
```

The AI Agent should receive **compressed, relevant, evidence-backed investigation packs**, not millions of raw events.

---

# Phase 9 main goal

Build a system that can run:

```text
same scenario
many seeds
long duration
full observability enabled
```

Then produce:

```text
ranked engineering investigation backlog
```

with evidence:

```text
affected runs
affected seeds
affected ticks
affected entities
affected resources
affected quests
affected systems
supporting metrics
supporting events
suggested first debugging step
```

---

# Phase 9 should include

- Mining experiment controller
- Large sweep dataset builder
- Data completeness auditor
- Determinism auditor
- Cross-run feature extractor
- Outlier detector
- Pattern clustering engine
- Recurring failure miner
- Priority scoring engine
- Evidence pack builder
- AI Agent investigation orchestrator
- Engineering backlog generator
- Next instrumentation recommender
- Human review loop

---

# Phase 9 should not include yet

- Automatic code fixing
- Automatic balance tuning
- ML model training
- Autonomous production changes
- Full natural-language chat UI over all data
- Expensive distributed data platform unless needed
- Letting AI make unsupported claims

---

# Phase 9 Milestones

Continue from Phase 8:

```text
Milestone 49 — Mining Experiment Controller
Milestone 50 — Mining Dataset Builder
Milestone 51 — Data Quality and Determinism Auditor
Milestone 52 — Cross-Run Pattern Mining Engine
Milestone 53 — Priority Scoring and Investigation Backlog
Milestone 54 — Evidence Pack Builder
Milestone 55 — AI Agent Investigation Orchestrator
Milestone 56 — Next Instrumentation and Experiment Recommender
Milestone 57 — Phase 9 Review Workflow and Quality Gate
```

---

# Milestone 49 — Mining Experiment Controller

## Goal

Control large simulation experiments.

This is different from normal sweeps.

Phase 4 had basic multi-run sweeps. Phase 9 needs structured mining experiments.

---

## Experiment types

Support these experiment modes:

| Mode                       | Purpose                                 |
| -------------------------- | --------------------------------------- |
| `same_seed_repeat`         | detect nondeterminism                   |
| `multi_seed_sweep`         | discover behavior patterns              |
| `version_comparison`       | detect regression                       |
| `profile_comparison`       | compare balance profiles                |
| `observability_comparison` | check if observability changes behavior |
| `stress_long_run`          | find long-horizon degradation           |

---

## Key idea

Same scenario + same seed is mainly for determinism.

Same scenario + many seeds is mainly for discovery.

So Phase 9 should support both.

---

## Components

```text
MiningExperimentConfig
MiningExperimentController
MiningRunMatrixBuilder
MiningExperimentManifest
MiningExperimentResult
```

---

## `MiningExperimentConfig`

Minimum fields:

```text
experiment_id
experiment_type
scenario_name
scenario_type
seeds
repeat_count
ticks
engine_version
balance_profile
expectation_pack
observability_profile
max_parallel_runs
output_dir
```

For same-seed repeat:

```text
scenario_name = RESOURCE_ECONOMY_1000
seeds = [42]
repeat_count = 100
ticks = 100000
experiment_type = same_seed_repeat
```

For multi-seed sweep:

```text
scenario_name = RESOURCE_ECONOMY_1000
seeds = [1..100]
repeat_count = 1
ticks = 100000
experiment_type = multi_seed_sweep
```

---

## Required logic

### 49.1 Run matrix generation

Generate concrete run specs:

```text
run_id
scenario
seed
repeat_index
engine_version
balance_profile
observability_profile
ticks
```

### 49.2 Experiment manifest

Write:

```text
data/mining_experiments/<experiment_id>/experiment_manifest.json
```

Include:

```text
experiment_id
experiment_type
scenario_name
seed_count
repeat_count
run_count
started_at
ended_at
status
run_ids
artifact_paths
```

### 49.3 Execution control

Start simple:

```text
sequential execution first
parallel execution later
```

Parallelism can cause nondeterminism or resource distortion, so do not start there.

---

## Outputs

```text
experiment_manifest.json
run_matrix.jsonl
experiment_status.json
```

---

## Acceptance criteria

```text
[ ] Can run same-seed repeat experiment.
[ ] Can run multi-seed sweep experiment.
[ ] Each run produces normal Phase 3/4 artifacts.
[ ] Experiment manifest links all run artifacts.
[ ] Failed runs are recorded, not hidden.
```

---

# Milestone 50 — Mining Dataset Builder

## Goal

Convert hundreds of run artifacts into one queryable dataset.

This is the data engineering layer.

The AI Agent should not manually read hundreds of JSON files. The system should prepare a structured dataset first.

---

## Recommended storage

Use:

```text
Parquet + DuckDB
```

Do not jump to ClickHouse unless local analysis becomes too slow.

---

## Components

```text
MiningDatasetBuilder
MiningDatasetManifest
RunFeatureExtractor
EventFeatureExtractor
MetricFeatureExtractor
AnomalyFeatureExtractor
DatasetQueryService
```

---

## Dataset layout

```text
data/mining_experiments/<experiment_id>/dataset/
  dataset_manifest.json
  runs.parquet
  metric_windows.parquet
  simulation_events.parquet
  anomalies.parquet
  hard_law_violations.parquet
  findings.parquet
  reviews.parquet
  entity_timeline_samples.parquet
  run_features.parquet
  seed_features.parquet
```

Minimum first version:

```text
runs.parquet
metric_windows.parquet
anomalies.parquet
hard_law_violations.parquet
run_features.parquet
```

Do not require full event warehouse first.

---

## Important table: `run_features`

This is the most important table for AI-assisted mining.

One row per run.

Fields:

```text
run_id
seed
repeat_index
scenario_name
scenario_type
status
ticks_completed
health_score
critical_count
warning_count
hard_law_violation_count
anomaly_count
stuck_anomaly_count
quest_stall_count
economy_freeze_count
governor_degraded_count
tick_compute_ms_p95
memory_rss_bytes_max
event_count
dropped_event_count
top_anomaly_rule
top_domain
worst_tick_range_start
worst_tick_range_end
```

This lets the system quickly identify suspicious runs.

---

## Required logic

### 50.1 Artifact normalization

Convert different artifact files into stable tables.

### 50.2 Feature extraction

Extract run-level features.

Examples:

```text
total anomalies
critical anomalies
most common rule
first hard law violation tick
max degraded governor window
p95 tick compute
max memory
event count
```

### 50.3 Missing data handling

Never fake data.

Use:

```text
null
missing_signal = true
skipped_reason
```

### 50.4 Dataset manifest

Include:

```text
experiment_id
source_run_count
valid_run_count
table_paths
record_counts
schema_versions
created_at
```

---

## Acceptance criteria

```text
[ ] Hundreds of run artifacts can be converted into one dataset.
[ ] Missing artifacts are recorded.
[ ] Run-level feature table exists.
[ ] DuckDB can query worst runs and common anomalies.
[ ] Dataset build is reproducible.
```

---

# Milestone 51 — Data Quality and Determinism Auditor

## Goal

Before asking “what is wrong with the simulation,” confirm the data is trustworthy.

---

# Part A — Data Quality Auditor

## Components

```text
DataCompletenessAuditor
SchemaConsistencyAuditor
ArtifactIntegrityAuditor
RunValidityClassifier
```

## Checks

```text
run count
completed count
failed count
partial count
missing artifacts
schema version mismatch
engine version mismatch
scenario config mismatch
corrupted JSONL
empty event files
missing metric windows
missing reports
```

## Output

```text
data_quality_report.json
data_quality_report.md
```

## Classification

Each run should be classified:

```text
VALID_FOR_MINING
VALID_PARTIAL
INVALID_MISSING_ARTIFACTS
INVALID_SCHEMA_MISMATCH
INVALID_ENGINE_VERSION_MISMATCH
INVALID_CORRUPTED_ARTIFACT
```

---

# Part B — Determinism Auditor

## Components

```text
DeterminismAuditor
RepeatGroupComparator
HashComparator
ReplayComparator
EarliestDivergenceFinder
ObservabilitySideEffectDetector
```

## Checks for same-seed repeat

Compare:

```text
final state hash
replay hash
event count
anomaly count
hard law count
metric windows
run report logical fields
```

Performance can vary slightly, but logical outputs should match.

---

## Determinism verdict

```text
DETERMINISTIC
SUSPICIOUS_NONDETERMINISM
CONFIRMED_NONDETERMINISM
INSUFFICIENT_DATA
```

---

## Important logic

If same seed repeated 100 times gives different final hashes:

```text
P0 issue
```

Possible causes:

```text
thread scheduling
unordered iteration
time-based randomness
observability side effect
non-deterministic collection ordering
parallel worker race
```

---

## Outputs

```text
determinism_audit.json
determinism_audit.md
earliest_divergence_report.json
```

---

## Acceptance criteria

```text
[ ] Data quality report identifies invalid runs.
[ ] Same-seed repeated runs are grouped.
[ ] Final hash mismatches are detected.
[ ] Earliest divergence tick is reported when possible.
[ ] Observability ON/OFF side effects can be detected.
```

---

# Milestone 52 — Cross-Run Pattern Mining Engine

## Goal

Find repeated behavior patterns across many runs.

This is the heart of Phase 9.

---

## Components

```text
PatternMiningEngine
OutlierDetector
FailureClusterer
RecurringAnomalyMiner
SeedOutlierAnalyzer
TemporalPatternMiner
DomainPatternMiner
```

---

# Mining logic types

## 1. Outlier detection

Find runs that are unusual.

Examples:

```text
lowest health score
highest anomaly count
highest memory
highest tick p95
earliest hard law violation
most quest stalls
most stuck entities
```

Output:

```text
outlier_runs.json
```

---

## 2. Recurring anomaly mining

Find patterns that appear across many runs.

Example:

```text
NavigationStuck appears in 72/100 runs.
ResourceProductionZero appears in 41/100 runs.
QuestStalled appears in only 2/100 runs.
```

Output:

```text
recurring_anomalies.json
```

---

## 3. Domain clustering

Group issues by subsystem:

```text
movement
economy
quest
combat
runtime
strategy
faction
```

Example:

```text
movement-related issues dominate 65% of failing runs
economy-related issues dominate 30%
quest issues are rare
```

Output:

```text
domain_cluster_report.json
```

---

## 4. Temporal clustering

Find when issues happen.

Example:

```text
economy freeze usually starts between tick 18000 and 22000
governor degradation starts after tick 50000
hard law violation occurs immediately after resource depletion
```

Output:

```text
temporal_patterns.json
```

---

## 5. Entity/resource/quest hotspot mining

Find repeated hotspots.

Examples:

```text
resource_node_91 appears in 29 failed runs
region_forest_3 appears in 44 movement failures
quest_chain_blacksmith appears in 12 stalls
faction_red collapses in 80% of combat runs
```

Output:

```text
hotspot_report.json
```

---

## 6. Cross-signal correlation

Look for signals that appear together.

Example:

```text
ResourceProductionZero often appears with:
- high NavigationStuck
- high inventory_full_ratio
- many depleted node targets
```

This helps root-cause investigation.

Output:

```text
cross_signal_correlations.json
```

---

## Avoid overengineering

Use simple statistical logic first:

```text
counts
percentages
percentiles
thresholds
co-occurrence
z-score optional
IQR optional
```

Do not start with ML clustering.

---

## Acceptance criteria

```text
[ ] Worst runs are identified.
[ ] Recurring anomalies are ranked.
[ ] Domain clusters are generated.
[ ] Temporal issue windows are detected.
[ ] Hotspots are detected.
[ ] Correlated signals are reported.
```

---

# Milestone 53 — Priority Scoring and Investigation Backlog

## Goal

Turn mined patterns into an engineering priority list.

The output should not be:

```text
Here are 500 anomalies.
```

The output should be:

```text
Start with these 10 investigation items.
```

---

## Components

```text
InvestigationCandidate
PriorityScorer
EngineeringBacklogGenerator
BacklogItem
PriorityPolicy
```

---

## Candidate categories

```text
determinism_failure
hard_law_failure
liveness_failure
balance_issue
performance_regression
observability_quality_issue
data_quality_issue
interesting_story
```

---

## Priority levels

```text
P0 — correctness/determinism/corruption
P1 — repeated liveness failure or major collapse
P2 — strong balance issue across many seeds
P3 — rare issue or weak evidence
P4 — interesting behavior, not urgent
```

---

## Priority scoring factors

| Factor          | Meaning                       |
| --------------- | ----------------------------- |
| Severity        | Critical issue beats warning  |
| Frequency       | Appears across many runs      |
| Reproducibility | Same seed reproduces          |
| Blast radius    | Affects many entities/systems |
| Confidence      | Evidence quality              |
| Actionability   | Clear subsystem to inspect    |
| Regression      | Worse than baseline           |
| Runtime impact  | Performance/memory cost       |

---

## Example output

```text
P1 — Resource economy freeze after tick ~20,000

Affected:
- 37/100 runs
- seeds: 4, 9, 12, 18, ...
- common tick window: 18,000–23,000

Evidence:
- resource_produced_count becomes zero
- active workers remain >300
- many workers target depleted nodes
- NavigationStuck increases before freeze

Likely subsystem:
- resource scorer
- depleted node invalidation
- worker target reselection

Suggested first debugging step:
- inspect resource target selection after node depletion

Best reproduction seed:
- seed 18
```

---

## Outputs

```text
engineering_backlog.json
engineering_backlog.md
priority_summary.json
```

---

## Acceptance criteria

```text
[ ] Issues are ranked.
[ ] Each issue has evidence.
[ ] Each issue has affected runs/seeds.
[ ] Each issue has suggested first debugging step.
[ ] P0/P1 issues appear at top.
```

---

# Milestone 54 — Evidence Pack Builder

## Goal

Create compact packages for AI Agent and engineers.

The AI Agent should not read everything. It should read curated evidence packs.

---

## Components

```text
EvidencePackBuilder
EvidenceSelector
TimelineSliceExtractor
MetricWindowExtractor
EventSliceExtractor
ReproductionCommandBuilder
```

---

## Evidence pack layout

```text
data/mining_experiments/<experiment_id>/evidence_packs/<candidate_id>/
  evidence_pack.json
  evidence_summary.md
  affected_runs.json
  affected_seeds.txt
  metric_windows_excerpt.jsonl
  events_excerpt.jsonl
  anomalies_excerpt.json
  timelines_excerpt.json
  reproduction_commands.md
```

---

## Evidence pack fields

```text
candidate_id
priority
title
category
affected_runs
affected_seeds
tick_ranges
affected_entities
affected_resources
affected_quests
affected_regions
supporting_metrics
supporting_events
supporting_anomalies
suspected_subsystems
confidence
missing_data
reproduction_commands
```

---

## Evidence selection logic

Include:

```text
top 3 worst runs
top 3 representative runs
earliest failing run
best reproduction seed
metric windows around failure
events before and after failure
entity timeline snippets
anomaly cluster summary
```

Avoid including:

```text
all events
all metric windows
all timelines
huge raw files
```

---

## Acceptance criteria

```text
[ ] Each backlog item can produce evidence pack.
[ ] Evidence pack is compact enough for AI review.
[ ] Evidence pack includes reproduction command.
[ ] Evidence pack includes missing data notes.
[ ] Evidence pack links back to full artifacts.
```

---

# Milestone 55 — AI Agent Investigation Orchestrator

## Goal

Use an AI Agent to analyze evidence packs and produce investigation recommendations.

The AI Agent should be constrained, evidence-based, and repeatable.

---

## Components

```text
AIAgentInvestigationRunner
AgentPromptTemplateRegistry
AgentInputPack
AgentOutputValidator
AgentFindingParser
AgentReportMerger
```

---

## Agent tools

The Agent should conceptually have access to these tools:

| Tool                      | Purpose                          |
| ------------------------- | -------------------------------- |
| `ArtifactReaderTool`      | read selected artifacts          |
| `DuckDBQueryTool`         | run predefined dataset queries   |
| `EvidencePackReaderTool`  | inspect candidate evidence       |
| `MetricWindowQueryTool`   | query tick windows               |
| `EventSliceQueryTool`     | inspect event sequences          |
| `TimelineQueryTool`       | inspect entity timeline snippets |
| `BaselineComparisonTool`  | compare to baseline              |
| `ReproductionCommandTool` | produce reproduction command     |
| `BacklogWriterTool`       | write structured findings        |
| `ReviewReaderTool`        | read human labels/reviews        |

Keep these as internal abstractions first.

Do not need a full autonomous agent platform on day one.

---

## Agent workflow

```text
1. Read experiment summary.
2. Read data quality report.
3. Read determinism audit.
4. Read priority backlog candidates.
5. For each P0/P1/P2 candidate:
   - read evidence pack
   - verify evidence
   - classify issue
   - suggest likely subsystem
   - suggest first debugging step
   - suggest missing instrumentation
6. Produce final investigation report.
```

---

## Agent output format

The Agent must output structured data:

```text
agent_investigation_report.md
agent_findings.json
agent_backlog_updates.json
missing_instrumentation.json
next_experiment_suggestions.json
```

---

## Required Agent rules

The Agent must follow:

```text
No evidence, no claim.
Do not invent metrics.
Do not invent files.
Do not claim root cause as fact.
Separate likely cause from confirmed cause.
List missing data.
Prefer reproducible issues.
Prefer P0/P1 issues.
```

---

## Agent finding fields

```text
finding_id
candidate_id
priority
verdict
category
confidence
evidence_used
likely_subsystems
recommended_first_step
recommended_reproduction
missing_data
agent_notes
```

---

## Output validation

Use `AgentOutputValidator`.

Check:

```text
[ ] Required fields exist.
[ ] Every major claim references evidence.
[ ] Priority is valid.
[ ] Confidence is valid.
[ ] Candidate ID exists.
[ ] No unsupported category.
```

If validation fails:

```text
mark agent output invalid
do not promote into backlog
```

---

## Acceptance criteria

```text
[ ] Agent can analyze one evidence pack.
[ ] Agent can analyze full experiment summary.
[ ] Agent output is structured.
[ ] Invalid agent output is rejected.
[ ] Agent recommendations are traceable to evidence.
```

---

# Milestone 56 — Next Instrumentation and Experiment Recommender

## Goal

Use mining results to decide what data or experiments are needed next.

Often the first large experiment will reveal:

```text
we do not have enough data to explain root cause
```

That is still useful.

---

## Components

```text
InstrumentationGapDetector
NextExperimentRecommender
SignalCoverageAnalyzer
RuleImprovementRecommender
```

---

## Missing data categories

```text
missing event type
missing metric
missing entity timeline field
missing scenario expectation
missing root-cause evidence
missing baseline
missing review labels
missing reproduction command
```

---

## Example output

```text
Issue:
ResourceProductionZero

Missing data:
- worker current target reason
- resource node depletion tick
- inventory full duration by entity
- shop/storage transaction rejection reason

Recommended instrumentation:
- emit ResourceTargetSelected event
- record target score breakdown
- add inventory_full_ticks metric
- add depleted_node_target_count metric
```

---

## Next experiment suggestions

Examples:

```text
rerun seed 18 with DEBUG observability
rerun RESOURCE_ECONOMY_1000 with resource decision tracing enabled
run same-seed repeat for seed 18
compare old resource scorer vs new scorer
run mutation: reduce resource node count by 20%
```

---

## Acceptance criteria

```text
[ ] Missing signals are listed.
[ ] Suggested instrumentation is tied to issues.
[ ] Next experiment suggestions are concrete.
[ ] Recommendations avoid broad vague advice.
```

---

# Milestone 57 — Phase 9 Review Workflow and Quality Gate

## Goal

Make Phase 9 results usable by engineers.

The output should become actionable work, not just analysis.

---

## Components

```text
MiningReviewWorkflow
BacklogReviewStore
IssuePromotionPolicy
MiningQualityGate
```

---

## Review labels

For each AI/mining finding:

```text
ACCEPTED_FOR_INVESTIGATION
CONFIRMED_BUG
BALANCE_ISSUE
FALSE_POSITIVE
EXPECTED_BEHAVIOR
NEEDS_MORE_DATA
DUPLICATE
LOW_PRIORITY
```

---

## Promotion logic

Only promote to engineering backlog when:

```text
priority is P0/P1
or repeated P2 across many runs
or human review accepts it
or hard law/determinism failure exists
```

---

## Mining quality gate

Use in CI or long-run validation.

Gate examples:

```text
FAIL if deterministic mismatch exists
FAIL if hard law violation appears
FAIL if P0 issue exists
WARNING if P1 liveness issue appears in >10% runs
WARNING if baseline drift detected
PASS if no P0/P1 and data quality valid
```

---

## Outputs

```text
mining_quality_gate.json
reviewed_engineering_backlog.md
reviewed_engineering_backlog.json
```

---

## Acceptance criteria

```text
[ ] Engineers can review findings.
[ ] Accepted findings become backlog items.
[ ] False positives are recorded.
[ ] Mining gate can fail on P0.
[ ] Mining gate can warn on recurring P1/P2.
```

---

# Phase 9 End-to-End Flow

Final intended flow:

```text
1. Define mining experiment.
2. Generate run matrix.
3. Run hundreds of simulations.
4. Produce normal observability artifacts per run.
5. Build mining dataset.
6. Run data quality audit.
7. Run determinism audit.
8. Extract run features.
9. Mine cross-run patterns.
10. Rank investigation candidates.
11. Build evidence packs.
12. AI Agent investigates evidence packs.
13. Validate AI output.
14. Generate engineering backlog.
15. Recommend missing instrumentation.
16. Recommend next experiment.
17. Engineers review findings.
18. Accepted findings become implementation/debugging tasks.
```

---

# Minimum viable Phase 9

Do not build everything at once.

The first useful version only needs:

```text
MiningExperimentController
MiningDatasetBuilder
DataQualityAuditor
DeterminismAuditor
PatternMiningEngine
PriorityScorer
EvidencePackBuilder
AI Agent prompt runner
EngineeringBacklogGenerator
```

Minimum outputs:

```text
data_quality_report.md
determinism_audit.md
pattern_mining_report.md
engineering_backlog.md
evidence_packs/
agent_investigation_report.md
next_instrumentation.md
```

This is enough to start.

---

# Required CLI commands

Add these:

```text
rpg-observe mining run <experiment_config>
rpg-observe mining build-dataset <experiment_id>
rpg-observe mining audit-data <experiment_id>
rpg-observe mining audit-determinism <experiment_id>
rpg-observe mining find-patterns <experiment_id>
rpg-observe mining rank <experiment_id>
rpg-observe mining build-evidence <experiment_id>
rpg-observe mining investigate-ai <experiment_id>
rpg-observe mining recommend-next <experiment_id>
rpg-observe mining gate <experiment_id>
```

Keep the CLI thin. It should call services, not contain logic.

---

# Required reports

Phase 9 should generate:

```text
experiment_summary.md
data_quality_report.md
determinism_audit.md
pattern_mining_report.md
priority_backlog.md
agent_investigation_report.md
missing_instrumentation_report.md
next_experiment_report.md
mining_quality_gate.md
```

JSON versions should also exist for automation.

---

# Required tests

## Unit tests

```text
test_mining_experiment_config.py
test_mining_dataset_builder.py
test_data_quality_auditor.py
test_determinism_auditor.py
test_pattern_mining_engine.py
test_priority_scorer.py
test_evidence_pack_builder.py
test_agent_output_validator.py
test_next_instrumentation_recommender.py
```

## Integration tests

```text
test_mining_experiment_flow.py
test_mining_dataset_flow.py
test_same_seed_determinism_flow.py
test_multi_seed_pattern_mining_flow.py
test_ai_investigation_pack_flow.py
test_mining_quality_gate_flow.py
```

## Performance tests

```text
test_large_experiment_dataset_build.py
test_pattern_mining_runtime.py
test_evidence_pack_size_limit.py
```

---

# Phase 9 performance rules

```text
[ ] Mining never runs inside engine tick path.
[ ] AI Agent never touches live engine state.
[ ] Dataset builder can stream large JSONL files.
[ ] Evidence packs are compact.
[ ] Pattern mining uses summarized tables first.
[ ] Full event scan is only used when needed.
[ ] Same-seed determinism analysis is separated from multi-seed balance mining.
```

---

# Phase 9 AI safety rules for engineering correctness

The AI Agent must not be allowed to:

```text
invent root cause
invent missing metrics
modify simulation code directly
promote unsupported findings
ignore data quality failures
claim certainty from weak evidence
```

The AI Agent can:

```text
summarize evidence
rank likely causes
suggest files/systems to inspect
suggest missing instrumentation
suggest next experiments
generate debugging playbooks
draft engineering backlog items
```

---

# Final acceptance criteria

Phase 9 is complete when:

```text
[ ] Large mining experiment can be defined.
[ ] Hundreds of run artifacts can be indexed.
[ ] Mining dataset can be built.
[ ] Data quality audit works.
[ ] Same-seed determinism audit works.
[ ] Multi-seed pattern mining works.
[ ] Outlier seeds are identified.
[ ] Recurring failures are clustered.
[ ] Engineering priorities are ranked.
[ ] Evidence packs are generated.
[ ] AI Agent can analyze evidence packs.
[ ] AI output is validated.
[ ] Missing instrumentation is recommended.
[ ] Next experiments are recommended.
[ ] Human review can accept/reject findings.
[ ] Mining quality gate can pass/warn/fail.
```

---

# My strong recommendation

Phase 9 should be treated as the bridge between:

```text
observability system
```

and:

```text
engineering decision system
```

The Observatory tells you:

```text
what happened
```

Phase 9 tells you:

```text
where to start
why it matters
what evidence supports it
what to run next
what data is missing
```

That is exactly what you need after running hundreds of long simulations.
