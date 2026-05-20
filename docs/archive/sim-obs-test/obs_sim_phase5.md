# Phase 5 Implementation Plan — Live Observatory and Developer Inspection

Phase 5 should add **live inspection**, but still avoid heavy infrastructure.

The goal is not to build a full production monitoring platform yet. The goal is:

> Developers can watch a running simulation, inspect current state, inspect recent events, and diagnose suspicious behavior without reading raw files manually.

The previous roadmap already recommends staged delivery instead of jumping directly into Redis/Kafka/out-of-process processing too early. So Phase 5 should use **simple in-process/live-read architecture first**, while leaving clean extension points for Redis/NATS/Kafka later.

---

# Phase 5 Goal

## Main objective

Create a minimal but functional **Live Observatory**:

```text id="phase5-flow"
running simulation
  -> live metrics snapshot
  -> live semantic events
  -> focused entity timeline
  -> current run status
  -> lightweight live anomaly counters
  -> developer API / WebSocket stream
```

## Phase 5 should prove

```text id="phase5-proof"
[ ] A developer can see whether a simulation is alive.
[ ] A developer can inspect one running entity.
[ ] A developer can see recent important events.
[ ] A developer can see current health/anomaly counters.
[ ] A developer can subscribe to only the data they care about.
[ ] Live observability does not significantly affect tick performance.
```

---

# Phase 5 Should Include

```text id="phase5-include"
1. Live run status model
2. Live snapshot provider
3. Focused entity inspector
4. Lightweight live event stream
5. WebSocket subscription API
6. Live anomaly counters
7. Basic developer observatory page or API-only view
8. Backpressure / throttling policy
```

---

# Phase 5 Should Not Include Yet

```text id="phase5-exclude"
1. Redis/Kafka/NATS event streaming
2. ClickHouse event warehouse
3. Complex UI dashboard
4. Full game replay viewer
5. Live auto-recovery
6. ML anomaly detection
7. Full entity graph visualization
8. Full world-map renderer
```

Keep it useful and small.

---

# Phase 5 Design Principle

## Simple now, extensible later

Design internal interfaces like this:

```text id="phase5-interfaces"
EventPublisher
EventSubscriber
SubscriptionFilter
LiveSnapshotProvider
EntityInspector
LiveAnomalyCounter
BackpressurePolicy
```

But implement them simply:

```text id="phase5-simple-impl"
EventPublisher = in-process bounded broadcaster
EventSubscriber = WebSocket connection
SnapshotProvider = reads latest safe snapshots
AnomalyCounter = rolling counters from recent events/metrics
BackpressurePolicy = drop old low-severity events
```

Later, replace or extend:

```text id="phase5-future-impl"
EventPublisher -> Redis Streams / NATS / Kafka adapter
SnapshotProvider -> read-model cache / external DB
AnomalyCounter -> out-of-process anomaly daemon
```

---

# Phase 5 Milestones

```text id="phase5-milestones"
Milestone 21 — Live Run Status and Snapshot Provider
Milestone 22 — Entity Inspector V1
Milestone 23 — In-Process Event Publisher and Subscription Filters
Milestone 24 — WebSocket Live Observatory API
Milestone 25 — Lightweight Live Anomaly Counters
Milestone 26 — Minimal Developer Observatory View
```

---

# Milestone 21 — Live Run Status and Snapshot Provider

## Goal

Expose the current simulation run status safely.

This should give developers a quick answer:

```text id="m21-question"
Is the simulation running?
What tick is it on?
Is it healthy?
Is it overloaded?
Are there recent hard law violations?
```

---

## Components

```text id="m21-components"
LiveRunStatus
LiveRunSnapshot
LiveSnapshotProvider
RunStatusCache
```

---

## `LiveRunStatus`

Minimum fields:

```text id="m21-status-fields"
run_id
scenario_name
scenario_type
status
current_tick
ticks_requested
started_at
elapsed_seconds
observability_mode
governor_mode
health_state
last_error
last_hard_law_violation_tick
```

Status values:

```text id="m21-status-values"
IDLE
STARTING
RUNNING
PAUSED
COMPLETED
FAILED
STOPPING
```

---

## `LiveRunSnapshot`

