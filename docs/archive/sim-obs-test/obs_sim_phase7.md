---
status: archive
authority: P2
audience: historical
layer: engine
original_date: unknown
---

# Phase 7 Implementation Plan — Production-Grade Observatory Platform

Phase 7 should only start after Phase 6 proves that local artifacts, DuckDB/Parquet, historical APIs, and optional stream adapters are useful.

This phase is about moving from:

```text id="p7_intro_1"
local developer observability
```

to:

```text id="p7_intro_2"
long-running production/lab observability platform
```

But we still avoid overengineering.

The final feasibility roadmap already recommends staged delivery and warns against jumping directly to heavy external infrastructure before the local pipeline is proven.

---

# Phase 7 Goal

## Main objective

Add production-grade observability capabilities:

```text id="p7_goal_1"
external event storage
live event streaming
anomaly worker service
historical event search
alerting
observability dashboard
multi-run investigation
controlled retention
```

But every external component should remain optional and replaceable.

---

# Phase 7 Should Include

```text id="p7_include_1"
1. Event warehouse adapter
2. External stream adapter productionization
3. Live anomaly worker service
4. Historical event search
5. Advanced run/sweep dashboard
6. Alert routing
7. Access and operational safety
8. Production readiness validation
```

---

# Phase 7 Should Not Include Yet

```text id="p7_exclude_1"
1. ML anomaly detection
2. auto-balancing stats
3. auto-remediation of simulation logic
4. full multiplayer/server gameplay platform
5. complex role-based enterprise system
6. replacing all file artifacts
7. making ClickHouse/Kafka mandatory
```

File artifacts should remain the source of truth for local/CI workflows.

---

# Phase 7 Entry Criteria

Do not start Phase 7 unless these are true:

```text id="p7_entry_1"
[ ] Phase 3 single-run Observatory flow works.
[ ] Phase 4 multi-run baseline flow works.
[ ] Phase 5 live inspection works.
[ ] Phase 6 export/retention/deployment profiles work.
[ ] JSONL/Parquet artifacts are becoming too large or too slow for some use cases.
[ ] The team has clear query requirements for historical event search.
[ ] There is a real need for live anomaly processing outside the engine process.
```

---

# Phase 7 Milestones

```text id="p7_milestones_1"
Milestone 34 — Warehouse Adapter and Schema Stabilization
Milestone 35 — ClickHouse Event Warehouse V1
Milestone 36 — Production Stream Adapter
Milestone 37 — Live Anomaly Worker Service
Milestone 38 — Historical Event Search API
Milestone 39 — Observatory Dashboard V1
Milestone 40 — Alert Routing and Incident Workflow
Milestone 41 — Production Readiness Validation
```

---

# Milestone 34 — Warehouse Adapter and Schema Stabilization

## Goal

Prepare the Observatory for an external event warehouse without coupling the engine to a specific database.

This milestone should not start by choosing a huge stack. It should define the adapter boundary first.

---

## Why this matters

The engine currently produces artifacts:

```text id="m34_artifacts_1"
simulation_events.jsonl
metric_windows.jsonl
anomalies.json
run_report.json
baseline.json
sweep_report.json
```

Future warehouse storage may be:

```text id="m34_storage_1"
ClickHouse
TimescaleDB
PostgreSQL
DuckDB
S3 + Parquet
```

The analyzer and engine should not care.

---

## Components

```text id="m34_components_1"
WarehouseAdapter
WarehouseWriteJob
WarehouseQueryJob
WarehouseSchemaRegistry
WarehouseIngestionResult
WarehouseHealthStatus
```

---

## Design logic

Use this boundary:

```text id="m34_flow_1"
RunArtifactRepository
  -> WarehouseAdapter
      -> ingest run artifacts
      -> ingest sweep artifacts
      -> query historical data
```

The engine should never write directly to ClickHouse/PostgreSQL/etc.

---

## Minimal warehouse tables

Stabilize these logical schemas:

```text id="m34_tables_1"
runs
sweeps
simulation_events
metric_windows
anomalies
hard_law_violations
baselines
comparison_results
```

Do not add every domain-specific table yet.

---

## Tasks

### 34.1 Define warehouse adapter interface

Checklist:

```text id="m34_check_1"
[ ] Define ingest_run(run_id).
[ ] Define ingest_sweep(sweep_id).
[ ] Define query_runs(filter).
[ ] Define query_events(filter).
[ ] Define query_anomalies(filter).
[ ] Define health().
[ ] Define close().
```

Acceptance:

```text id="m34_accept_1"
[ ] Analyzer can call adapter without knowing DB implementation.
[ ] Null/local adapter exists for tests.
```

---

### 34.2 Define stable warehouse record models

Checklist:

```text id="m34_check_2"
[ ] Define RunRecord.
[ ] Define SweepRecord.
[ ] Define EventRecord.
[ ] Define MetricWindowRecord.
[ ] Define AnomalyRecord.
[ ] Define HardLawViolationRecord.
[ ] Define BaselineRecord.
[ ] Define ComparisonRecord.
```

Important:

```text id="m34_rule_1"
Keep payload fields as JSON string first.
Do not flatten every domain-specific payload.
```

Acceptance:

```text id="m34_accept_2"
[ ] Records can be converted from local artifacts.
[ ] Records can be serialized to JSON.
[ ] Schema version is included.
```

---

### 34.3 Add schema registry

Checklist:

```text id="m34_check_3"
[ ] Define warehouse schema version.
[ ] Validate incoming artifact schema.
[ ] Validate outgoing warehouse schema.
[ ] Reject unsupported versions clearly.
```

Acceptance:

```text id="m34_accept_3"
[ ] Ingestion fails safely on incompatible schema.
[ ] Error explains version mismatch.
```

---

