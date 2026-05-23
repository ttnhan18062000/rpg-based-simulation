Got it. I reviewed it as the **whole Observatory feature from Phase 1 → Phase 9**, not only Phase 9.

# Overall verdict

The implementation is a **wide Observatory scaffold**, but it is **not yet a complete or trustworthy implementation** of the full Phase 1–9 plan.

It has many good components already:

```text
/metrics exporter
Loki/Promtail config
SimulationEvent model
EventRecorder
EntityTimelineStore
HardLawMonitor
MetricWindowRecorder
AnalysisPipeline
RuleEngine
RunReportGenerator
Live status/snapshot/entity APIs
WebSocket event stream
Warehouse/export adapters
DuckDB/Parquet path
Domain analyzers
Expectation pack framework
Story/review/quality modules
Phase 9 mining pipeline
```

But the major problem is:

```text
many components exist,
but several critical flows are incomplete, inconsistent, synthetic, or not connected to real long-run artifacts.
```

I also extracted and ran the uploaded code/tests locally:

```text
compileall: passed

observability unit/integration subset:
309 passed
8 failed
8 skipped

extra metrics/live/perf tests:
10 passed

hard-law/parity tests:
4 passed
```

The failures are not random. They point to real gaps: missing expectation packs, Parquet/pyarrow handling, scenario-level gate inconsistency, and expectation-pack integration.

---

# Phase-by-phase review

## Phase 1 — Prometheus, Loki, Grafana foundation

Status:

```text
PARTIAL
```

### Implemented

The code has a `/metrics` path and Prometheus collector support. The dashboard and docker stack are also present. The original feasibility roadmap required `/metrics`, Loki label hardening, and core P0 telemetry as the first execution step.

### Problems

The Grafana dashboard expects many metrics that do not appear to be fully exported, such as:

```text
sim_world_difficulty_mult
sim_faction_population
sim_entity_level_distribution
sim_items_crafted_total
sim_shop_transactions_total
sim_combat_events_total
sim_skill_events_total
sim_redis_latency_seconds_bucket
sim_kafka_publish_seconds_bucket
sim_worker_health
sim_invalid_actions_total
```

The dashboard is ahead of the actual exporter. That means Grafana can show many “No data” panels even though `/metrics` exists. The exported dashboard config includes these queries.

### Incorrect / missing

```text
[ ] Dashboard must be aligned with actually exported metrics.
[ ] Missing metric panels should be removed, hidden, or moved to “future”.
[ ] Add a test that scrapes /metrics and verifies every dashboard PromQL query has data or is explicitly optional.
```

---

## Phase 2 — SimulationEvent, EventRecorder, timeline, parity

Status:

```text
PARTIAL-GOOD
```

### Implemented

The code has:

```text
SimulationEvent
CombatDamageEvent
CombatKillEvent
GoldTransactionEvent
QuestEvent
MovementEvent
LifecycleEvent
EventExtractor
EntityTimelineStore
```

The kernel calls `_phase_observability()` after hard-law checks and state advancement, which is the correct architectural boundary: observe after committed state, not during decision mutation.

### Problems

The planned event taxonomy used stable semantic names like:

```text
EntityKilled
QuestStarted
QuestCompleted
ResourceNodeDepleted
GovernorModeChanged
InvariantViolation
NavigationStuck
```

But implementation currently uses lower-level names:

```text
combat_damage
combat_kill
gold_transaction
quest_event
movement
lifecycle
```

The event model and extractor show these lower-level event types.

That is not fatal, but it creates drift. Rules, reports, mining, and AI investigation may expect semantic names while the recorder emits technical names.

### Incorrect / missing

```text
[ ] Standardize event taxonomy.
[ ] Keep low-level event_type only inside payload or subtype.
[ ] Add canonical event_type names.
[ ] Add taxonomy compatibility tests.
```

Recommended mapping:

| Current                             | Better canonical event                   |
| ----------------------------------- | ---------------------------------------- |
| `combat_kill`                       | `EntityKilled`                           |
| `quest_event` with completed status | `QuestCompleted`                         |
| `gold_transaction` from quest       | `QuestRewardDelivered`                   |
| `movement` with stuck/failure       | `NavigationStuck` or `MovementAttempted` |
| `lifecycle` despawn                 | `EntityDespawned`                        |

---

## Phase 3 — Single-run artifact pipeline, rules, report

Status:

```text
PARTIAL
```

### Implemented

The code has a proper `RunManifest` and `RunArtifactRepository` with standard files:

```text
run_manifest.json
simulation_events.jsonl
hard_law_violations.jsonl
anomalies.json
run_report.json
run_report.md
```

This matches the right architecture for local single-run analysis.

It also has:

```text
MetricWindowRecorder
AnalysisPipeline
RuleEngine
RunReportGenerator
EvidenceBuilder
Triage/report logic
```

### Major problems

## 1. Hard-law artifact mismatch

`RunArtifactRepository` standardizes this:

```text
hard_law_violations.jsonl
```

But the Phase 9 dataset builder reads this:

```text
hard_law_violations.json
```

That means hard-law violations can be silently lost during later mining.

## 2. HardLawMonitor does not appear to persist violations to artifact JSONL

The kernel records violations into runtime status and routes alerts, but the reviewed path does not clearly write every violation to `hard_law_violations.jsonl`.

That breaks the post-run pipeline, because Phase 3 and Phase 9 depend on artifact truth, not only live status.

## 3. Rule semantics are too weak

The biggest example is `ResourceProductionZero`.

It appears to use `gold_total_avg == 0` as a proxy for resource production. That is incorrect.

Resource production needs its own signal:

```text
resource_produced_count
resource_production_rate
harvest_success_count
resource_node_depletion_count
active_harvester_count
```

Gold is not resource production.

### Incorrect / missing

```text
[ ] Persist hard-law violations to hard_law_violations.jsonl.
[ ] Standardize .jsonl vs .json artifact naming.
[ ] Fix ResourceProductionZero to use real production metrics.
[ ] Add artifact schema contract tests.
[ ] Add end-to-end run test: real kernel run -> artifacts -> analysis -> report.
```

---

## Phase 4 — Multi-run sweeps, baseline, comparison, CI gate

Status:

```text
PARTIAL
```

### Implemented

The code has sweep/baseline/comparator/report/gate modules and CLI hooks.

### Problems

The scenario-level gate test currently fails: expected `PASS`, got `WARNING`.

That means the CI gate behavior is not stable enough yet.

Also, the baseline/comparison system depends on correct run summaries, but the artifact schema is inconsistent. For example:

```text
run_report.json may store health_score under metadata
mining/baseline code may expect top-level health_score
```

This can cause false baseline results.

### Incorrect / missing

```text
[ ] Define one stable run_report.json schema.
[ ] Make all consumers read the same schema.
[ ] Fix CI gate expected status.
[ ] Add tests for baseline comparison from real run_report.json, not synthetic reports.
```

---

## Phase 5 — Live Observatory

Status:

```text
MVP MOSTLY WORKING
```

### Implemented well

The tests cover:

```text
live status endpoint
live snapshot endpoint
live entity inspection
live health endpoint
WebSocket event stream
subscription validation
subscriber limit
heartbeat
live anomaly counters
```

The WebSocket and live worker tests show useful implementation coverage.

### Problems

The test endpoint:

```text
/api/v1/test/publish_event
```

is useful for testing, but it must not be enabled in production.

Also, live status/entity/snapshot endpoints need stronger limits:

```text
max timeline size
max response payload
rate limit
read-only guarantee
no full-world scan
```

### Incorrect / missing

```text
[ ] Hide /api/v1/test/publish_event outside test/debug profile.
[ ] Add payload-size tests for entity inspection.
[ ] Add no-full-world-scan performance test.
[ ] Add read-only/mutation safety tests.
```

---