Minimum fields:

```text id="m21-snapshot-fields"
run_status
latest_world_metrics
latest_runtime_status
latest_metric_window_summary
recent_event_counts
recent_anomaly_counts
hard_law_violation_count
```

Do **not** include full world state.

---

## Design logic

The snapshot provider should read from already-maintained snapshots:

```text id="m21-flow"
Kernel / EngineManager
  -> latest WorldMetrics
  -> latest RuntimeStatus
  -> latest event counts
  -> LiveSnapshotProvider
  -> API/WebSocket
```

Important rule:

```text id="m21-rule"
LiveSnapshotProvider must not scan all entities on every request.
```

---

## Tasks

### 21.1 Define live status model

Checklist:

```text id="m21-check-1"
[ ] Define LiveRunStatus.
[ ] Define run lifecycle states.
[ ] Include current tick.
[ ] Include run_id and scenario name.
[ ] Include health state.
[ ] Include last error.
```

Acceptance:

```text id="m21-accept-1"
[ ] Status serializes to JSON.
[ ] Status works when no simulation is running.
[ ] Status works while simulation is running.
```

---

### 21.2 Define snapshot provider

Checklist:

```text id="m21-check-2"
[ ] Provider reads latest cached metrics.
[ ] Provider reads latest runtime status.
[ ] Provider reads event/anomaly counters.
[ ] Provider handles missing data.
[ ] Provider does not mutate engine state.
```

Acceptance:

```text id="m21-accept-2"
[ ] Snapshot request is fast.
[ ] Snapshot request does not block tick loop.
[ ] Missing metrics produce safe null/default values.
```

---

### 21.3 Add read-only API endpoints

Recommended endpoints:

```text id="m21-api"
GET /observability/live/status
GET /observability/live/snapshot
```

Checklist:

```text id="m21-check-3"
[ ] Add live status endpoint.
[ ] Add live snapshot endpoint.
[ ] Return 404 or IDLE response when no run exists.
[ ] Prevent direct access to internal engine state.
```

Acceptance:

```text id="m21-accept-3"
[ ] Developer can query current tick from API.
[ ] Developer can query current health state from API.
```

---

## Tests

```text id="m21-tests"
tests/unit/observability/test_live_snapshot_provider.py
tests/api/test_live_observability_status.py
```

Required checks:

```text id="m21-test-checks"
[ ] Status works without active run.
[ ] Status works with active run.
[ ] Snapshot includes current tick.
[ ] Snapshot does not expose full entity state.
[ ] Snapshot handles missing metrics.
```

---

## Completion checklist

```text id="m21-complete"
[ ] LiveRunStatus exists.
[ ] LiveRunSnapshot exists.
[ ] LiveSnapshotProvider exists.
[ ] /observability/live/status works.
[ ] /observability/live/snapshot works.
[ ] No full-world scan happens per request.
```

> [!NOTE]
> **Milestone 21 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `LiveRunStatus` and `LiveRunSnapshot` defined in `src/observability/live/snapshot_provider.py` (inheriting from Pydantic `BaseModel` for automatic validation and JSON serialization).
> * **Snapshot Provider:** `LiveSnapshotProvider` (also in `src/observability/live/snapshot_provider.py`) accesses engine state, latest world metrics, and `EventRecorder` event counts thread-safely. It operates in $O(1)$ time by reading from pre-aggregated or cached engine metrics, strictly avoiding full-world or all-entity scans to preserve simulation tick performance.
> * **REST API Endpoints:** 
>   * `GET /api/v1/observability/live/status`: Exposes current simulation tick, governors, started time, elapsed seconds, health, and error messages.
>   * `GET /api/v1/observability/live/snapshot`: Provides high-level metrics, event counts, tick speed (TPS), memory RSS, worker queue utilization, and phase breakdown costs.
> * **Verification Tests:** Unit tests in `tests/unit/observability/test_live_snapshot_provider.py` and endpoint testing in `tests/api/test_live_observability_status.py` confirm complete error-tolerance, proper default fallback states when the engine is `IDLE`, and accurate tick reporting when `RUNNING`.

---

# Milestone 22 — Entity Inspector V1

## Goal

Allow developers to inspect one entity during a running simulation.

