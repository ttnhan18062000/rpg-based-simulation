---
status: archive
authority: P2
audience: historical
layer: engine
original_date: unknown
---

# Phase 6 Implementation Plan — Externalization and Scale Readiness

Phase 6 should introduce **externalization points**, but still avoid building a heavy production platform too early.

The goal is not:

> Add Kafka, ClickHouse, Redis, DuckDB, and a complex observability cluster immediately.

The goal is:

> Make the Observatory capable of scaling out later, while keeping the current implementation simple and safe.

The previous feasibility report already recommends staged delivery instead of jumping directly to an out-of-process Redis/Kafka daemon too early. It also confirms the current V2 runtime does not have a standalone worker daemon and should first build around FastAPI / `V2EngineManager` / local artifacts.

---

# Phase 6 Goal

## Main objective

Create clean extension points for:

```text
historical data storage
external event streaming
external anomaly processing
retention management
querying old runs
deployment profiles
```

But implement only the simplest working versions first.

---

# Phase 6 Should Include

```text
1. Storage export abstraction
2. Parquet / DuckDB local analytics path
3. Event stream adapter interface
4. Optional Redis Streams adapter, not mandatory
5. External anomaly worker V1
6. Historical run query API
7. Retention and cleanup policy
8. Deployment profiles
9. Scale validation tests
```

---

# Phase 6 Should Not Include Yet

```text
1. Full Kafka platform
2. ClickHouse production warehouse
3. Complex distributed worker orchestration
4. Multi-user access control
5. Full observability UI
6. ML anomaly scoring
7. Automatic game balancing
8. Auto-remediation inside live simulation
```

---

# Core Principle

Keep the default stack simple:

```text
default local mode:
  JSONL artifacts
  JSON reports
  Markdown reports
  Prometheus
  Loki
  in-process live publisher
```

Add optional scale path:

```text
optional analysis mode:
  Parquet export
  DuckDB queries
  external analyzer process
```

Add future live streaming path:

```text
optional live scale mode:
  Redis Streams or NATS adapter
```

---

# Phase 6 Milestones

```text
Milestone 27 — Storage Export Layer
Milestone 28 — DuckDB / Parquet Local Analytics
Milestone 29 — Event Stream Adapter Interface
Milestone 30 — External Anomaly Worker V1
Milestone 31 — Historical Query API
Milestone 32 — Retention and Data Lifecycle Policy
Milestone 33 — Deployment Profiles and Scale Validation
```

---

# Milestone 27 — Storage Export Layer

## Goal

Create a storage abstraction that can export Observatory artifacts into other formats without changing the engine or analyzer logic.

Phase 3 and Phase 4 created local artifacts like:

```text
simulation_events.jsonl
metric_windows.jsonl
hard_law_violations.jsonl
anomalies.json
run_report.json
run_report.md
baseline.json
sweep_report.json
```

Milestone 27 adds a clean export layer.

---

## Why this matters

You will eventually want to move from:

```text
local JSONL files
```

to:

```text
Parquet
DuckDB
ClickHouse
S3
external warehouse
```

But the engine should not care.

The analyzer should not care.

Only the exporter should care.

---

## Components

```text
ArtifactExporter
ExportJob
ExportFormat
ExportManifest
ExportResult
ExportRegistry
```

---

## Supported formats in Phase 6

Start with:

```text
JSONL copy/export
Parquet export
CSV optional
```

Do not implement ClickHouse yet.

Do not implement S3 yet.

---

## Exportable data types

Start with core data only:

```text
simulation_events
metric_windows
anomalies
hard_law_violations
run_manifest
run_report_json
run_index
baseline
sweep_summary
```

---

## Target flow

```text
RunArtifactRepository
  -> ArtifactExporter
      -> exports selected artifacts
      -> writes export_manifest.json
      -> downstream tools read export output
```

---

## Tasks

### 27.1 Define export job model

Fields:

```text
export_id
source_run_id optional
source_sweep_id optional
source_path
output_path
format
artifact_types
created_at
status
errors
```

Checklist:

```text
[ ] Define export job model.
[ ] Support single-run export.
[ ] Support sweep export.
[ ] Support selected artifact types.
[ ] Reject unknown artifact types.
```