### 34.4 Add ingestion dry-run mode

Checklist:

```text id="m34_check_4"
[ ] Validate run artifacts.
[ ] Convert to warehouse records.
[ ] Count records.
[ ] Do not write to DB.
[ ] Report what would be ingested.
```

Acceptance:

```text id="m34_accept_4"
[ ] Developer can run ingestion validation without database.
```

---

## Tests

```text id="m34_tests_1"
tests/unit/observability/test_warehouse_adapter_interface.py
tests/unit/observability/test_warehouse_record_mapping.py
tests/integration/observability/test_warehouse_ingestion_dry_run.py
```

Required checks:

```text id="m34_test_checks_1"
[ ] Local artifacts map to warehouse records.
[ ] Schema version validation works.
[ ] Dry-run reports record counts.
[ ] Unsupported schema fails clearly.
```

---

```text id="m34_complete_1"
[ ] WarehouseAdapter exists.
[ ] Stable logical schemas exist.
[ ] Artifact-to-record mapping works.
[ ] Dry-run ingestion works.
[ ] No database dependency is mandatory.
```

> [!NOTE]
> **Milestone 34 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** Abstract `WarehouseAdapter` (ABC with `@abstractmethod` enforcement) in `src/observability/warehouse/base.py`. Typed record models (`RunRecord`, `EventRecord`, `MetricWindowRecord`, `AnomalyRecord`, `HardLawViolationRecord`, etc.) in `src/observability/warehouse/models.py`. `WarehouseSchemaRegistry` with strict version-pinned validation in `src/observability/warehouse/registry.py`.
> * **Interface completeness:** The adapter defines 8 abstract methods: `ingest_run`, `ingest_sweep`, `query_runs`, `query_events`, `query_anomalies`, `query_metric_windows`, `query_violations`, `health`, and `close`. The interface was extended with `query_metric_windows` and `query_violations` beyond the original spec to align with the canonical M35 ClickHouse table set.
> * **Dry-run mode:** `ingest_run(dry_run=True)` validates artifacts and counts records without writing to any database.
> * **Verification Tests:** `tests/unit/observability/test_warehouse_adapter_interface.py` (ABC enforcement, full stub instantiation) and `tests/unit/observability/test_warehouse_record_mapping.py` (schema version validation, payload serialization). Fixed: the test stub for `DummyWarehouse` was updated to include the expanded `query_metric_windows` and `query_violations` abstract methods.

---

# Milestone 35 — ClickHouse Event Warehouse V1

## Goal

Add a real high-volume analytical event warehouse.

ClickHouse is the preferred option for large event analytics, but it should be optional.

---

## Why ClickHouse

Good for:

```text id="m35_good_1"
large event history
multi-run analytics
fast group-by queries
high compression
historical anomaly analysis
entity/tick/event filtering
```

Not for:

```text id="m35_bad_1"
live tick loop
authoritative state
transactional gameplay logic
primary engine storage
```

---

## Components

```text id="m35_components_1"
ClickHouseWarehouseAdapter
ClickHouseSchemaManager
ClickHouseIngestionJob
ClickHouseQueryService
```

---

## Minimal ClickHouse tables

## `runs`

```text id="m35_runs_1"
run_id
scenario_name
scenario_type
seed
status
ticks_completed
health_score
started_at
ended_at
schema_version
```

## `simulation_events`

```text id="m35_events_1"
run_id
tick
event_type
event_category
severity
entity_id
region_id
quest_id
faction_id
message
payload_json
created_at
```

## `metric_windows`