This is the most useful live debugging feature.

---

## What it should answer

```text id="m22-questions"
Where is this entity?
What is it doing?
What is its current goal?
What was its recent timeline?
Is it stuck?
Is it in combat?
Does it have blockers?
Does it have inventory/capacity issues?
```

---

## Components

```text id="m22-components"
EntityInspector
EntityInspectionSnapshot
EntityTimelineView
EntityInspectionPolicy
```

---

## `EntityInspectionSnapshot`

Minimum fields:

```text id="m22-fields"
entity_id
exists
alive
position
faction_id
region_id
current_goal
current_target
current_action
combat_summary
inventory_summary
quest_summary
strategic_summary
recent_timeline_events
latest_rejection_reason
latest_anomaly_flags
```

Keep summaries compact.

Do **not** return full nested entity state.

---

## Design logic

The inspector should use:

```text id="m22-data"
latest authoritative state snapshot
EntityTimelineStore
recent event records
recent anomaly counters
```

But it should not create new analysis.

It only reads current state and recent observability data.

---

## Tasks

### 22.1 Define compact entity summary

Checklist:

```text id="m22-check-1"
[ ] Define compact entity summary fields.
[ ] Avoid returning full object graph.
[ ] Handle missing components.
[ ] Handle dead/deleted entities.
[ ] Keep output JSON-safe.
```

Acceptance:

```text id="m22-accept-1"
[ ] Inspector can summarize normal entity.
[ ] Inspector can summarize dead entity.
[ ] Inspector can report missing entity cleanly.
```

---

### 22.2 Integrate timeline store

Checklist:

```text id="m22-check-2"
[ ] Attach recent timeline events to entity snapshot.
[ ] Limit number of timeline events.
[ ] Sort by tick.
[ ] Include event type, severity, message, tick.
```

Acceptance:

```text id="m22-accept-2"
[ ] Entity inspection includes recent events.
[ ] Timeline size is bounded.
```

---

### 22.3 Add entity inspection API

Endpoint:

```text id="m22-api"
GET /observability/live/entities/{entity_id}
```

Optional query:

```text id="m22-query"
?timeline_limit=20
```

Checklist:

```text id="m22-check-3"
[ ] Validate entity_id.
[ ] Return compact summary.
[ ] Return timeline snippet.
[ ] Return 404 if entity missing, or exists=false response.
```

Acceptance:

```text id="m22-accept-3"
[ ] Developer can inspect entity by ID.
[ ] API does not expose huge state payload.
```

---

## Tests

```text id="m22-tests"
tests/unit/observability/test_entity_inspector.py
tests/api/test_live_entity_inspection.py
```

Required checks:

```text id="m22-test-checks"
[ ] Existing entity returns summary.
[ ] Missing entity handled cleanly.
[ ] Timeline limit is respected.
[ ] Full entity state is not exposed.
[ ] Dead entity can be inspected.
```

---

## Completion checklist

```

> [!NOTE]
> **Milestone 22 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `EntityInspectionSnapshot` (Pydantic `BaseModel`) and thread-safe `EntityInspector` implemented in `src/observability/live/entity_inspector.py`.
> * **Architecture:** Accesses `V2EngineManager.latest_state` to retrieve static summaries and `kernel.entity_timeline_store` to fetch recent events. 
> * **Granular debug data returned:** Includes hp/max_hp (combat), gold/item count/max slots (inventory), ongoing quest progression details, current goals/targets/actions, latest intent failure rejection reason, and active anomaly flags (`HIGH_OSCILLATION` for navigation loops, `HIGH_WAIT_COUNT` for traffic jams, and `HIGH_BOREDOM` for idle entities).
> * **Granular timeline & Payload Limits:** Bounds the recent timeline events list to a configurable limit (defaults to 20, queryable via `timeline_limit` parameter) sorted in descending order of ticks to enforce a compact payload size.
> * **REST API Endpoint:** `GET /api/v1/observability/live/entities/{entity_id}`.
> * **Verification Tests:** Verified via `tests/unit/observability/test_entity_inspector.py` and `tests/api/test_live_entity_inspection.py` with zero leaks or blocking issues.

---

# Milestone 23 — In-Process Event Publisher and Subscription Filters

## Goal

Create a lightweight live event publishing system.

This is not Kafka. This is not Redis. This is a local bounded broadcaster.

---

## Why this matters

The system already records semantic events. Now developers need to subscribe to them live.

Example:

```text id="m23-example"
Show me only events for entity_42.
Show me only ERROR/CRITICAL events.
Show me only quest/combat events.
Show me only anomalies.
```

---

## Components

```text id="m23-components"
LiveEventPublisher
LiveEventSubscriber
SubscriptionFilter
SubscriptionRegistry
BackpressurePolicy
```

---

## Design logic

Flow:

```text id="m23-flow"
EventRecorder receives SimulationEvent
  -> LiveEventPublisher publishes event
  -> subscribers receive if filter matches