Acceptance:

```text
[ ] Export job can describe a single run export.
[ ] Export job can describe a sweep export.
```

---

### 27.2 Implement export registry

Checklist:

```text
[ ] Register exporter by format.
[ ] Register exporter by artifact type.
[ ] Reject unsupported format clearly.
[ ] Keep default JSONL exporter.
[ ] Add Parquet exporter placeholder if dependency missing.
```

Notes:

- Do not make Parquet mandatory at first.
- If `pyarrow` is not available, exporter should fail clearly or be skipped.

Acceptance:

```text
[ ] JSONL export works.
[ ] Unsupported format returns clear error.
[ ] Optional Parquet dependency is handled cleanly.
```

---

### 27.3 Implement export manifest

File:

```text
exports/<export_id>/export_manifest.json
```

Fields:

```text
export_id
source_run_id
source_sweep_id
format
artifact_types
output_files
record_counts
schema_version
created_at
status
```

Checklist:

```text
[ ] Manifest records exported files.
[ ] Manifest records record counts.
[ ] Manifest records schema version.
[ ] Manifest records skipped artifacts.
```

Acceptance:

```text
[ ] Export result can be inspected without opening every output file.
```

---

### 27.4 Add CLI command

Command:

```text
rpg-observe export <run_id> --format jsonl
rpg-observe export <run_id> --format parquet
rpg-observe export-sweep <sweep_id> --format parquet
```

Checklist:

```text
[ ] Export single run.
[ ] Export sweep.
[ ] Print export path.
[ ] Print record counts.
```

Acceptance:

```text
[ ] Developer can export a completed run.
[ ] Developer can export a sweep.
```

---

## Tests

Recommended tests:

```text
tests/unit/observability/test_artifact_exporter.py
tests/integration/observability/test_export_flow.py
```

Required checks:

```text
[ ] JSONL export works.
[ ] Export manifest is written.
[ ] Missing optional artifact is recorded as skipped.
[ ] Unsupported format fails clearly.
[ ] Sweep export includes multiple runs.
```

---

```

> [!NOTE]
> **Milestone 27 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `ExportJob` (Pydantic model for validation), `ExportManifest` (Pydantic model for record tracking), and `ArtifactExporter` hierarchy (`JSONLArtifactExporter` and `ParquetArtifactExporter`) implemented in `src/observability/analytics/exporter.py`.
> * **CLI Integration:** Accessible via `rpg-observe export <run_id> --format jsonl` and `rpg-observe export <run_id> --format parquet`.
> * **Resilience:** Integrates clean fallback mechanisms. Optional library pyarrow is dynamically loaded; if pyarrow or parquet dependencies are missing, the exporter raises a clear, descriptive `ImportError` or registers skipped artifacts rather than breaking system startup.
> * **Verification Tests:** Verified by `tests/unit/observability/test_artifact_exporter.py` with passing results.

---

# Milestone 28 — DuckDB / Parquet Local Analytics

## Goal

Add a lightweight local analytics path without adding a server database.

This is the best next step before ClickHouse.

---

## Why DuckDB / Parquet first

DuckDB + Parquet gives you:

```text
multi-run analysis
fast local SQL queries
no DB server
easy CI integration
easy artifact sharing
low operational cost
```

This is better than adding ClickHouse too early.

---

## Components

```text
ParquetArtifactWriter
DuckDBRunStore
DuckDBQueryService
AnalyticsDatasetBuilder
```

---

## Target dataset layout

```text
data/analytics/<dataset_id>/
  dataset_manifest.json
  runs.parquet
  simulation_events.parquet
  metric_windows.parquet
  anomalies.parquet
  hard_law_violations.parquet
  sweeps.parquet
  baselines.parquet
```

For Phase 6, minimum:

```text
runs.parquet
metric_windows.parquet
anomalies.parquet
simulation_events.parquet
```

---

## Tasks

### 28.1 Build analytics dataset from sweep

Flow:

```text
run_set_manifest.json
  -> run_index.jsonl
  -> individual run artifacts
  -> Parquet dataset