```text id="m35_metric_1"
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

```text id="m35_anomaly_1"
run_id
rule_id
severity
domain
tick_start
tick_end
affected_entity_count
message
evidence_json
```

---

## Tasks

### 35.1 Add ClickHouse config

Fields:

```text id="m35_config_1"
enabled
host
port
database
username
password
secure
batch_size
```

Checklist:

```text id="m35_check_1"
[ ] ClickHouse disabled by default.
[ ] Config validates required fields when enabled.
[ ] Missing ClickHouse dependency fails clearly.
```

Acceptance:

```text id="m35_accept_1"
[ ] Local/CI profiles work without ClickHouse.
[ ] Long-run profile can enable ClickHouse.
```

---

### 35.2 Implement schema manager

Checklist:

```text id="m35_check_2"
[ ] Create database if configured.
[ ] Create tables.
[ ] Check schema version.
[ ] Refuse destructive migration in V1.
```

Acceptance:

```text id="m35_accept_2"
[ ] Fresh ClickHouse instance can be initialized.
[ ] Existing schema can be checked.
```

---

### 35.3 Implement batch ingestion

Checklist:

```text id="m35_check_3"
[ ] Ingest one run.
[ ] Ingest one sweep.
[ ] Batch inserts.
[ ] Record ingestion result.
[ ] Skip duplicate records or handle idempotency.
```

Simple idempotency:

```text id="m35_idempotency_1"
same run_id + same artifact checksum = skip
same run_id + different checksum = reject unless force
```

Acceptance:

```text id="m35_accept_3"
[ ] Ingested run appears in ClickHouse.
[ ] Re-ingesting same run does not duplicate rows.
```

---

### 35.4 Implement core queries

Supported queries:

```text id="m35_queries_1"
worst runs by health score
anomaly count by rule
events by entity
events by run and tick range
hard law violations by scenario
metric trend by run
```

Checklist:

```text id="m35_check_4"
[ ] Query service exposes predefined queries.
[ ] No arbitrary public SQL endpoint.
[ ] Results are JSON-safe.
```

Acceptance:

```text id="m35_accept_4"
[ ] Developer can query entity event history.
[ ] Developer can query most common anomaly rules.
```

---

### 35.5 Add CLI commands

```text id="m35_cli_1"
rpg-observe warehouse init
rpg-observe warehouse ingest-run <run_id>
rpg-observe warehouse ingest-sweep <sweep_id>
rpg-observe warehouse query worst-runs
rpg-observe warehouse query entity-events --entity-id <id>
```

Acceptance:

```text id="m35_accept_5"
[ ] ClickHouse workflow can be operated from CLI.
```

---

## Tests

```text id="m35_tests_1"
tests/unit/observability/test_clickhouse_record_mapping.py
tests/integration/observability/test_clickhouse_ingestion.py
tests/integration/observability/test_clickhouse_queries.py
```

Notes:

```text id="m35_test_note_1"
ClickHouse integration tests should be optional/skipped when service is unavailable.
```

---

```text id="m35_complete_1"
[ ] ClickHouse adapter exists.
[ ] ClickHouse is optional.
[ ] Schema initialization works.
[ ] Batch ingestion works.
[ ] Core queries work.
[ ] Re-ingestion is safe.
```

> [!NOTE]
> **Milestone 35 Verification Notes:**
> * **Implementation status:** **IMPLEMENTATION EXISTS — Integration tests require live ClickHouse (skipped in CI)**
> * **Components:** `ClickHouseWarehouseAdapter` in `src/observability/warehouse/clickhouse.py`. Implements the full `WarehouseAdapter` ABC including batch inserts, idempotency checks, and the 6 predefined query types (`worst-runs`, `anomaly-summary`, `entity-events`, `run-metric-trend`, `hard-law-violations`, `events-by-tick-range`).
> * **Optionality:** ClickHouse is fully disabled by default. The `clickhouse-driver` Python library is dynamically imported; if missing, the adapter raises a clear `ImportError` on construction. `ObservabilityDeploymentProfile` enables ClickHouse only for the `long_run` profile.
> * **Idempotency:** Implements `same run_id + same artifact checksum = skip`, `different checksum = reject unless force` via a manifest tracking table.
> * **Batch sizing:** Configurable via `SIM_WAREHOUSE_CLICKHOUSE_BATCH_SIZE` / `RPG_WAREHOUSE_CLICKHOUSE_BATCH_SIZE` env vars; defaults to 1000 rows/batch.
> * **CLI commands:** `rpg-observe warehouse init`, `rpg-observe warehouse ingest-run <run_id>`, `rpg-observe warehouse ingest-sweep <sweep_id>`, `rpg-observe warehouse query worst-runs`.
> * **Note on `datetime.utcnow()` deprecation:** `WarehouseIngestionResult.created_at` uses `datetime.utcnow()` — a minor deprecation warning that should be updated to `datetime.now(datetime.UTC)` in a follow-up.

---

# Milestone 36 — Production Stream Adapter

## Goal

Make live event streaming externalizable.

Default remains in-process. Production can use Redis Streams or NATS.

Do not implement every streaming backend.

Pick one simple backend first.

---

## Recommendation

Use this priority:

```text id="m36_priority_1"
1. Redis Streams
2. NATS JetStream later
3. Kafka/Redpanda much later
```

Redis Streams is enough for a first production/lab version.

---

## Components

```text id="m36_components_1"
RedisStreamAdapter
StreamConsumerGroupManager
StreamBackpressureMonitor
StreamPublishMetrics
```

---

## Target flow

```text id="m36_flow_1"
EventRecorder
  -> EventStreamAdapter
      -> Redis Streams
          -> Live anomaly worker
          -> optional UI consumer
```

---

## Important rule

```text id="m36_rule_1"
Stream publishing must never block the simulation tick loop.
```

Use bounded queues and background flush.

---

## Tasks

### 36.1 Implement Redis stream publisher

Checklist:

```text id="m36_check_1"
[ ] Publish SimulationEvent JSON.
[ ] Use configurable stream key.
[ ] Use background publisher thread.
[ ] Use bounded local queue.
[ ] Track dropped events.
[ ] Handle Redis unavailable.
```

Acceptance:

```text id="m36_accept_1"
[ ] Event is published to Redis when available.
[ ] Engine continues when Redis is unavailable.
[ ] Dropped event count is visible.
```

---

### 36.2 Implement backpressure policy

Policy:

```text id="m36_policy_1"
if local publish queue full:
  drop DEBUG/INFO first
  keep WARNING/ERROR/CRITICAL if possible
  increment dropped count
  emit warning metric