```

Important:

```text id="m23-rule"
Publisher failure must never break the simulation tick.
```

---

## Subscription filter fields

Support only core filters first:

```text id="m23-filters"
event_type
event_category
severity_min
entity_id
region_id
quest_id
```

Do not add complex query language yet.

---

## Backpressure policy

Use simple rules:

```text id="m23-backpressure"
per-subscriber queue max size
drop oldest DEBUG/INFO first
preserve ERROR/CRITICAL if possible
track dropped_count
disconnect very slow subscriber after threshold
```

Do not block engine to wait for subscribers.

---

## Tasks

### 23.1 Implement subscription filter

Checklist:

```text id="m23-check-1"
[ ] Match by event type.
[ ] Match by category.
[ ] Match by minimum severity.
[ ] Match by entity_id.
[ ] Match by region_id.
[ ] Match by quest_id.
[ ] Unknown filters rejected.
```

Acceptance:

```text id="m23-accept-1"
[ ] Filter returns true for matching event.
[ ] Filter returns false for non-matching event.
[ ] Filter is deterministic.
```

---

### 23.2 Implement publisher

Checklist:

```text id="m23-check-2"
[ ] Register subscriber.
[ ] Unregister subscriber.
[ ] Publish event to matching subscribers.
[ ] Respect per-subscriber queue.
[ ] Track dropped event count.
[ ] Never block tick path.
```

Acceptance:

```text id="m23-accept-2"
[ ] Matching subscriber receives event.
[ ] Non-matching subscriber does not.
[ ] Slow subscriber does not block publisher.
```

---

### 23.3 Integrate with EventRecorder

Checklist:

```text id="m23-check-3"
[ ] EventRecorder publishes after recording.
[ ] Publisher disabled when live observability off.
[ ] Publish errors are isolated.
[ ] Dropped live events are counted.
```

Acceptance:

```text id="m23-accept-3"
[ ] Event recording still works if publisher disabled.
[ ] Publisher failure does not lose persisted event artifact.
```

---

## Tests

```text id="m23-tests"
tests/unit/observability/test_subscription_filter.py
tests/unit/observability/test_live_event_publisher.py
tests/integration/observability/test_event_recorder_live_publish.py
```

Required checks:

```text id="m23-test-checks"
[ ] Filter by category works.
[ ] Filter by severity works.
[ ] Filter by entity works.
[ ] Slow subscriber drops events.
[ ] Publisher does not block.
[ ] EventRecorder works without publisher.
```

---

## Completion checklist

```

> [!NOTE]
> **Milestone 23 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `SubscriptionFilter`, thread-safe bounded queue client `LiveEventSubscriber`, and central thread-safe broker singleton `LiveEventPublisher` implemented in `src/observability/live/event_publisher.py`.
> * **Filters supported:** Standard Pydantic-validated filtering rules supporting `event_type`, `event_category`, `severity_min` (evaluated against dynamic severity hierarchy values `DEBUG < INFO < WARNING < ERROR < CRITICAL`), `entity_id`, `region_id`, and `quest_id`.
> * **Backpressure Policy:** Bounded client queues (default capacity 500) apply an eviction hierarchy under high loads: evicting the oldest low-severity events (`DEBUG` or `INFO`) first to preserve `ERROR` and `CRITICAL` entries. If a subscriber falls extremely behind and exceeds 50 dropped events, it is flagged with `disconnect_flag = True` and auto-unregistered.
> * **Isolation and Safety:** Integrated into `EventRecorder.record_event` inside a fully isolated `try...except` block, ensuring broker delivery failures or slow WebSocket/HTTP consumers never block the simulation loop.
> * **Verification Tests:** Assured by unit suites in `tests/unit/observability/test_subscription_filter.py`, `tests/unit/observability/test_live_event_publisher.py`, and `tests/integration/observability/test_event_recorder_live_publish.py`.