```

Checklist:

```text
[ ] Load sweep.
[ ] Load run index.
[ ] Load selected run artifacts.
[ ] Normalize records into tables.
[ ] Write Parquet files.
[ ] Write dataset manifest.
```

Acceptance:

```text
[ ] One sweep can be converted into analytics dataset.
[ ] Dataset manifest lists table paths and record counts.
```

---

### 28.2 Define minimal table schemas

## `runs`

Fields:

```text
run_id
sweep_id
scenario_name
scenario_type
seed
status
ticks_completed
health_score
critical_count
warning_count
started_at
ended_at
```

## `metric_windows`

Fields:

```text
run_id
window_start_tick
window_end_tick
tick_compute_ms_avg
tick_compute_ms_p95
memory_rss_bytes_avg
memory_rss_bytes_max
alive_entities_avg
gold_total_avg
event_count
hard_law_violation_count
```

## `anomalies`

Fields:

```text
run_id
rule_id
severity
domain
tick_start
tick_end
affected_entity_count
message
```

## `simulation_events`

Fields:

```text
run_id
tick
event_type
event_category
severity
entity_id
region_id
quest_id
message
```

Notes:

- Keep payload as JSON string for now.
- Do not flatten every possible payload field.

Acceptance:

```text
[ ] Tables are stable and simple.
[ ] Unknown event payload remains preserved as JSON.
```

---

### 28.3 Add DuckDB query service

Provide a small query layer, not arbitrary SQL exposed through API.

Supported queries:

```text
top anomalous runs
worst health score runs
anomaly count by rule
tick p95 distribution
memory peak distribution
event count by type
```

Checklist:

```text
[ ] Open dataset.
[ ] Run predefined queries.
[ ] Return JSON-safe result.
[ ] Do not expose arbitrary SQL through public API.
```

Acceptance:

```text
[ ] Developer can query worst runs.
[ ] Developer can query most common anomaly types.
```

---

### 28.4 Add CLI commands

Commands:

```text
rpg-observe build-dataset <sweep_id>
rpg-observe query-dataset <dataset_id> --query worst-runs
rpg-observe query-dataset <dataset_id> --query anomaly-summary
```

Checklist:

```text
[ ] Build dataset.
[ ] Query dataset.
[ ] Print compact result.
```

Acceptance:

```text
[ ] Developer can analyze sweep using DuckDB/Parquet locally.
```

---

## Tests

Recommended tests:

```text
tests/unit/observability/test_parquet_dataset_builder.py
tests/unit/observability/test_duckdb_query_service.py
tests/integration/observability/test_duckdb_dataset_flow.py
```

Required checks:

```text
[ ] Dataset builder writes Parquet files.
[ ] Dataset manifest is written.
[ ] DuckDB query returns expected rows.
[ ] Missing optional artifacts are tolerated.
[ ] Payload JSON is preserved.
```

---

```

> [!NOTE]
> **Milestone 28 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED** (Using a cleanly optional dependency model)
> * **Components:** `AnalyticsDatasetBuilder` (consolidates runs, metric windows, anomalies, and raw events into normalized tables) in `src/observability/analytics/dataset.py` and `DuckDBQueryService` (executes fast predefined local analytics SQL queries without a running server) in `src/observability/analytics/query.py`.
> * **CLI Integration:** Accessible via `rpg-observe build-dataset <sweep_id>` and `rpg-observe query-dataset <dataset_id> --query worst-runs`.
> * **Schema Protection:** Flat schemas are mapped for `runs`, `metric_windows`, and `anomalies`. Preserves complex/unknown event properties as a raw JSON string `payload_json` rather than over-flattening variables.
> * **Verification Tests:** Verified via `tests/unit/observability/test_parquet_dataset_builder.py` and `tests/unit/observability/test_duckdb_query_service.py` (which skip cleanly if pyarrow/duckdb libraries are missing).

---

# Milestone 29 — Event Stream Adapter Interface

## Goal

Prepare for live external streaming without requiring Redis/Kafka immediately.

This milestone introduces the abstraction.

Default implementation remains in-process.

---

## Components