## Phase 6 — Export, DuckDB/Parquet, stream abstraction, worker, history, retention

Status:

```text
PARTIAL + OVER-EAGER
```

### Implemented

The code includes:

```text
ArtifactExporter
ExportManager
ParquetArtifactExporter
AnalyticsDatasetBuilder
DuckDBQueryService
EventStreamAdapter
RedisStreamAdapter
ExternalAnomalyWorker
Historical query API
Retention manager
Deployment profiles
```

The stream abstraction is the right direction because the engine should depend on `EventStreamAdapter`, not Redis/Kafka directly.

### Problems

## 1. Parquet export fails when pyarrow is missing

Tests failed because CLI export expected success but Parquet export failed without `pyarrow`.

Correct behavior should be one of:

```text
install pyarrow as required dependency
or fallback to JSON
or skip Parquet with clear message
```

Not fail unexpectedly.

## 2. Raw SQL access is too open

The dataset query service supports raw SQL in tests. That is okay internally, but public CLI/API should use named queries only:

```text
worst-runs
anomaly-summary
metric-trend
entity-events
```

## 3. External services enabled too early

The compose stack includes Redis, RabbitMQ, Kafka, Zookeeper, Loki, Promtail, Prometheus, Grafana, backend, frontend, worker, watchdog. That is too heavy for default Observatory operation.

### Incorrect / missing

```text
[ ] Make Parquet optional or install pyarrow.
[ ] Restrict raw SQL to internal/dev mode.
[ ] Add named query-only CLI/API path.
[ ] Split docker-compose into profiles: local, ci, long_run_lab, streaming, warehouse, full_stack.
```

---

## Phase 7 — Production platform

Status:

```text
SCAFFOLD ONLY
```

### Implemented

There are adapters and tests for:

```text
ClickHouse dry-run
Redis stream adapter
Redis stream consumer
Live anomaly worker
Alert router
Production readiness reporting
```

### Critical problem

`docker-compose.yml` still references invalid active V2 modules:

```text
python -m src.workers.ai_worker_daemon
python -m src.utils.watchdog
```

Earlier architecture analysis already identified these paths as legacy/non-active V2 paths. The V2 watchdog should be `src/observability/watchdog.py` or an equivalent new V2 module.

### Incorrect / missing

```text
[ ] Remove invalid ai_worker/watchdog services from default compose.
[ ] Replace with real V2 worker/watchdog modules.
[ ] Add compose boot test.
[ ] Make Redis/Kafka/ClickHouse optional profile services.
[ ] Do not call this production-ready yet.
```

---

## Phase 8 — Advanced simulation understanding

Status:

```text
PARTIAL / FAILING TESTS
```

### Implemented

The code has:

```text
UnderstandingPipeline
DomainAnalyzerRegistry
MovementDomainAnalyzer
EconomyDomainAnalyzer
QuestDomainAnalyzer
RuntimeDomainAnalyzer
ExpectationPackLoader
RootCauseEngine
BalanceDiagnosisEngine
StoryDetector
ReviewStore
AnalyzerQualityReporter
BaselineEvolutionPolicy
```

The pipeline structure is good and explicitly post-run only.

### Critical problem

Expectation packs are missing:

```text
resource_economy.json
combat_heavy.json
peaceful_village.json
```

The loader falls back to the default `mixed_sandbox` pack, so tests expecting scenario-specific packs fail. The tests explicitly expect those packs.

### Additional concern

Some Phase 8 logic uses synthetic event names like:

```text
gold_transaction
quest_event
```

which reinforces the event taxonomy drift. Story and domain analyzer tests use those lower-level names.

### Incorrect / missing

```text
[ ] Add expectation packs for resource_economy, combat_heavy, mixed_sandbox, peaceful_village.
[ ] Ensure each pack has enough hard/warning/domain expectations.
[ ] Stop silently falling back when a known scenario pack is missing.
[ ] Align expectation packs with canonical event taxonomy.
```

---

## Phase 9 — Simulation mining and AI-assisted investigation