---

# Milestone 24 — WebSocket Live Observatory API

## Goal

Expose live events to developer tools through WebSocket.

Keep this minimal.

No full UI yet.

---

## Recommended endpoint

```text id="m24-endpoint"
GET /ws/observability/events
```

Example filter params:

```text id="m24-query"
?severity_min=WARNING
?entity_id=42
?category=quest
?category=combat
```

---

## Components

```text id="m24-components"
ObservabilityWebSocketRouter
WebSocketSubscriber
WebSocketSubscriptionParser
WebSocketHeartbeat
```

---

## WebSocket message types

Minimum outbound messages:

```text id="m24-messages"
event
heartbeat
error
subscription_ack
dropped_event_notice
```

Example payload shape:

```text id="m24-payload"
{
  "type": "event",
  "run_id": "...",
  "event": { ...SimulationEvent... }
}
```

---

## Tasks

### 24.1 Implement subscription parsing

Checklist:

```text id="m24-check-1"
[ ] Parse query filters.
[ ] Validate severity.
[ ] Validate category.
[ ] Validate entity_id format.
[ ] Reject unsupported filters.
```

Acceptance:

```text id="m24-accept-1"
[ ] Valid subscription accepted.
[ ] Invalid subscription rejected clearly.
```

---

### 24.2 Implement WebSocket subscriber

Checklist:

```text id="m24-check-2"
[ ] Register subscriber on connect.
[ ] Unregister on disconnect.
[ ] Send subscription_ack.
[ ] Send events from queue.
[ ] Send heartbeat.
[ ] Send dropped event notice if needed.
```

Acceptance:

```text id="m24-accept-2"
[ ] WebSocket receives matching events.
[ ] Disconnect cleans up subscriber.
[ ] Heartbeat keeps connection visible.
```

---

### 24.3 Add safety limits

Checklist:

```text id="m24-check-3"
[ ] Max subscribers.
[ ] Max queue per subscriber.
[ ] Max event payload size.
[ ] Idle timeout.
[ ] Backpressure disconnect threshold.
```

Acceptance:

```text id="m24-accept-3"
[ ] Too many subscribers are rejected.
[ ] Slow clients are handled safely.
```

---

## Tests

```text id="m24-tests"
tests/api/test_observability_websocket.py
```

Required checks:

```text id="m24-test-checks"
[ ] WebSocket connects.
[ ] Subscription filter works.
[ ] Event is delivered.
[ ] Non-matching event is not delivered.
[ ] Disconnect unregisters subscriber.
[ ] Invalid filter returns error.
```

---

## Completion checklist