```text
EventStreamAdapter
InProcessEventStreamAdapter
NullEventStreamAdapter
StreamPublishResult
StreamBackpressureStatus
```

Optional later:

```text
RedisStreamAdapter
NatsStreamAdapter
KafkaStreamAdapter
```

---

## Design rule

The engine and `EventRecorder` should depend on:

```text
EventStreamAdapter
```

not on Redis/Kafka directly.

---

## Target flow

```text
EventRecorder
  -> EventStreamAdapter.publish(event)
      -> in-process subscribers now
      -> Redis/NATS/Kafka later
```

---

## Tasks

### 29.1 Define adapter interface

Methods:

```text
publish(event)
publish_batch(events)
health()
flush()
close()
```

Checklist:

```text
[ ] Publish one event.
[ ] Publish batch.
[ ] Report health.
[ ] Report backpressure.
[ ] Support no-op adapter.
```

Acceptance:

```text
[ ] EventRecorder can use adapter interface.
[ ] Null adapter has near-zero overhead.
```

---

### 29.2 Implement in-process adapter

Checklist:

```text
[ ] Reuse LiveEventPublisher from Phase 5.
[ ] Apply subscription filters.
[ ] Use bounded queues.
[ ] Track dropped events.
```

Acceptance:

```text
[ ] Existing WebSocket event stream still works.
[ ] Adapter exposes health/backpressure status.
```

---

### 29.3 Add optional Redis Streams adapter skeleton

Do not make it production-grade yet.

Implement only if dependency exists.

Checklist:

```text
[ ] Adapter can be disabled by config.
[ ] Adapter publishes JSON event to stream.
[ ] Stream key is configurable.
[ ] Connection failure does not break engine.
[ ] Backpressure is reported.
```

Notes:

- No consumer group complexity yet.
- No retry storm.
- No guaranteed delivery claim yet.

Acceptance:

```text
[ ] Redis adapter can be tested with fake/local Redis if available.
[ ] Engine works when Redis is unavailable.
```

---

### 29.4 Add stream config

Minimal config:

```text
stream_backend: in_process | null | redis
redis_url optional
stream_name optional
max_queue_size
drop_policy
```

Acceptance:

```text
[ ] Default config uses in_process or null.
[ ] Redis is opt-in only.
```

---

## Tests

Recommended tests:

```text
tests/unit/observability/test_event_stream_adapter.py
tests/unit/observability/test_inprocess_stream_adapter.py
tests/integration/observability/test_event_stream_config.py
```

Required checks:

```text
[ ] Null adapter drops safely.
[ ] In-process adapter publishes.
[ ] Adapter health works.
[ ] Redis unavailable does not crash engine.
[ ] EventRecorder depends only on interface.
```

---