Status:

```text
PROTOTYPE
```

### Implemented

The code has:

```text
MiningExperimentConfig
MiningRunMatrixBuilder
MiningExperimentController
MiningDatasetBuilder
DataCompletenessAuditor
DeterminismAuditor
PatternMiningEngine
EngineeringBacklogGenerator
EvidencePackBuilder
AIAgentInvestigationRunner
NextExperimentRecommender
MiningQualityGate
```

The tests cover matrix generation, dataset building, querying, data completeness, determinism, and mining reports.

### Critical problems

## 1. Invalid observability mode mapping

The controller maps:

```text
production -> ObservabilityMode.PRODUCTION or ObservabilityMode.FULL
full       -> ObservabilityMode.FULL
none       -> ObservabilityMode.NONE
```

But the real enum uses:

```text
OFF
LIGHT
DEBUG
CERTIFICATION
LONG_RUN
```

This can crash execution.

Correct mapping:

```text
production -> LONG_RUN
full       -> DEBUG or LONG_RUN
light      -> LIGHT
none       -> OFF
cert       -> CERTIFICATION
```

## 2. Mining dataset is too small

Current builder creates mainly:

```text
runs
run_features
anomalies
hard_law_violations
```

It does not yet build the intended richer mining dataset:

```text
metric_windows
simulation_events
findings
reviews
entity_timeline_samples
seed_features
```

The builder code confirms the smaller table set.

## 3. Determinism auditor can falsely pass

If final hashes are missing, same-seed repeated runs should produce:

```text
INSUFFICIENT_DATA
```

not:

```text
DETERMINISTIC
```

Current logic is too weak because “no mismatch found” is not the same as “deterministic.”

## 4. AI Agent runner is not real AI-assisted investigation yet

It appears to behave like a heuristic stub. That is okay for scaffolding, but it should be named honestly or replaced with a real evidence-pack-driven AI integration.

### Incorrect / missing

```text
[ ] Fix ObservabilityMode mapping.
[ ] Build full mining dataset tables.
[ ] Fix determinism missing-hash behavior.
[ ] Make evidence packs candidate-type aware.
[ ] Make AI investigation evidence-validated.
[ ] Do not promote AI output unless evidence references validate.
```

---

# Cross-phase critical issues

## P0 — Must fix before long-run use

| Issue                                        | Why it matters                                   |
| -------------------------------------------- | ------------------------------------------------ |
| Invalid `ObservabilityMode` mapping          | Phase 9 experiment execution can crash           |
| Docker compose references missing V2 modules | Production/lab stack may fail to boot            |
| Determinism auditor can falsely pass         | Can hide race/nondeterminism bugs                |
| Artifact schema mismatch                     | Later phases mine wrong or missing data          |
| Hard-law violations not reliably persisted   | Post-run analysis can miss critical law failures |

---

## P1 — Must fix before calling feature complete

| Issue                                      | Why it matters                                    |
| ------------------------------------------ | ------------------------------------------------- |
| Missing expectation packs                  | Phase 8 scenario understanding fails              |
| Dashboard/exporter mismatch                | Grafana can show false “No data”                  |
| `ResourceProductionZero` uses wrong signal | Economy analysis can be wrong                     |
| Parquet CLI fails when pyarrow missing     | Export flow not robust                            |
| Event taxonomy inconsistent                | Rules/mining/AI may miss signals                  |
| AI investigation is stub-level             | Not yet true AI-assisted analysis                 |
| Test data too synthetic                    | Passing tests do not prove real long-run behavior |

---

## P2 — Important hardening

| Issue                                    | Why it matters                 |
| ---------------------------------------- | ------------------------------ |
| Per-event file flushing                  | Long-run IO overhead risk      |
| Raw SQL query access                     | Unsafe for public/dev API      |
| External infra enabled too early         | Operational complexity         |
| Review workflow needs append-only ledger | Auditability                   |
| Quality gate ignores data quality        | Can pass bad experiment data   |
| Pattern mining too shallow               | Weak root-cause prioritization |