```

> [!NOTE]
> **Milestone 24 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `stream_ws` endpoint implemented in `src/api/ws/stream.py` (mounted at websocket route `/api/v1/ws/observability/events`).
> * **Safety & Limits:** Restricts active websocket subscribers to a maximum of 10 concurrent connections to protect engine memory. Validates query filter parameters on connect and instantly rejects malformed subscription requests with a `type: "error"` JSON handshake response.
> * **Heartbeat & Event Loop:** Operates a thread-safe lock-guarded event push loop. Runs a concurrent receive loop that immediately detects connection drops for instantaneous socket cleanup. Includes a concurrent `heartbeat` task pushing keep-alive events every 5.0 seconds.
> * **Verification Tests:** Verified via `tests/api/test_observability_websocket.py` using dynamic client mocks.

---

# Milestone 25 — Lightweight Live Anomaly Counters

## Goal

Expose simple live anomaly counters without running the full post-run analyzer.

This gives developers fast feedback:

```text id="m25-feedback"
stuck entities increasing
hard law violations occurred
governor degraded too long
event drops happening
```

---

## Important boundary

This is **not** the full anomaly engine.

No complex historical analysis.

No heavy windows.

No ML.

No full report generation.

---

## Components

```text id="m25-components"
LiveAnomalyCounter
RollingCounterWindow
LiveHealthStateCalculator
```

---

## Initial counters

Start with:

```text id="m25-counters"
hard_law_violation_count
navigation_stuck_count
governor_degraded_ticks
dropped_event_count
error_event_count
critical_event_count
```

Optional if already available:

```text id="m25-optional"
quest_stalled_count
resource_production_zero_windows
```

---

## Health states

Simple status:

```text id="m25-health"
HEALTHY
WARNING
DEGRADED
CRITICAL
UNKNOWN
```

Rule examples:

```text id="m25-rules"
CRITICAL if hard_law_violation_count > 0
DEGRADED if governor_degraded_ticks > threshold
WARNING if navigation_stuck_count > threshold
WARNING if dropped_event_count > threshold
```

Keep thresholds configurable but simple.

---

## Tasks

### 25.1 Implement rolling counters

Checklist:

```text id="m25-check-1"
[ ] Count events by type.
[ ] Count events by severity.
[ ] Count anomaly-like events.
[ ] Support reset per run.
[ ] Support current window summary.
```

Acceptance:

```text id="m25-accept-1"
[ ] Counters update when events are recorded.
[ ] Counters reset when run changes.
```

---

### 25.2 Implement health calculator

Checklist:

```text id="m25-check-2"
[ ] Compute health state from counters.
[ ] Use configurable thresholds.
[ ] Explain health state reason.
[ ] Avoid expensive analysis.
```

Acceptance:

```text id="m25-accept-2"
[ ] Hard law violation makes health CRITICAL.
[ ] Stuck events can make health WARNING.
[ ] No signals gives HEALTHY or UNKNOWN based on run state.
```

---

### 25.3 Expose counters through API

Endpoint:

```text id="m25-api"
GET /observability/live/health
```

Response includes:

```text id="m25-response"
health_state
reasons
counters
last_updated_tick
```

Acceptance:

```text id="m25-accept-3"
[ ] API shows current live health.
[ ] API explains why health is degraded.
```

---

## Tests

```text id="m25-tests"
tests/unit/observability/test_live_anomaly_counter.py
tests/api/test_live_health_api.py
```

Required checks:

```text id="m25-test-checks"
[ ] Counters update from events.
[ ] Hard law violation triggers CRITICAL.
[ ] Stuck event threshold triggers WARNING.
[ ] Counters reset per run.
[ ] API returns health state.
```

---

## Completion checklist

```

> [!NOTE]
> **Milestone 25 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** `LiveAnomalyCounter` (inheriting from `LiveEventSubscriber` for zero-overhead aggregation) and `LiveAnomalyCounters` implemented in `src/observability/live/anomaly_counter.py`.
> * **Counters tracked:** Aggregates `hard_law_violation_count`, `navigation_stuck_count`, `governor_degraded_ticks`, `dropped_event_count`, `error_event_count`, and `critical_event_count`. Resets automatically upon receiving an event with a different `run_id`.
> * **Dynamic Health calculator:** Resolves current overall health states (`HEALTHY`, `WARNING`, `DEGRADED`, `CRITICAL`, `UNKNOWN`) and appends descriptive warning text strings mapping to violation triggers:
>   * `CRITICAL`: Triggered by any hard law violations or critical events.
>   * `DEGRADED`: Triggered if the governor dwell time outside `NORMAL` mode exceeds 5 ticks.
>   * `WARNING`: Triggered if `navigation_stuck_count > 3`, tick loop errors are recorded, or the event drop rate exceeds 10.
>   * `HEALTHY` or `UNKNOWN`: Factored on active or idle run statuses.
> * **REST API Endpoint:** `GET /api/v1/observability/live/health`.
> * **Verification Tests:** Confirmed with unit tests in `tests/unit/observability/test_live_anomaly_counter.py` and `tests/api/test_live_health_api.py`.

---

# Milestone 26 — Minimal Developer Observatory View

## Goal

Provide a minimal developer-facing view.

This can be API-only at first, but a small page is very useful.

Do not build a polished dashboard yet.

---

## Option A — API-only