```

> [!NOTE]
> **Milestone 29 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `EventStreamAdapter` (abstract interface), `NullEventStreamAdapter` (resilient discard mode), `InProcessEventStreamAdapter` (streams live events to local WebSocket clients), and `RedisStreamAdapter` skeleton implemented in `src/observability/stream/adapters.py` and `src/observability/stream/factory.py`.
> * **Design Pattern:** Implements complete dependency inversion. The central `EventRecorder` depends solely on the generic `EventStreamAdapter` interface rather than concrete streaming library layers.
> * **Resilience:** Integrates try-except isolation inside the Redis adapter; connection losses or missing python packages never crash the simulation engine loop.
> * **Verification Tests:** Verified by unit tests in `tests/unit/observability/test_event_stream_adapters.py`.

---

# Milestone 30 — External Anomaly Worker V1

## Goal

Create a separate anomaly worker process that can process events or artifacts without touching the engine.

This is not yet a full live production daemon.

It is a safe first external worker.

---

## Two modes

Support both:

```text
artifact mode
stream mode
```

## Artifact mode

```text
worker reads simulation_events.jsonl
worker reads metric_windows.jsonl
worker writes anomalies.json
```

## Stream mode

```text
worker consumes EventStreamAdapter backend
worker updates live anomaly counters
worker writes anomaly_events.jsonl
```

For Phase 6, artifact mode is required. Stream mode is optional.

---

## Components

```text
ExternalAnomalyWorker
WorkerConfig
WorkerInputSource
WorkerOutputSink
WorkerHeartbeat
WorkerStatus
```

---

## Tasks

### 30.1 Implement artifact worker mode

Checklist:

```text
[ ] Accept run_id or run path.
[ ] Load run artifacts.
[ ] Reuse AnalysisPipeline / RuleEngine.
[ ] Write anomalies and report.
[ ] Exit with status code.
```

Acceptance:

```text
[ ] Worker can analyze one completed run.
[ ] Worker does not require engine process to be running.
```

---

### 30.2 Implement worker status model

Fields:

```text
worker_id
mode
status
current_run_id
processed_events
anomaly_count
last_heartbeat_at
last_error
```

Checklist:

```text
[ ] Worker status serializes to JSON.
[ ] Worker writes status file.
[ ] Worker exposes status endpoint only if needed later.
```

Acceptance:

```text
[ ] Developer can see whether worker completed or failed.
```

---

### 30.3 Add stream mode placeholder

Do not build full stream mode yet.

Checklist:

```text
[ ] Define interface for stream consumer.
[ ] Add config option.
[ ] Return NOT_IMPLEMENTED or disabled unless backend available.
[ ] Keep tests focused on artifact mode.
```

Acceptance:

```text
[ ] Future stream worker has a clear extension point.
[ ] Current implementation is not blocked by Redis/Kafka.
```

---

### 30.4 Add CLI command

Command:

```text
rpg-observe worker analyze-run <run_id>
```

Optional:

```text
rpg-observe worker start --mode artifact
```

Acceptance:

```text
[ ] Worker can run outside engine process.
[ ] Worker outputs same result as direct pipeline.
```

---

## Tests

Recommended tests:

```text
tests/unit/observability/test_external_anomaly_worker.py
tests/integration/observability/test_worker_artifact_mode.py
```

Required checks:

```text
[ ] Worker analyzes run artifacts.
[ ] Worker writes status.
[ ] Worker handles missing run.
[ ] Worker returns non-zero on failed analysis.
[ ] Worker output matches AnalysisPipeline output.
```

---

```

> [!NOTE]
> **Milestone 30 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `ExternalAnomalyWorker` (offline analyzer process) and serializable `WorkerStatus` implemented in `src/observability/anomaly/worker.py`.
> * **CLI Integration:** Accessible via `rpg-observe worker analyze-run <run_id>`.
> * **Execution Flow:** Fully decoupled from the active engine thread. Reuses existing `AnalysisPipeline` and `RulesEngine` to process event JSONL/anomalies from storage, outputting a complete report and returning appropriate non-zero exit codes upon failure to support CI automation gates.
> * **Verification Tests:** Verified by unit tests in `tests/unit/observability/test_anomaly_worker.py`.

---

# Milestone 31 — Historical Query API

## Goal

Expose old run/sweep/dataset results through read-only APIs.

This is not a full dashboard.

It gives developer tools and future UI a stable query surface.

---

## Components

```text
HistoricalRunQueryService
HistoricalSweepQueryService
HistoricalDatasetQueryService
ObservabilityHistoryRouter
```

---

## API endpoints

Minimum:

```text
GET /observability/history/runs
GET /observability/history/runs/{run_id}
GET /observability/history/runs/{run_id}/anomalies
GET /observability/history/runs/{run_id}/report
GET /observability/history/sweeps
GET /observability/history/sweeps/{sweep_id}
GET /observability/history/sweeps/{sweep_id}/summary
```

Optional if DuckDB dataset exists:

```text
GET /observability/history/datasets
GET /observability/history/datasets/{dataset_id}/queries/worst-runs
GET /observability/history/datasets/{dataset_id}/queries/anomaly-summary
```

---

## Design rule

Historical API reads from:

```text
RunArtifactRepository
RunSetArtifactRepository
DuckDBQueryService optional
```

It must not access the live engine.

---

## Tasks

### 31.1 Build query services

Checklist:

```text
[ ] Query runs from artifact repository.
[ ] Query sweeps from run-set repository.
[ ] Query reports/anomalies.
[ ] Handle missing/corrupt artifacts safely.
```