```

Checklist:

```text id="m36_check_2"
[ ] Queue size configurable.
[ ] Drop policy configurable.
[ ] Dropped count exported.
[ ] Backpressure status visible.
```

Acceptance:

```text id="m36_accept_2"
[ ] Slow Redis does not block ticks.
[ ] Backpressure is observable.
```

---

### 36.3 Add stream health endpoint

Endpoint:

```text id="m36_api_1"
GET /observability/live/stream-health
```

Fields:

```text id="m36_fields_1"
backend
connected
queue_size
dropped_events
last_publish_error
last_success_at
```

Acceptance:

```text id="m36_accept_3"
[ ] Developer can see stream backend health.
```

---

### 36.4 Add consumer group foundation

Keep it minimal.

Checklist:

```text id="m36_check_4"
[ ] Define consumer group name.
[ ] Worker can read events from stream.
[ ] Ack processed messages.
[ ] Handle malformed event.
```

Do not build complex retry/dead-letter yet.

Acceptance:

```text id="m36_accept_4"
[ ] Basic stream consumer can receive and ack events.
```

---

## Tests

```text id="m36_tests_1"
tests/unit/observability/test_redis_stream_adapter.py
tests/integration/observability/test_stream_backpressure.py
tests/integration/observability/test_stream_consumer_basic.py
```

Optional integration service:

```text id="m36_test_note_1"
Skip Redis tests if Redis is not available.
```

---

```text id="m36_complete_1"
[ ] Redis stream adapter exists.
[ ] Stream backend is optional.
[ ] Publishing is non-blocking.
[ ] Backpressure is handled.
[ ] Stream health is visible.
[ ] Basic consumer group works.
```

> [!NOTE]
> **Milestone 36 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components (production-hardened):** `RedisStreamAdapter` in `src/observability/stream/adapters.py` substantially upgraded from Phase 6 skeleton.
> * **Non-blocking architecture:** Adds a dedicated daemon background thread (`RedisStreamPublisherWorker`) that drains an internal thread-safe `collections.deque` queue. The simulation `publish()` call returns immediately — it only enqueues the event.
> * **Backpressure policy (enhanced):** When the queue is full, `DEBUG`/`INFO` events are silently dropped first. For `WARNING`/`ERROR`/`CRITICAL` events, the policy scans the queue and evicts an older low-severity entry before inserting. If no eviction is possible, the high-severity event is also dropped and `backpressure_active = True`.
> * **Connection resilience:** `_send_to_redis` attempts a reconnect via `_connect()` before every batch if `_connected=False`. `health()` now reflects `queue_size`, `backpressure_active`, `last_success_at`, and `last_publish_error` for stream health observability.
> * **Stream health endpoint:** `GET /api/v1/observability/live/stream-health` added to `src/api/server.py`.
> * **Flush and close:** `flush()` blocks up to 5 seconds waiting for the local queue to drain; `close()` signals the worker thread to terminate and joins with a 1-second timeout.
> * **Verification Tests:** `tests/unit/observability/test_redis_stream_adapter.py` — 3 new tests: async non-blocking, backpressure eviction/dropping behavior, and degraded fallback (missing redis library).

---

# Milestone 37 — Live Anomaly Worker Service

## Goal

Turn the Phase 6 external anomaly worker into a live worker service.

This service consumes events from stream backend and emits anomaly events/counters.

---

## Scope

Keep worker simple.

It should:

```text id="m37_scope_1"
consume SimulationEvents
maintain small rolling windows
detect core live anomalies
emit AnomalyDetected events
export worker metrics
write worker status
```

It should not:

```text id="m37_not_1"
mutate simulation state
auto-fix entities
run heavy ML
perform full post-run analysis
query entire warehouse per event
```

---

## Components

```text id="m37_components_1"
LiveAnomalyWorker
LiveRuleEngine
RollingEventWindow
WorkerMetricsExporter
WorkerStatusEndpoint
AnomalyEventPublisher
```

---

## Core live rules

Only implement these:

```text id="m37_rules_1"
HardLawViolationLive
NavigationStuckLive
EventDropRateHigh
GovernorDegradedLive
CriticalEventObserved
```

Do not implement full economy/quest/combat balance live yet.

---

## Tasks

### 37.1 Implement live worker config

Fields:

```text id="m37_config_1"
worker_id
stream_backend
stream_name
consumer_group
window_ticks
max_memory_mb
enabled_rules
output_mode
```

Checklist:

```text id="m37_check_1"
[ ] Config validates.
[ ] Worker can run in artifact mode or stream mode.
[ ] Stream mode requires stream backend.
```

Acceptance:

```text id="m37_accept_1"
[ ] Worker starts with valid config.
[ ] Worker refuses invalid config clearly.
```

---

### 37.2 Implement stream consumer loop

Checklist:

```text id="m37_check_2"
[ ] Read events.
[ ] Validate event schema.
[ ] Update rolling windows.
[ ] Ack processed events.
[ ] Handle malformed event.
[ ] Handle stream disconnect.
```

Acceptance:

```text id="m37_accept_2"
[ ] Worker consumes valid events.
[ ] Malformed events do not crash worker.
```

---

### 37.3 Implement live rule engine

Checklist:

```text id="m37_check_3"
[ ] Evaluate only enabled rules.
[ ] Use bounded rolling windows.
[ ] Emit anomaly records.
[ ] Deduplicate repeated anomaly spam.
[ ] Track rule status.
```

Acceptance:

```text id="m37_accept_3"
[ ] Hard law event triggers live anomaly.
[ ] Repeated stuck events trigger live anomaly.
[ ] Same anomaly is not emitted every tick forever.
```

---

### 37.4 Publish anomaly outputs

Output destinations:

```text id="m37_output_1"
anomaly_events.jsonl
Prometheus worker metrics
optional Redis stream anomaly channel
Loki warning/error logs
```

Checklist:

```text id="m37_check_4"
[ ] Write local anomaly events.
[ ] Increment counters.
[ ] Publish optional anomaly event.
[ ] Log warnings/errors.
```

Acceptance:

```text id="m37_accept_4"
[ ] Live anomaly is visible in metrics/logs/artifacts.
```

---

### 37.5 Add worker health/status

Endpoint or status file:

```text id="m37_status_1"
worker_id
status
events_processed
anomalies_emitted
last_event_tick
last_error
stream_lag
memory_estimate
```

Acceptance:

```text id="m37_accept_5"
[ ] Developer can check worker health.
```

---

## Tests

```text id="m37_tests_1"
tests/unit/observability/test_live_anomaly_worker.py
tests/unit/observability/test_live_rule_engine.py
tests/integration/observability/test_live_worker_stream_flow.py
```

Required checks:

```text id="m37_test_checks_1"
[ ] Worker consumes event.
[ ] Worker handles malformed event.
[ ] Core live rules fire.
[ ] Duplicate anomalies are suppressed.
[ ] Worker status updates.
```

---

```text id="m37_complete_1"
[ ] LiveAnomalyWorker exists.
[ ] Stream mode works.
[ ] Core live rules work.
[ ] Worker metrics exist.
[ ] Worker status is visible.
[ ] Worker cannot mutate engine state.
```

> [!NOTE]
> **Milestone 37 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `LiveAnomalyWorker`, `LiveWorkerConfig`, `RollingEventWindow`, `LiveWorkerStatus` in `src/observability/anomaly/worker.py`. Live rule classes in `src/observability/anomaly/rules.py`.
> * **Dual stream backend support:** Worker starts a background daemon thread and supports both `in_process` (subscribes via `LiveEventPublisher`) and `redis` (via `RedisStreamConsumer`) backends. Mode is determined by `LiveWorkerConfig.stream_backend`.
> * **5 live rules implemented:** `HardLawViolationLive`, `NavigationStuckLive`, `EventDropRateHigh`, `GovernorDegradedLive`, `CriticalEventObserved` — exactly as specified. Each rule evaluates events against a rolling `window_ticks` sliding window.
> * **Deduplication:** `emit_anomaly` enforces a per-rule+entity cooldown gate of 20 ticks. `dedup_key` = `rule_name:entity_id:event_category`. This prevents alert spam.
> * **Alert integration:** Severe anomalies (`CRITICAL`/`ERROR`/`HIGH`) and worker loop exceptions both route through `AlertsManager.get_router()` automatically.
> * **Memory monitoring:** `flush_diagnostics()` (called every second) samples RSS via `psutil` and sets `status=DEGRADED` if the RSS exceeds `config.max_memory_mb`.
> * **Read-only guarantee:** Worker processes copies of events from the stream. It has no reference to the engine's mutable world state.
> * **Verification Tests:** `tests/unit/observability/test_live_anomaly_worker.py` — 9 tests covering: config validation, rolling window eviction, all 5 live rules, deduplication cooldown, and in-process lifecycle start/stop.

---

# Milestone 38 — Historical Event Search API

## Goal

Expose warehouse-backed historical search.

This gives developers a way to search across many runs.

---

## Supported search cases

Start with these:

```text id="m38_cases_1"
find events for entity_id across a run
find anomalies by rule_id across sweeps
find hard law violations across scenarios
find worst health score runs
find event timeline for one entity
find metric trend for one run
```

Do not build arbitrary query language yet.

---

## Components

```text id="m38_components_1"
HistoricalSearchService
HistoricalSearchQuery
HistoricalSearchResult
WarehouseQueryRouter
SearchPagination
```

---

## API endpoints

```text id="m38_api_1"
GET /observability/search/events
GET /observability/search/anomalies
GET /observability/search/runs
GET /observability/search/entity-timeline
GET /observability/search/metric-trend
```

Query parameters:

```text id="m38_params_1"
run_id
sweep_id
scenario_name
entity_id
event_type
severity
tick_start
tick_end
limit
cursor
```

---

## Tasks

### 38.1 Define search query model

Checklist:

```text id="m38_check_1"
[ ] Define allowed filters.
[ ] Validate IDs.
[ ] Validate tick range.
[ ] Validate limit.
[ ] Reject unsupported filters.
```

Acceptance:

```text id="m38_accept_1"
[ ] Invalid query fails clearly.
[ ] Path traversal impossible.
```

---

### 38.2 Implement query router

Flow:

```text id="m38_flow_1"
if warehouse enabled:
  query ClickHouse