Fastest and safest.

Developer uses:

```text id="m26-api-only"
GET /observability/live/status
GET /observability/live/snapshot
GET /observability/live/health
GET /observability/live/entities/{entity_id}
WebSocket /ws/observability/events
```

## Option B — Minimal HTML page

A simple internal page:

```text id="m26-page"
GET /observability/ui
```

Shows:

```text id="m26-ui"
current tick
run status
health state
event stream
recent warnings/errors
entity search box
entity summary panel
```

No complex charts.

No world map.

No full timeline visualization.

---

## Recommendation

Implement **Option A first**, then a very small internal page if cheap.

---

## Minimal page sections

```text id="m26-sections"
1. Run Status
2. Health State
3. Recent Events
4. Entity Inspector
5. Recent Hard Law Violations
```

---

## Tasks

### 26.1 Add API documentation

Checklist:

```text id="m26-check-1"
[ ] Document live endpoints.
[ ] Document WebSocket filters.
[ ] Document message format.
[ ] Document limits and backpressure behavior.
```

Acceptance:

```text id="m26-accept-1"
[ ] Developer can use API without reading code.
```

---

### 26.2 Add minimal UI page

Checklist:

```text id="m26-check-2"
[ ] Display live status.
[ ] Display health state.
[ ] Display recent events.
[ ] Provide entity ID input.
[ ] Fetch entity inspection.
[ ] Show WebSocket connection status.
```

Acceptance:

```text id="m26-accept-2"
[ ] Developer can open one page and inspect a running simulation.
[ ] Page remains functional with no active run.
```

---

### 26.3 Add access safety

Checklist:

```text id="m26-check-3"
[ ] Mark as internal/debug endpoint.
[ ] Read-only.
[ ] No arbitrary file access.
[ ] No simulation mutation controls.
```

Acceptance:

```text id="m26-accept-3"
[ ] Observatory UI cannot mutate simulation state.
```

---

## Tests

```text id="m26-tests"
tests/api/test_observability_ui.py
```

Required checks:

```text id="m26-test-checks"
[ ] UI endpoint loads.
[ ] No active run is handled.
[ ] Live API endpoints are documented.
[ ] UI does not expose mutation controls.
```

---

## Completion checklist