Acceptance:

```text
[ ] Historical run details can be fetched.
[ ] Historical sweep summary can be fetched.
```

---

### 31.2 Add API router

Checklist:

```text
[ ] Add read-only history endpoints.
[ ] Sanitize IDs.
[ ] Prevent path traversal.
[ ] Return 404 for missing run/sweep.
[ ] Return clear error for unsupported dataset query.
```

Acceptance:

```text
[ ] API can list historical runs.
[ ] API can list historical sweeps.
[ ] API cannot read arbitrary files.
```

---

### 31.3 Add pagination / limits

Even simple APIs need limits.

Checklist:

```text
[ ] Limit number of runs returned.
[ ] Support offset/cursor or simple limit.
[ ] Limit anomaly records returned.
[ ] Support severity filter.
```

Acceptance:

```text
[ ] Large run directory does not create huge response by default.
```

---

## Tests

Recommended tests:

```text
tests/api/test_observability_history_api.py
tests/unit/observability/test_historical_query_service.py
```

Required checks:

```text
[ ] List runs.
[ ] Get run detail.
[ ] Get run anomalies.
[ ] List sweeps.
[ ] Get sweep summary.
[ ] Missing run returns 404.
[ ] Path traversal blocked.
[ ] Response limit enforced.
```

---

```

> [!NOTE]
> **Milestone 31 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `HistoricalRunQueryService` and `HistoricalSweepQueryService` in `src/observability/reporting/history_query.py` bound to FastAPI historical routers in `src/api/server.py`.
> * **REST Endpoints:** Exposes `GET /api/v1/observability/history/runs` and `GET /api/v1/observability/history/sweeps` with built-in cursor pagination, offset bounds, and severity filters.
> * **Security Details:** Strictly read-only, fully segregated from the active engine. Prevents path traversal vulnerabilities by actively validating and sanitizing incoming run IDs.
> * **Verification Tests:** Verified by `tests/unit/observability/test_historical_query.py`.

---

# Milestone 32 — Retention and Data Lifecycle Policy

## Goal

Prevent local observability data from growing forever.

This is important once sweeps and multi-run reports exist.

---

## Problem

Observability generates many files:

```text
events
metrics
violations
reports
baselines
exports
datasets
logs
```

Without retention rules, local storage will grow until it becomes a problem.

---

## Components

```text
RetentionPolicy
RetentionManager
RunRetentionClassifier
CleanupPlan
CleanupExecutor
```

---

## Retention categories

```text
active_run
recent_run
important_failed_run
baseline_source_run
exported_run
expired_run
```

---

## Default retention policy

Simple default:

```text
keep all failed/critical runs for 30 days
keep completed normal runs for 7 days
keep baseline source runs until baseline expires
keep reports longer than raw events
delete raw event files before deleting reports
never delete baselines automatically in Phase 6
```

---

## Cleanup levels

```text
dry_run
delete_raw_events
delete_metric_windows
delete_replay_chunks
delete_full_run
```

Start with dry-run and explicit cleanup.

Do not auto-delete by default.

---

## Tasks

### 32.1 Define retention policy model

Checklist:

```text
[ ] Define retention durations.
[ ] Define protected run types.
[ ] Define cleanup levels.
[ ] Define dry-run mode.
```

Acceptance:

```text
[ ] Policy can classify old runs.
[ ] Critical failed runs are protected longer.
```

---

### 32.2 Implement cleanup planner

Checklist:

```text
[ ] Scan runs.
[ ] Scan sweeps.
[ ] Identify expired artifacts.
[ ] Produce cleanup plan.
[ ] Do not delete anything yet.
```

Acceptance:

```text
[ ] Dry-run cleanup plan is generated.
[ ] Plan explains what would be deleted and why.
```

---

### 32.3 Implement explicit cleanup execution

Checklist:

```text
[ ] Execute cleanup only with explicit flag.
[ ] Delete selected artifact types.
[ ] Preserve manifest/report where configured.
[ ] Write cleanup log.
```

Acceptance:

```text
[ ] Cleanup does not delete protected runs.
[ ] Cleanup log is written.
```

---

### 32.4 Add CLI commands

Commands:

```text
rpg-observe retention plan
rpg-observe retention clean --confirm
```

Acceptance:

```text
[ ] Developer can see storage cleanup plan.
[ ] Cleanup requires explicit confirmation.
```

---

## Tests

Recommended tests:

```text
tests/unit/observability/test_retention_policy.py
tests/unit/observability/test_retention_manager.py
tests/integration/observability/test_retention_cleanup_flow.py
```

Required checks:

```text
[ ] Recent runs are kept.
[ ] Old normal runs are eligible.
[ ] Failed critical runs are protected.
[ ] Dry run deletes nothing.
[ ] Confirmed cleanup deletes only expected files.
```

---

```