---

# Biggest schema problems

These must be standardized.

## 1. Hard-law artifact name

Current repository:

```text
hard_law_violations.jsonl
```

Mining builder:

```text
hard_law_violations.json
```

Fix:

```text
Use hard_law_violations.jsonl everywhere.
```

## 2. Anomaly rule field

Some places use:

```text
rule_name
```

Others expect:

```text
rule_id
```

Fix:

```text
Canonical field = rule_id
Legacy alias = rule_name
Writer should emit both temporarily or migration should normalize.
```

## 3. Run report health score location

Some code expects:

```text
health_score
```

Others write/read:

```text
metadata.health_score
```

Fix:

```text
Define run_report_v1 schema.
All readers must use the same location.
```

## 4. Metric window tick fields

Metric windows use:

```text
window_start_tick
window_end_tick
```

Evidence/mining code should not expect:

```text
tick
```

Fix:

```text
Slice metric windows by window_start_tick/window_end_tick.
```

---

# Test suite assessment

## Good coverage

The tests cover many modules:

```text
live API
WebSocket
health counters
rule engine
analysis pipeline
warehouse
stream adapters
domain analyzers
story detector
review store
Phase 9 mining
```

That is good breadth.

## Weakness

Many tests use:

```text
synthetic JSON
mocked warehouse
mocked pipeline
mocked ClickHouse
manual fake events
test-only publish endpoint
```

That is okay for unit tests, but not enough for the whole Observatory.

Missing are more “real flow” tests:

```text
real Kernel run
real artifacts
real analysis pipeline
real report
real mining dataset
real evidence pack
real quality gate
```

---

# Missing tests to add

## P0 tests

```text
test_observability_mode_mapping_uses_real_enum_values
test_compose_services_reference_existing_modules
test_hard_law_violation_persisted_to_jsonl
test_artifact_schema_contract_all_readers_match_writers
test_same_seed_missing_hash_is_insufficient_data
test_same_seed_hash_mismatch_is_p0
test_dashboard_queries_match_exported_metrics
```

## P1 tests

```text
test_expectation_packs_exist_for_core_scenarios
test_resource_production_zero_requires_resource_metric
test_mining_dataset_includes_metric_windows
test_mining_dataset_includes_simulation_events
test_anomaly_rule_id_normalization
test_run_report_schema_contract
test_parquet_export_fallback_without_pyarrow
test_ai_output_rejects_missing_evidence_reference
```

## P2 tests

```text
test_event_taxonomy_canonical_names
test_event_recorder_buffered_flush_policy
test_live_api_payload_size_limit
test_raw_sql_disabled_in_public_query_path
test_review_store_append_only
test_quality_gate_fails_on_invalid_data_quality
```

---

# Recommended fix order

Do not add new features first.

Fix in this order:

```text
1. Fix ObservabilityMode mapping.
2. Fix docker-compose invalid module paths / split profiles.
3. Add missing expectation packs.
4. Standardize artifact schemas.
5. Persist hard-law violations to JSONL.
6. Fix determinism auditor missing-hash false pass.
7. Align dashboard metrics with exporter.
8. Fix ResourceProductionZero signal.
9. Expand mining dataset tables.
10. Replace or rename AI investigation stub.
11. Strengthen data quality and quality gate.
12. Add real end-to-end Observatory tests.
```

---

# Final assessment

The whole Observatory feature is **not complete yet**.

Current state:

```text
Phase 1: partial
Phase 2: partial-good
Phase 3: partial
Phase 4: partial
Phase 5: MVP mostly working
Phase 6: partial / over-eager
Phase 7: scaffold only
Phase 8: partial / failing packs
Phase 9: prototype
```

Best description:

```text
The Observatory architecture has been broadly scaffolded,
but the implementation is not yet reliable enough for hundreds of long-run simulations.
```

The next engineering move should be:

```text
hardening + schema alignment + real-flow validation
```

not adding more observability features.