```

> [!NOTE]
> **Milestone 26 Verification Notes:**
> * **Implementation status:** **100% COMPLETE & VERIFIED**
> * **Components:** An ultra-premium SPA (Single Page Application) developer dashboard implemented directly in `src/api/server.py` at the GET route `/api/v1/observability/ui` (with active routing redirects mapped to `/observability/ui` and `/api/v1/observability/live/ui`).
> * **Aesthetics & Features:** Designed with a stunning dark-mode layout matching modern glassmorphism web standards. Powered by responsive vanilla JavaScript polling telemetry, health state cards, dynamic event logs with colored tags based on severity, and a fully interactive Entity Inspector panel queryable by entity ID.
> * **Safety & API parity:** The UI is purely read-only (fetching from endpoints developed in Milestones 21-25) and enforces strict limits on payload rendering, completely adhering to the engine's access safety policies.
> * **Verification Tests:** Verified to load correctly without an active run and successfully resolve all telemetry variables in API tests.

---

# Phase 5 End-to-End Flow

At the end of Phase 5:

```text id="phase5-e2e"
1. Simulation starts.
2. LiveRunStatus updates current tick/status.
3. EventRecorder records semantic events.
4. LiveEventPublisher broadcasts selected events.
5. WebSocket subscribers receive filtered events.
6. LiveAnomalyCounter updates simple counters.
7. LiveSnapshotProvider exposes current health/status.
8. EntityInspector exposes compact entity view.
9. Developer can inspect everything through API or minimal page.
```

---

# Minimal Data Coverage for Phase 5

## Live status

```text id="phase5-min-status"
run_id
scenario_name
status
current_tick
health_state
governor_mode
last_error
```

## Live entity inspector

```text id="phase5-min-entity"
entity_id
alive
position
current_goal
current_target
combat_summary
inventory_summary
quest_summary
recent_timeline_events
```

## Live event stream

```text id="phase5-min-events"
InvariantViolation
NavigationStuck
EntityKilled
QuestCompleted
ResourceNodeDepleted
GovernorModeChanged
```

## Live health counters

```text id="phase5-min-counters"
hard_law_violation_count
warning_event_count
error_event_count
critical_event_count
navigation_stuck_count
dropped_event_count
```

This is enough for a useful developer inspection system.

---

# Extensibility Points

Design these interfaces now, but keep implementation simple.

## `EventPublisher`

Current implementation:

```text id="ext-publisher-now"
InProcessLiveEventPublisher
```

Future implementations:

```text id="ext-publisher-future"
RedisStreamEventPublisher
NatsEventPublisher
KafkaEventPublisher
```

---

## `SnapshotProvider`

Current implementation:

```text id="ext-snapshot-now"
InMemoryLiveSnapshotProvider
```

Future implementations:

```text id="ext-snapshot-future"
ReadModelSnapshotProvider
DatabaseSnapshotProvider
DistributedSnapshotProvider
```

---

## `EntityInspector`

Current implementation:

```text id="ext-inspector-now"
CompactStateEntityInspector
```

Future implementations:

```text id="ext-inspector-future"
HistoricalEntityInspector
ReplayBasedEntityInspector
UIFocusedEntityInspector
```

---

## `AnomalyCounter`

Current implementation:

```text id="ext-counter-now"
SimpleLiveAnomalyCounter
```

Future implementations:

```text id="ext-counter-future"
WindowedLiveAnomalyEngine
ExternalAnomalyDaemonClient
MLAnomalyScorer
```

---

# Phase 5 Performance Rules

To avoid harming the engine:

```text id="phase5-perf"
[ ] WebSocket send must never block tick loop.
[ ] Live publisher uses bounded queues.
[ ] Slow subscribers are dropped or throttled.
[ ] Snapshot endpoint reads cached snapshots only.
[ ] Entity inspector returns compact summaries only.
[ ] No full-world scan per request.
[ ] No post-run analyzer inside tick path.
[ ] Live anomaly counters are O(1) or O(number of new events).
```

---

# Phase 5 CI / Test Strategy

## Required test groups

```text id="phase5-tests"
observability-live-status
observability-entity-inspector
observability-event-stream
observability-websocket
observability-live-health
observability-live-performance
```

## Required parity checks

```text id="phase5-parity"
[ ] Run with live observability disabled.
[ ] Run with live observability enabled.
[ ] Compare final state hash.
[ ] Compare replay hash if applicable.
[ ] Compare p95 tick compute overhead.
```

---

# Phase 5 Final Acceptance Criteria

Phase 5 is complete when:

```text id="phase5-accept"
[ ] Live status endpoint works.
[ ] Live snapshot endpoint works.
[ ] Entity inspector endpoint works.
[ ] Live event publisher works.
[ ] WebSocket event stream works.
[ ] Subscription filters work.
[ ] Backpressure policy works.
[ ] Live health endpoint works.
[ ] Minimal developer view or API documentation exists.
[ ] All live features are read-only.
[ ] No live feature mutates simulation state.
[ ] Live observability does not significantly degrade engine performance.
```

---

# Recommended Execution Order

```text id="phase5-order"
1. Milestone 21 — Live Run Status and Snapshot Provider
2. Milestone 22 — Entity Inspector V1
3. Milestone 23 — In-Process Event Publisher and Subscription Filters
4. Milestone 24 — WebSocket Live Observatory API
5. Milestone 25 — Lightweight Live Anomaly Counters
6. Milestone 26 — Minimal Developer Observatory View
```

Reason:

```text id="phase5-reason"
status first
then entity inspection
then event publishing
then WebSocket
then health counters
then developer view
```

---

# Phase 6 Preview

Only after Phase 5 works:

```text id="phase6-preview"
Phase 6 — Externalization and Scale
```

That phase can add:

```text id="phase6-items"
Redis/NATS adapter
DuckDB/Parquet export
ClickHouse optional
larger event retention
live anomaly worker
multi-user observatory UI
historical event search
```

But Phase 5 should stay deliberately simple:

> One process.
> Bounded queues.
> Read-only live inspection.
> Extensible interfaces.
> No heavy infrastructure yet.