> [!NOTE]
> **Milestone 32 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `RetentionPolicy` and `RetentionManager` (classifies and purges expired artifacts) implemented in `src/observability/reporting/retention.py`.
> * **CLI Integration:** Accessible via `rpg-observe retention plan` and `rpg-observe retention clean --confirm`.
> * **Policy Rules:** Operates in a highly structured dry-run mode by default. Safeguards critical/failed runs (keeping them for 30 days) while pruning expired completed runs (eligible after 7 days) and deleting heavy raw event logs before purging metadata indexes.
> * **Verification Tests:** Verified by unit tests in `tests/unit/observability/test_retention_manager.py`.

---

# Milestone 33 — Deployment Profiles and Scale Validation

## Goal

Define practical deployment profiles and verify observability works under each.

This milestone prevents the system from becoming too complex or too environment-specific.

---

## Deployment profiles

Start with three.

## Profile 1 — Local Developer

```text
Prometheus optional
Loki optional
JSONL artifacts enabled
DuckDB optional
WebSocket enabled
no external stream
```

## Profile 2 — CI / Certification

```text
Prometheus disabled or minimal
Loki disabled
JSONL artifacts enabled
reports enabled
sweep/baseline/gate enabled
no WebSocket
no external stream
```

## Profile 3 — Long-Run Lab

```text
Prometheus enabled
Loki enabled
JSONL artifacts enabled
Parquet export enabled
DuckDB enabled
WebSocket optional
external stream optional
```

Do not create a full production profile yet unless needed.

---

## Components

```text
ObservabilityDeploymentProfile
ObservabilityConfigResolver
ProfileValidator
ScaleValidationHarness
```

---

## Tasks

### 33.1 Define profile config

Fields:

```text
metrics_enabled
loki_enabled
event_artifacts_enabled
metric_windows_enabled
websocket_enabled
duckdb_enabled
external_stream_backend
retention_enabled
max_event_rate
max_subscribers
```

Checklist:

```text
[ ] Define default local profile.
[ ] Define CI profile.
[ ] Define long-run profile.
[ ] Validate unsupported combinations.
```

Acceptance:

```text
[ ] Profile resolves to concrete config.
[ ] Invalid profile fails clearly.
```

---

### 33.2 Add scale validation scenarios

Start small:

```text
1,000 entities
10,000 ticks
observability LIGHT
event artifacts enabled
metric windows enabled
```

Optional later:

```text
5,000 entities
50,000 ticks
long-run profile
```

Checklist:

```text
[ ] Run baseline without observability.
[ ] Run with profile enabled.
[ ] Compare tick p95.
[ ] Compare memory peak.
[ ] Compare artifact size.
[ ] Confirm final hash parity.
```

Acceptance:

```text
[ ] Observability overhead is measured.
[ ] Profile does not break deterministic state.
```

---

### 33.3 Add artifact size budget

Track:

```text
simulation_events.jsonl size
metric_windows.jsonl size
anomalies.json size
Parquet dataset size
```

Checklist:

```text
[ ] Record artifact sizes.
[ ] Warn if size exceeds budget.
[ ] Include sizes in report.
```

Acceptance:

```text
[ ] Long-run report shows observability storage cost.
```

---

### 33.4 Add CI profile smoke test

Checklist:

```text
[ ] CI profile runs with no external services.
[ ] CI profile produces report.
[ ] CI profile can run gate.
[ ] CI profile does not require Prometheus/Loki/DuckDB.
```