else:
  query local artifacts / DuckDB if available
```

Checklist:

```text id="m38_check_2"
[ ] Prefer warehouse when enabled.
[ ] Fall back to local artifacts if possible.
[ ] Return unsupported if no backend.
```

Acceptance:

```text id="m38_accept_2"
[ ] Search works with ClickHouse.
[ ] Search degrades gracefully without warehouse.
```

---

### 38.3 Add pagination

Checklist:

```text id="m38_check_3"
[ ] Limit max response size.
[ ] Add cursor or offset.
[ ] Return next cursor.
```

Acceptance:

```text id="m38_accept_3"
[ ] Large query does not return huge payload.
```

---

### 38.4 Add query audit logs

Checklist:

```text id="m38_check_4"
[ ] Log search type.
[ ] Log run/sweep scope.
[ ] Do not log huge result payload.
[ ] Do not promote high-cardinality labels.
```

Acceptance:

```text id="m38_accept_4"
[ ] Search is observable without Loki label explosion.
```

---

## Tests

```text id="m38_tests_1"
tests/api/test_historical_event_search_api.py
tests/unit/observability/test_historical_search_service.py
```

Required checks:

```text id="m38_test_checks_1"
[ ] Search events by run.
[ ] Search events by entity.
[ ] Search anomalies by rule.
[ ] Search hard law violations.
[ ] Pagination works.
[ ] Invalid filters rejected.
```

---

```text id="m38_complete_1"
[ ] Historical search API exists.
[ ] Warehouse query router exists.
[ ] Local fallback exists where possible.
[ ] Pagination exists.
[ ] Search is read-only and safe.
```

> [!NOTE]
> **Milestone 38 Verification Notes:**
> * **Implementation status:** **PARTIAL — Core router and API endpoints implemented; full ClickHouse-backed query paths require M35 live ClickHouse**
> * **Components:** `WarehouseQueryRouter` in `src/observability/warehouse/factory.py` orchestrates backend selection. Historical search REST endpoints added to `src/api/server.py` under `GET /api/v1/observability/search/*`.
> * **Routing strategy:** If warehouse is enabled and connected, routes to `ClickHouseWarehouseAdapter`. Falls back to local `DuckDBQueryService` (if enabled) or `HistoricalRunQueryService` from Phase 6.
> * **Supported search cases:** Events by run/entity, anomalies by rule across sweeps, hard law violations by scenario, worst health runs, entity timeline, and metric trends are all exposed.
> * **Dashboard integration:** The `src/api/server.py` UI now includes a full **Historical Event Search** panel with a "QUERY WAREHOUSE" button, paginated result tables, and an Entity Timeline aggregation view backed by these endpoints.
> * **Safety:** IDs sanitized, path traversal blocked, response size bounded by `limit`/`cursor` parameters.

---

# Milestone 39 — Observatory Dashboard V1

## Goal

Create a practical dashboard for developers and QA.

Not a polished product UI.

---

## Dashboard views

Start with five views:

```text id="m39_views_1"
1. Live Run Overview
2. Run Report Browser
3. Sweep / Baseline Comparison
4. Historical Event Search
5. Entity Timeline
```

---

## View 1 — Live Run Overview

Shows:

```text id="m39_live_1"
current tick
health state
TPS / tick compute
memory
governor mode
recent warnings/errors
live event stream
```

---

## View 2 — Run Report Browser

Shows:

```text id="m39_report_1"
list of runs
health score
anomaly summary
hard law violations
report markdown
artifact links
```

---

## View 3 — Sweep / Baseline Comparison

Shows:

```text id="m39_sweep_1"
sweep summary
baseline comparison
worst seeds
health score distribution
most common anomalies
failed expectations
```

---

## View 4 — Historical Event Search

Shows:

```text id="m39_search_1"
search filters
event table
anomaly table
hard law violation table
pagination
```

---

## View 5 — Entity Timeline

Shows:

```text id="m39_timeline_1"
entity id
timeline events
current/live summary if run active
historical events if warehouse enabled
anomaly flags
```

---

## Tasks

### 39.1 Build dashboard shell

Checklist:

```text id="m39_check_1"
[ ] Navigation.
[ ] API client.
[ ] Error handling.
[ ] Loading states.
[ ] Read-only mode.
```

Acceptance:

```text id="m39_accept_1"
[ ] Dashboard loads.
[ ] API errors are displayed clearly.
```

---

### 39.2 Build live overview page

Checklist:

```text id="m39_check_2"
[ ] Display live status.
[ ] Display live health.
[ ] Display recent events.
[ ] Show stream connection status.
```

Acceptance:

```text id="m39_accept_2"
[ ] Developer can see if simulation is alive.
```

---

### 39.3 Build report browser

Checklist:

```text id="m39_check_3"
[ ] List runs.
[ ] Open run report.
[ ] Show anomalies.
[ ] Show hard law violations.
```

Acceptance:

```text id="m39_accept_3"
[ ] Developer can inspect completed run.
```

---

### 39.4 Build sweep comparison page

Checklist:

```text id="m39_check_4"
[ ] List sweeps.
[ ] Show sweep summary.
[ ] Show worst runs.
[ ] Show baseline comparison.
```

Acceptance:

```text id="m39_accept_4"
[ ] Developer can inspect multi-run results.
```

---

### 39.5 Build event search page

Checklist:

```text id="m39_check_5"
[ ] Query by run/entity/event type/severity.
[ ] Show paginated results.
[ ] Open event detail.
```

Acceptance:

```text id="m39_accept_5"
[ ] Developer can search historical events.
```

---

## Tests

```text id="m39_tests_1"
tests/ui/test_observatory_dashboard_smoke.py
tests/api/test_observatory_dashboard_api_contract.py
```

Focus on smoke tests.

Do not overbuild UI tests.

---

```text id="m39_complete_1"
[ ] Dashboard V1 exists.
[ ] Live overview works.
[ ] Run report browser works.
[ ] Sweep comparison works.
[ ] Event search works.
[ ] Entity timeline works.
[ ] Dashboard is read-only.
```

> [!NOTE]
> **Milestone 39 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED (SPA, 5 views)**
> * **Components:** Premium dark-mode glassmorphism SPA served at `GET /api/v1/observability/ui` from `src/api/server.py`. Substantially expanded from the Phase 5 minimal page into a full multi-view dashboard.
> * **5 Views implemented:**
>   1. **Live Run Overview** — Real-time metric cards (tick, TPS, memory, health), governor mode badge, recent event log stream with severity-colored tags.
>   2. **Run Report Browser** — Lists local historical runs, opens full anomaly summaries and artifact links for any selected run.
>   3. **Sweep / Baseline Comparison** — Lists sweeps, shows seed distribution, worst-run highlights, and baseline comparison diffs.
>   4. **Historical Event Search** — Filter panel (run ID, entity, event type, severity), paginated warehouse result table, "QUERY WAREHOUSE" action button.
>   5. **Entity Timeline** — Combines live `EntityInspector` data (when run active) with warehouse historical events (when ClickHouse enabled) to render a full per-entity event timeline.
> * **Read-only guarantee:** The UI fetches purely from existing read-only endpoints (Milestones 21–25, 31, 38). No mutation controls are exposed.

---

# Milestone 40 — Alert Routing and Incident Workflow

## Goal

Route serious Observatory findings to developers.

This is not a full incident management platform.

Start small.

---

## Alert sources

```text id="m40_sources_1"
Hard law violation
Critical anomaly
Watchdog trip
Governor stuck in survival/degraded mode
Stream backpressure high
Anomaly worker failure
```

---

## Alert destinations

Start with:

```text id="m40_dest_1"
logs
Prometheus alert metrics
webhook optional
Slack optional later
```

Do not hard-code Slack first.

Use generic webhook.

---

## Components

```text id="m40_components_1"
AlertRule
AlertRouter
AlertEvent
AlertSink
WebhookAlertSink
LogAlertSink
AlertDeduplicator
```

---

## Tasks

### 40.1 Define alert event

Fields:

```text id="m40_fields_1"
alert_id
alert_type
severity
run_id
sweep_id optional
tick optional
message
evidence
dedup_key
created_at
```

Acceptance:

```text id="m40_accept_1"
[ ] Alert event serializes to JSON.
```

---

### 40.2 Implement alert router

Checklist:

```text id="m40_check_2"
[ ] Route alert to enabled sinks.
[ ] Deduplicate repeated alerts.
[ ] Apply severity threshold.
[ ] Track delivery success/failure.
```

Acceptance:

```text id="m40_accept_2"
[ ] Critical alert reaches log sink.
[ ] Duplicate alert is suppressed.
```

---

### 40.3 Implement webhook sink

Checklist:

```text id="m40_check_3"
[ ] Generic webhook URL.
[ ] Timeout.
[ ] Retry limited.
[ ] Failure logged.
[ ] Disabled by default.
```

Acceptance:

```text id="m40_accept_3"
[ ] Webhook receives alert in test.
[ ] Failed webhook does not crash worker.
```

---

### 40.4 Integrate alert sources

Start with:

```text id="m40_integrate_1"
HardLawViolationDetected
WatchdogTrip
LiveAnomalyWorker critical anomaly
StreamBackpressureHigh
```

Acceptance:

```text id="m40_accept_4"
[ ] Hard law violation creates alert.
[ ] Worker failure creates alert.
```

---

## Tests

```text id="m40_tests_1"
tests/unit/observability/test_alert_router.py
tests/integration/observability/test_alert_webhook_sink.py
```

Required checks:

```text id="m40_test_checks_1"
[ ] Alert routes to log sink.
[ ] Alert routes to webhook sink.
[ ] Duplicate alert suppressed.
[ ] Failed webhook does not crash.
[ ] Severity threshold works.
```

---

```text id="m40_complete_1"
[ ] AlertEvent exists.
[ ] AlertRouter exists.
[ ] Log sink exists.
[ ] Webhook sink exists.
[ ] Hard law / watchdog / worker alerts integrated.
[ ] Alerts are deduplicated.
```

> [!NOTE]
> **Milestone 40 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `AlertEvent` (Pydantic model with factory methods) in `src/observability/alerts/models.py`. `AlertRouter`, `AlertDeduplicator` in `src/observability/alerts/router.py`. `LogAlertSink`, `WebhookAlertSink` in `src/observability/alerts/sinks.py`. `AlertsManager` singleton in `src/observability/alerts/manager.py`.
> * **Factory methods for alert sources:** `AlertEvent.create_hard_law_violation()`, `.create_watchdog_trip()`, `.create_critical_anomaly()`, `.create_stream_backpressure()` provide typed constructors for all primary sources.
> * **Deduplication:** `AlertDeduplicator` uses a time-windowed key cache (`dedup_key` → last seen timestamp). Duplicate alerts within the window are silently suppressed. Expired entries are pruned lazily on lookup.
> * **Severity threshold:** `AlertRouter` filters alerts below a configurable `min_severity` threshold before dispatching to sinks.
> * **Sink resilience:** A failing sink (`WebhookAlertSink` timeout / network error) never crashes the router — exceptions are caught, logged, and tracked in router metrics.
> * **Integration points:** `LiveAnomalyWorker.emit_anomaly()` and `LiveAnomalyWorker._run_loop()` exception handler both call `AlertsManager.get_router().route(event)` automatically. `HardLawMonitor` and kernel watchdog trip events are also wired.
> * **Verification Tests:** `tests/unit/observability/test_alert_router.py` — 19 tests covering AlertEvent factory methods, deduplicator time-window behavior, router dispatch, severity threshold, sink exception isolation, and metrics tracking.

---

# Milestone 41 — Production Readiness Validation

## Goal

Prove that the Production Observatory works without damaging the engine.

---

## Validation areas

```text id="m41_areas_1"
engine performance
stream backpressure
warehouse ingestion
live worker behavior
dashboard read performance
retention safety
alert routing
failure recovery
```

---

## Test scenarios

## Scenario 1 — Normal long run

```text id="m41_s1"
1,000 entities
50,000 ticks
Observatory live + warehouse enabled
```

Validate:

```text id="m41_s1_validate"
tick p95 overhead acceptable
event drop count acceptable
no hard law violations
warehouse ingestion successful
```

---

## Scenario 2 — Stream outage

Simulate:

```text id="m41_s2"
Redis unavailable
```

Validate:

```text id="m41_s2_validate"
engine continues
backpressure visible
alerts generated
no crash
```

---

## Scenario 3 — Warehouse outage

Simulate:

```text id="m41_s3"
ClickHouse unavailable
```

Validate:

```text id="m41_s3_validate"
run artifacts still written locally
warehouse ingestion fails safely
engine continues
```

---

## Scenario 4 — Anomaly worker crash

Validate:

```text id="m41_s4_validate"
engine continues
worker status shows failed
alert generated
worker can restart and resume if stream supports it
```

---

## Scenario 5 — High event volume

Validate:

```text id="m41_s5_validate"
bounded queues hold
low-priority events dropped first
critical events preserved where possible
dropped count visible
tick loop not blocked
```

---

## Components

```text id="m41_components_1"
ProductionReadinessHarness
FailureInjectionTools
ObservabilityOverheadReporter
BackpressureTestHarness
```

---

## Tasks

### 41.1 Define production readiness criteria

Checklist:

```text id="m41_check_1"
[ ] Max tick p95 overhead.
[ ] Max memory overhead.
[ ] Max event drop rate.
[ ] Required alert behavior.
[ ] Required failure behavior.
```

Example thresholds:

```text id="m41_thresholds_1"
LIGHT live mode overhead < 5%
stream outage must not crash engine
warehouse outage must not lose local artifacts
critical alert delivery attempted within 10 seconds
```

Acceptance:

```text id="m41_accept_1"
[ ] Criteria documented.
```

---

### 41.2 Implement failure injection tests

Checklist:

```text id="m41_check_2"
[ ] Simulate stream outage.
[ ] Simulate warehouse outage.
[ ] Simulate worker crash.
[ ] Simulate high event volume.
[ ] Simulate webhook failure.
```

Acceptance:

```text id="m41_accept_2"
[ ] All failures are handled safely.
```

---

### 41.3 Generate readiness report

Report sections:

```text id="m41_report_1"
1. Summary
2. Performance Overhead
3. Event Volume
4. Backpressure Behavior
5. Warehouse Ingestion
6. Worker Stability
7. Alert Routing
8. Failure Recovery
9. Known Limitations
```

Acceptance:

```text id="m41_accept_3"
[ ] Readiness report generated.
[ ] Known limitations are explicit.
```

---

## Tests

```text id="m41_tests_1"
tests/perf/test_production_observatory_overhead.py
tests/integration/test_observatory_stream_outage.py
tests/integration/test_observatory_warehouse_outage.py
tests/integration/test_anomaly_worker_failure.py
```

---

```text id="m41_complete_1"
[ ] Production readiness criteria exist.
[ ] Failure injection tests exist.
[ ] Readiness report exists.
[ ] Stream outage is safe.
[ ] Warehouse outage is safe.
[ ] Worker crash is safe.
[ ] Engine performance remains acceptable.
```

> [!NOTE]
> **Milestone 41 Verification Notes:**
> * **Implementation status:** **CRITERIA DEFINED — Scale/failure integration tests require infra (Redis/ClickHouse)**
> * **Criteria documented:** LIGHT live mode overhead target `< 5%` tick p95 delta. Stream outage must not crash engine. Warehouse outage must not lose local artifacts. Critical alert delivery attempted within 10 seconds.
> * **Failure modes verified by unit tests:**
>   * *Stream outage:* `RedisStreamAdapter` reconnects automatically; `publish()` enqueues to local buffer and marks `backpressure_active=True` if queue fills. `test_redis_adapter_degraded_fallback` confirms engine continues.
>   * *Worker crash:* `LiveAnomalyWorker._run_loop()` catches exceptions, routes a `WorkerLoopFailure` alert, and continues the loop. `test_worker_lifecycle_in_process` confirms start/stop lifecycle.
>   * *High event volume:* Backpressure eviction policy verified by `test_redis_adapter_backpressure_eviction_and_dropping`.
> * **Remaining integration scenarios** (Scenarios 1, 3, and full Scenario 2 end-to-end) require live Redis and ClickHouse instances and are deferred to dedicated lab/infra-available CI environments.

---

# Phase 7 End-to-End Flow

At the end of Phase 7:

```text id="p7_e2e_1"
1. Engine emits curated SimulationEvents.
2. EventRecorder persists local artifacts.
3. EventStreamAdapter optionally publishes events to Redis Streams.
4. LiveAnomalyWorker consumes events and emits anomaly events.
5. WarehouseAdapter ingests run/sweep artifacts into ClickHouse.
6. HistoricalSearchService queries warehouse or local fallback.
7. Dashboard displays live, historical, and sweep-level views.
8. AlertRouter routes critical findings.
9. Retention policy controls local artifact growth.
10. ProductionReadinessHarness validates failure behavior.
```

---

# Minimal Data Coverage for Phase 7

## Warehouse

```text id="p7_min_warehouse_1"
runs
simulation_events
metric_windows
anomalies
hard_law_violations
```

## Live stream

```text id="p7_min_stream_1"
InvariantViolation
NavigationStuck
GovernorModeChanged
WatchdogTrip
EntityKilled
QuestCompleted
```

## Live anomaly worker

```text id="p7_min_worker_1"
HardLawViolationLive
NavigationStuckLive
EventDropRateHigh
GovernorDegradedLive
CriticalEventObserved
```

## Dashboard

```text id="p7_min_dash_1"
live run overview
run report browser
sweep comparison
historical event search
entity timeline
```

## Alerts

```text id="p7_min_alert_1"
hard law violation
watchdog trip
worker failure
stream backpressure
critical anomaly
```

---

# Phase 7 Final Acceptance Criteria

```text id="p7_accept_1"
[ ] Warehouse adapter exists.
[ ] ClickHouse integration is optional and works when enabled.
[ ] Stream adapter supports in-process and Redis backends.
[ ] Live anomaly worker consumes stream events.
[ ] Historical search API works.
[ ] Dashboard V1 works.
[ ] Alert routing works.
[ ] Failure injection tests pass.
[ ] Engine remains safe when external components fail.
[ ] Local artifacts remain available as fallback.
```

---

# Recommended Execution Order

```text id="p7_order_1"
1. Milestone 34 — Warehouse Adapter and Schema Stabilization
2. Milestone 35 — ClickHouse Event Warehouse V1
3. Milestone 36 — Production Stream Adapter
4. Milestone 37 — Live Anomaly Worker Service
5. Milestone 38 — Historical Event Search API
6. Milestone 39 — Observatory Dashboard V1
7. Milestone 40 — Alert Routing and Incident Workflow
8. Milestone 41 — Production Readiness Validation
```

Reason:

```text id="p7_reason_1"
schema first
then warehouse
then streaming
then worker
then search
then dashboard
then alerts
then validation
```

---

# Phase 8 Preview

After Phase 7, the system is production-observable.

The next phase should not add more infrastructure. It should improve **simulation intelligence**:

```text id="p8_preview_1"
Phase 8 — Advanced Simulation Understanding
```

That can include:

```text id="p8_items_1"
deeper balance rules
scenario-specific expectation libraries
root-cause analysis
story detection
automatic baseline evolution
domain-specific dashboards
human review workflow
stat tuning recommendations
```

But that phase should only start after the platform is stable.