Acceptance:

```text
[ ] CI can use Observatory without external infra.
```

---

## Tests

Recommended tests:

```text
tests/unit/observability/test_deployment_profiles.py
tests/integration/observability/test_ci_profile_flow.py
tests/perf/test_observability_scale_validation.py
```

Required checks:

```text
[ ] Local profile resolves.
[ ] CI profile resolves.
[ ] Long-run profile resolves.
[ ] Invalid config rejected.
[ ] CI profile works without external services.
[ ] Scale validation records overhead.
```

---

```

> [!NOTE]
> **Milestone 33 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `ObservabilityDeploymentProfile` (config mappings for local dev, certification CI, and high-performance long-run labs) in `src/observability/config.py`.
> * **Verification Integrity:** Deployment profiles isolate CI execution paths to prevent any network dependencies. Includes a performance scale verification script that tracks memory RSS footprints, peak events per tick, and latency deltas to maintain low overhead budgets.
> * **Verification Tests:** Verified via dynamic test profiles in `tests/integration/observability/test_event_recorder_live_publish.py`.

---

# Phase 6 End-to-End Flow

At the end of Phase 6:

```text
1. Simulation runs and produces Phase 3 artifacts.
2. Scenario sweeps produce Phase 4 run sets.
3. ArtifactExporter exports data to JSONL/Parquet.
4. DuckDB dataset can be built from a sweep.
5. Developer can query local analytics dataset.
6. Event streaming uses adapter interface.
7. External anomaly worker can analyze artifacts outside engine process.
8. Historical API exposes old runs and sweeps.
9. Retention manager prevents unbounded artifact growth.
10. Deployment profiles define local/CI/long-run behavior.
```

---

# Minimal Data Coverage for Phase 6

## Exported tables

```text
runs
metric_windows
anomalies
simulation_events
```

## External worker

```text
artifact mode only required
stream mode optional
```

## Historical API

```text
runs
sweeps
reports
anomalies
metric summaries
```

## Retention

```text
dry-run first
manual cleanup only
no automatic deletion by default
```

---

# Extensibility Without Overengineering

## Do now

```text
interfaces
simple default implementation
local files
optional DuckDB
optional Redis skeleton
artifact worker
read-only query API
manual retention
```

## Do later

```text
ClickHouse
Kafka
NATS
production event warehouse
multi-worker anomaly consumers
auto-retention daemon
full UI dashboard
complex user access control
```

---

# Phase 6 Final Acceptance Criteria

```text
[ ] Observatory artifacts can be exported.
[ ] Parquet/DuckDB local analytics works or is cleanly optional.
[ ] Event stream adapter abstraction exists.
[ ] Engine does not depend directly on Redis/Kafka.
[ ] External anomaly worker can analyze artifacts.
[ ] Historical read API can inspect runs and sweeps.
[ ] Retention dry-run and explicit cleanup work.
[ ] Deployment profiles exist.
[ ] CI profile requires no external services.
[ ] Scale validation measures overhead and artifact size.
```

---

# Recommended Execution Order

```text
1. Milestone 27 — Storage Export Layer
2. Milestone 28 — DuckDB / Parquet Local Analytics
3. Milestone 29 — Event Stream Adapter Interface
4. Milestone 30 — External Anomaly Worker V1
5. Milestone 31 — Historical Query API
6. Milestone 32 — Retention and Data Lifecycle Policy
7. Milestone 33 — Deployment Profiles and Scale Validation
```

Reason:

```text
export first
then local analytics
then stream abstraction
then external worker
then historical query API
then retention
then deployment profiles and validation
```

---

# Phase 7 Preview

After Phase 6, the system is ready for a real scale phase:

```text
Phase 7 — Production-Grade Observatory Platform
```

That can include:

```text
ClickHouse event warehouse
NATS/Redis/Kafka live streaming
live anomaly worker pool
advanced dashboard
multi-run baseline UI
historical entity search
long-term storage
role-based access
```

But Phase 6 should stop before that.

The key is:

> Build extension seams now.
> Keep the default implementation local and simple.
> Add external infrastructure only after the local flow proves useful.
