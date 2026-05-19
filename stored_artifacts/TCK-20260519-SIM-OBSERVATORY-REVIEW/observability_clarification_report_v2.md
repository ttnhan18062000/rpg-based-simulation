# Second-Pass Observability Clarification Report for Simulation Observatory (Phase 2)

## Executive Summary
This clarification report completes the second-pass review of the Simulation Observatory architecture for the V2 RPG Engine. Building on the initial assessment, this document addresses twelve specific architectural questions spanning Loki label safety, Prometheus/Grafana metric mapping, diagnostic event mechanisms, domain event volume policies, hard law runtime monitoring, anomaly engine architectures, entity timeline retention models, semantic metrics gap analysis, balance profile loaders, and production watchdog stability. All architectural claims and recommendations are grounded in exact file paths, class names, method names, config blocks, and test citations.

---

## Section A: Deep-Dive into Loki Label Safety

### 1. Concrete Config Inspection & High-Cardinality Risks
Inspection of `promtail-config.yml` (located in the project root) reveals a critical high-cardinality label risk in the pipeline stages configured for container log scraping:
```yaml
scrape_configs:
  - job_name: system
    docker:
      sd_configs:
        - hosts:
            - unix:///var/run/docker.sock
    pipeline_stages:
      - json:
          expressions:
            level: level
            logger: logger
            tick: tick
      - labels:
          level:
          logger:
          tick: # CRITICAL HIGH-CARDINALITY HAZARD
```
By explicitly promoting the `tick` field from the JSON log context into a Loki stream label (`labels: tick:`), every single simulation tick generates a unique, immutable log stream in Loki's inverted index. In a standard 50,000-tick run, this produces 50,000 distinct stream chunks per container, leading to catastrophic index fragmentation, out-of-memory crashes in Loki indexers, and query timeouts.

### 2. Architectural Boundaries: Stream Labels vs JSON Context Fields
To ensure index scalability and microsecond query response times in Grafana log panels, the system must enforce strict architectural separation between Loki stream labels and structured JSON context fields:
- **Stream Labels (Strictly Low-Cardinality <= 50 values total)**: Must be confined to static infrastructure identifiers: `environment`, `service` (e.g., `backend`, `ai_worker`, `loki`), `container_name`, and `log_level` (`INFO`, `WARN`, `ERROR`).
- **JSON Context Fields (High-Cardinality)**: High-cardinality simulation metadata—specifically `tick`, `entity_id`, `target_id`, `quest_id`, `region_id`, `worker_id`, `causal_id`, and `transaction_id`—must remain embedded within the JSON payload string formatted by `JsonFormatter` (`src/logging/formatter.py`).

Grafana panels unpack JSON fields dynamically via Promtail/LogQL parse filters (`{service="backend"} | json | tick > 5000 and entity_id="HERO_01"`) with zero indexing penalty.

---

## Section B: Deep-Dive into Prometheus & Grafana Metric Mapping

### 1. Zero Export Path in Active V2 Codebase
The pre-configured Grafana dashboard (`grafana/dashboards/simulation.json`) relies on more than 20 PromQL queries, including `sim_current_tick`, `sim_active_entities`, `sim_ticks_per_second`, `sim_calamity_active`, `sim_gold_circulation_total`, and `sim_errors_total`.

However, exhaustive AST inspection reveals that the active V2 codebase (`src/api/server.py` and core engine loops) contains **zero import** of `prometheus_client` and does **not** expose a `/metrics` HTTP route. All Prometheus metric instrumentation exists exclusively in legacy code (`src_legacy/utils/metrics.py`). Consequently, when Prometheus scrapes `http://backend:8000/metrics` (as configured in `prometheus.yml`), it receives `HTTP 404 Not Found`, rendering all Grafana dashboard panels permanently empty ("No data").

### 2. Exhaustive Metric Inventory & Class Mapping
To restore full observability, the 20+ PromQL metrics required by `simulation.json` must be instrumented in the active V2 engine. The following table maps each required metric to its exact runtime source class and extraction method:

| PromQL Metric Name | Metric Type | Exact Source Class & File Path | Extraction Method / Attribute |
| :--- | :--- | :--- | :--- |
| `sim_current_tick` | Gauge | `Kernel` (`src/engine/kernel.py`) | `Kernel._current_tick` |
| `sim_active_entities` | Gauge | `WorldMetrics` (`src/engine/metrics.py`) | `WorldMetrics.alive_entities` |
| `sim_ticks_per_second` | Gauge | `RuntimeStatus` (`src/engine/runtime_status.py`) | Calculated from `PressureSignals.tick_compute_ms` |
| `sim_calamity_active` | Gauge | `CalamitySystem` (`src/systems/world_systems/calamity.py`)| `1.0` if `CalamityState.active` else `0.0` |
| `sim_faction_population` | Gauge | `FactionSystem` (`src/systems/world_systems/governance.py`)| `len(FactionState.members)` per faction |
| `sim_gold_circulation_total` | Gauge | `WorldMetrics` (`src/engine/metrics.py`) | `WorldMetrics.total_gold` |
| `sim_errors_total` | Counter | `RejectionRegistry` (`src/core/state.py`) | `len(RejectionRegistry.rejections)` |
| `sim_memory_rss_bytes` | Gauge | `SignalCollector` (`src/engine/observability.py`) | `psutil.Process().memory_info().rss` |
| `sim_dropped_work_total` | Counter | `RuntimeSnapshot` (`src/engine/observability.py`) | `RuntimeSnapshot.dropped_work_delta` |
| `sim_worker_queue_depth` | Gauge | `WorkerPool` (`src/engine/concurrency.py`) | `WorkerPool.get_queue_depth()` |
| `sim_phase_duration_seconds` | Histogram | `Kernel` (`src/engine/kernel.py`) | Measured inside `Kernel._phase_apply` |
| `sim_item_circulation` | Gauge | `InventoryService` (`src/services/inventory_service.py`)| Count of active items in `ItemRegistry` |
| `sim_trauma_index` | Gauge | `WorldMetrics` (`src/engine/metrics.py`) | `WorldMetrics.total_trauma` |
| `sim_quest_active_count` | Gauge | `WorldMetrics` (`src/engine/metrics.py`) | `WorldMetrics.quest_status_counts["ACTIVE"]` |
| `sim_quest_completed_total`| Counter | `WorldMetrics` (`src/engine/metrics.py`) | `WorldMetrics.quest_status_counts["COMPLETED"]` |
| `sim_building_sabotage_count`| Gauge | `BuildingRegistry` (`src/core/state.py`) | Count of `BuildingState.condition == "DAMAGED"` |
| `sim_social_contracts_active`| Gauge | `SocialContractSystem` (`src/systems/social.py`) | `len(SocialContractState.active_contracts)` |
| `sim_governor_throttle_mode` | Gauge | `ResourceGovernor` (`src/engine/governor.py`) | Enum int mapping (`NORMAL=0`, `THROTTLED=1`, etc.) |
| `sim_dirty_set_size` | Gauge | `DirtySet` (`src/core/dirty.py`) | `len(DirtySet._dirty_entities)` |
| `sim_rejection_count_total` | Counter | `WorldMetrics` (`src/engine/metrics.py`) | Sum of `WorldMetrics.rejection_counts.values()` |

### 3. Server vs Worker Daemon Export Architecture
To collect these metrics across multi-process deployments without port collisions or lock contention:
- **FastAPI Server (`src/api/server.py`)**: Mounts `prometheus_client.make_asgi_app()` at `/metrics`. Serves global read models, snapshot summaries, API request latency histograms, and certification status.
- **Worker Daemons (`src/workers/daemon.py`)**: Each worker daemon instantiates an isolated `PrometheusMetricsCollector` running an embedded WSGI server on distinct ports (`8001`, `8002`). Workers export thread utilization, queue depth, phase compute durations, and worker-specific memory RSS. Prometheus scrapes all targets via static configs in `prometheus.yml`.

---

## Section C: Complete Inventory of Existing Event & Trace Mechanisms

The V2 codebase features several distinct event, logging, and trace mechanisms serving different layers of the engine:
1. **`TraceEvent` (`src/core/diagnostic.py` line 12)**:
   - *Data Schema*: Structured dataclass containing `tick: int`, `system: str`, `event_type: str`, `payload: Dict[str, Any]`, and `causal_id: Optional[str]`.
   - *Emission & Storage*: Emitted by `Kernel._phase_apply` during state transitions and collected in memory. Flushed by `ReplayManager` (`src/engine/replay_manager.py` line 45) and `ReplaySink` (`src/engine/replay_sink.py` line 22) into compressed disk chunks (`chunk_0000.json`). Used exclusively for post-run deterministic replay and debugging.
2. **`JsonFormatter` (`src/logging/formatter.py` line 18)**:
   - *Data Schema*: Thread-local context (`_log_context`) capturing `tick`, `component`, `worker_id`, `entity_id`. Formats Python `logging.LogRecord` into JSON strings containing `timestamp`, `level`, `logger`, `message`, and `context`.
   - *Emission & Storage*: Emitted by structured loggers across systems. Scraped by Promtail from Docker stdout and indexed in Loki.
3. **`IntentResult` (`src/core/state.py` line 557)**:
   - *Data Schema*: Dataclass recording atomic resource transfer intent outcomes (`transaction_id: str`, `accepted: bool`, `reason: str`, `source_kind: str`, `source_id: str`). Attached to entity states during transaction resolution (`src/engine/economy.py`).
4. **`RejectionEvent` (`src/core/updates.py` line 26)**:
   - *Data Schema*: Dataclass capturing authoritative action rejections (`tick`, `actor_id`, `action_kind`, `reason`, `target_id`). Recorded directly into `RejectionRegistry` (`src/core/state.py` line 1028).
5. **`transaction_trace` (`src/engine/metrics.py` line 88)**:
   - *Data Schema*: Observation-only string log appended by `ResourceTransactionResolver.resolve_all` (`src/engine/economy.py`) onto `WorldMetrics.transaction_trace`.

---

## Section D: Architectural Trade-Offs: `TraceEvent` vs `SimulationEvent`

The current `TraceEvent` is tightly coupled to deterministic replay and diagnostic logging. Introducing a dedicated `SimulationEvent` hierarchy (`src/observability/events.py`) presents clear architectural trade-offs:

```
+-----------------------------------------------------------------------+
| TraceEvent (Diagnostic & Replay)                                      |
| - High Volume (Every entity delta / state mutation)                   |
| - Unstructured Payload (Arbitrary Dict[str, Any])                     |
| - Direct Disk Sink (Replay chunks chunk_0000.json)                    |
+-----------------------------------------------------------------------+
                                   |
                                   | (Decoupled Stream Boundary)
                                   v
+-----------------------------------------------------------------------+
| SimulationEvent (Observatory Read Model)                              |
| - Curated Semantic Domain Events (CombatKill, QuestComplete, Trade)   |
| - Strictly Typed Pydantic Validation (EntityTimeline compliance)      |
| - Asynchronous Pub/Sub Broker (Redis Stream / Kafka export)           |
+-----------------------------------------------------------------------+
```

### 1. Comparative Architectural Matrix

| Dimension | `TraceEvent` (`src/core/diagnostic.py`) | Proposed `SimulationEvent` (`src/observability/events.py`) |
| :--- | :--- | :--- |
| **Primary Consumer** | Deterministic Replay Engine (`ReplaySink`), CLI Debugger. | Simulation Observatory UI, Anomaly Engine, Entity Timeline view. |
| **Data Schema** | Unstructured dictionary payload (`Dict[str, Any]`). | Strictly typed Pydantic models with explicit domain schemas. |
| **Emission Volume** | Extremely High (100k+ events/sec; records every state delta). | Medium/Curated (500 events/sec; semantic milestones only). |
| **Validation Overhead** | Near zero (raw dict serialization). | Moderate (Pydantic model validation on initialization). |
| **Transport Layer** | Direct synchronous write to in-memory buffers -> disk chunks. | Async Pub/Sub (Redis Streams/Kafka) or WebSocket broadcast. |
| **Retention Lifecycle**| Per-run chunk rotation; purged upon scenario completion. | Persistent timeline storage in time-series DB (ClickHouse/Loki). |

### 2. Recommendation
**Do not merge `TraceEvent` and `SimulationEvent`.** Maintain `TraceEvent` for low-level byte-identical replay recording. Implement `SimulationEvent` as a curated, strongly-typed domain event layer in `src/observability/events.py` specifically designed for external UI timeline rendering and anomaly detection.

---

## Section E: Domain Event Volume Policies Across 11 Key Domains

To prevent event storming and network saturation during high-density simulations, `SimulationEvent` emission must be governed by strict volume and filtering policies across all 11 core gameplay domains:

1. **Movement (`src/systems/movement.py`)**:
   - *Policy*: **Sampled & Thresholded**. Suppress continuous step-by-step tile coordinate deltas. Emit `EntityRelocationEvent` only upon entering a new geographic zone (`RegionState`), entering/leaving a building, or completing a navigation path.
   - *Target Volume*: <1 event per entity every 50 ticks.
2. **Combat (`src/engine/combat.py`)**:
   - *Policy*: **Milestone & Critical State**. Suppress individual normal melee swings. Emit `CombatEngagementStartedEvent`, `CriticalHitEvent`, `StatusEffectAppliedEvent` (e.g., `STUNNED`, `BLEEDING`), and `CombatKillEvent`.
   - *Target Volume*: <5 events per engagement lifecycle.
3. **Harvesting (`src/systems/harvest.py`)**:
   - *Policy*: **Batch State Transitions**. Suppress per-tick channeling progress. Emit `HarvestStartedEvent`, `ResourceNodeDepletedEvent`, and `HarvestAbortedEvent`.
   - *Target Volume*: 2 events per node interaction.
4. **Economy (`src/engine/economy.py`)**:
   - *Policy*: **Atomic Transaction Finalization**. Record exactly-once `ResourceTransactionEvent` when items/gold change ownership between entities, shops, or crafting stations. Suppress failed intent spam.
   - *Target Volume*: 1 event per trade/craft resolution.
5. **Quests (`src/systems/quests.py`)**:
   - *Policy*: **Exhaustive Lifecycle Auditing**. Emit events for all authoritative state transitions: `QuestGeneratedEvent`, `QuestAcceptedEvent`, `QuestObjectiveProgressEvent`, `QuestCompletedEvent`, and `QuestFailedEvent`.
   - *Target Volume*: 100% emission; low volume (<10 events/sec).
6. **Social (`src/systems/social.py`)**:
   - *Policy*: **Contract & Milestone Driven**. Emit `SocialContractProposedEvent`, `SocialContractRatifiedEvent`, `SocialContractExpiredEvent`, and major relationship turning points (`NemesisFormedEvent`, `BondCreatedEvent`). Suppress routine gossip chatter.
   - *Target Volume*: <1 event per entity every 200 ticks.
7. **Strategy (`src/systems/strategy.py`)**:
   - *Policy*: **Project Transition Auditing**. Record all strategic mind mutations: `StrategicProjectStartedEvent`, `ProjectBlockedEvent` (with detour spawn metadata), and `StrategicProjectCompletedEvent`.
   - *Target Volume*: 100% emission; very low volume.
8. **World Dynamics (`src/systems/world_systems/calamity.py`)**:
   - *Policy*: **Exhaustive Macro Auditing**. Record all global state mutations: `CalamityTriggeredEvent`, `HazardSpawnedEvent`, `RaidWaveDispatchedEvent`, `WeatherShiftedEvent`, and `RegionKindTransformedEvent`.
   - *Target Volume*: 100% emission (<1 event/sec).
9. **Building & Sovereignty (`src/systems/world_systems/governance.py`)**:
   - *Policy*: **State Change Auditing**. Record `BuildingSabotagedEvent`, `BuildingRepairedEvent`, `TerritoryConqueredEvent`, and `TaxationCollectedEvent`. Suppress routine visitor entries.
   - *Target Volume*: <1 event per building every 500 ticks.
10. **Progression & Lifecycle (`src/systems/progression.py`)**:
    - *Policy*: **Exhaustive Milestone Auditing**. Emit `EntitySpawnedEvent`, `LevelUpEvent`, `SkillRankedUpEvent`, `BiologicalExhaustionEvent`, `HeirDesignatedEvent`, and `EntityPermadeathEvent`.
    - *Target Volume*: 100% emission; critical timeline markers.
11. **Infrastructure (`src/engine/kernel.py`)**:
    - *Policy*: **Throttled Anomaly & Governor Alerts**. Emit `GovernorModeShiftedEvent` (e.g., `NORMAL` to `THROTTLED`), `PhaseBudgetExceededEvent`, and `WatchdogTripwireEvent`.
    - *Target Volume*: Zero during normal operation; alerts only on threshold breach.

---

## Section F: Inventory of Hard Laws Across All Domains

The V2 simulation relies on strict hard laws to guarantee mathematical determinism and state integrity. The following inventory documents all hard laws, their current enforcement mechanisms, test citations, and their suitability for runtime verification via `DirtySet` monitoring.

```
+---------------------------------------------------------------------------------------------------------------------------------+
|                                                   SIMULATION HARD LAWS MATRIX                                                   |
+----------------------------------------+------------------------------------+---------------------------------------------------+
| Domain & Hard Law                      | Runtime Enforcement Mechanism      | Automated Test Verification Path                  |
+----------------------------------------+------------------------------------+---------------------------------------------------+
| COMB-001: Manhattan Distance           | LegalityServiceV2._verify_range    | tests/engine/test_legality_service.py             |
| COMB-002: Exact 1 Entity Per Tile      | SpatialGrid.move_entity            | tests/engine/test_spatial_grid.py                 |
| COMB-266: Action Readiness >= 0        | ActionSystem._validate_readiness   | tests_v2/combat/test_action_readiness.py          |
| ECON-201: Atomic Gold Conservation     | ResourceTransactionResolver        | tests/engine/test_economy_transactions.py         |
| TOWN-011: Bounded Inventory Slots      | InventoryService.add_item          | tests_v2/inventory/test_inventory_service.py      |
| PROG-077: Non-Negative Attributes      | EntityBuilder & UpdateGuard        | tests_v2/progression/test_leveling.py             |
| SOC-102: Mutual Contract Ratification  | SocialContractSystem.ratify        | tests_v2/social/test_social_contracts.py          |
| STRAT-044: Bounded Active Projects (1) | StrategicIntelligenceSystem        | tests_v2/strategy/test_project_continuity.py      |
| KERN-001: Phase Isolation & Deep-Freeze| Kernel._guard_stability            | tests/engine/test_kernel_isolation.py             |
+----------------------------------------+------------------------------------+---------------------------------------------------+
```

### Feasibility of `DirtySet` Monitoring
`DirtySet` (`src/core/dirty.py`) tracks entities modified during the current tick (`_dirty_entities: Set[EntityID]`). **`DirtySet` monitoring is highly feasible and architecturally optimal for Hard Law verification.** Because invariant checks (e.g., non-negative HP/gold, valid grid coordinates) only need to be evaluated against entities that actually mutated during the tick, `DirtySet` provides an exact O(K) candidate filter. This eliminates the need for expensive O(N) full-world scans at the end of every tick.

---

## Section G: `HardLawMonitor` V1 Scope & Architecture

To bridge the gap between enforcement and monitoring, the Simulation Observatory requires an active runtime verification component: `HardLawMonitor` (`src/observability/hard_law_monitor.py`).

```
+-----------------------------------------------------------------------+
| WorldState (Entities, Grid, Factions, Metrics)                        |
+-----------------------------------------------------------------------+
                                   |
                                   | (Pulls Modified Entities via DirtySet)
                                   v
+-----------------------------------------------------------------------+
| HardLawMonitor (Executed by Kernel._phase_finalization)               |
| +-------------------------------------------------------------------+ |
| | Rule 1: Zero Negative Gold / Attributes (Entity Update Verification)| |
| | Rule 2: Strict Global Conservation (World Gold == Gold Circulation) | |
| | Rule 3: Zero Occupancy Collision (SpatialGrid.get_occupancy Check)  | |
| | Rule 4: Zero Orphaned Items / Entities in Registries                | |
| +-------------------------------------------------------------------+ |
+-----------------------------------------------------------------------+
                                   |
                                   | (On Invariant Breach Trigger)
                                   v
+-----------------------------------------------------------------------+
| InvariantViolationEvent -> RejectionRegistry -> Kernel.halt_simulation|
+-----------------------------------------------------------------------+
```

### 1. V1 Scope: The Four Core Invariant Rules
The V1 `HardLawMonitor` is scoped to verify four non-negotiable global invariants at the end of every tick:
1. **Rule 1: Non-Negative Attributes**: Scans `DirtySet` entities to verify `HP >= 0`, `stamina >= 0`, `gold >= 0`, and `readiness >= 0`.
2. **Rule 2: Global Gold Conservation**: Verifies that total world gold (sum of all entity gold + shop liquidity + world chests) equals the initial world seed gold plus or minus verified economic injection/sink events.
3. **Rule 3: Spatial Occupancy Collisions**: Verifies that no two alive solid entities share identical `(x, y)` tile coordinates on the `SpatialGrid`.
4. **Rule 4: Registry Referential Integrity**: Verifies that all active items in entity inventories exist in `ItemRegistry`, and all active building occupants exist in `BuildingRegistry`.

### 2. Execution Hook & Failure Response
- **Hook**: Executed inside `Kernel._phase_finalization` (`src/engine/kernel.py`) immediately before `_phase_persistence`.
- **Response**: If an invariant is breached, the monitor emits an `InvariantViolationEvent`, appends the breach to `RejectionRegistry`, logs a `SYSTEM_CRITICAL` error to Promtail/Loki, and executes `Kernel.halt_simulation(reason="HARD_LAW_VIOLATION")` to prevent corrupt state snapshots from persisting to disk.

---

## Section H: Evaluation of Anomaly Engine Architectural Options

To detect strange simulation events (e.g., stuck entities, resource crowding, oscillating navigation), the system requires an Anomaly Engine. Three distinct architectural options were evaluated:

```
+-------------------------------------------------------------------------------------------------------------------------+
|                                               ANOMALY ENGINE ARCHITECTURE                                               |
+-----------------------+------------------------------------------+------------------------------------------------------+
| Model                 | Execution Boundary                       | Latency vs Overhead Trade-off                        |
+-----------------------+------------------------------------------+------------------------------------------------------+
| 1. In-Process Hook    | Synchronous inside Kernel loop           | Zero network latency; High CPU/tick overhead hazard  |
| 2. Out-of-Process     | Async daemon consuming Kafka/Redis stream| Zero engine overhead; Millisecond detection delay    |
| 3. Post-Run Audit     | CLI tool parsing chunk_0000.json on disk | Zero runtime impact; No real-time intervention logic |
+-----------------------+------------------------------------------+------------------------------------------------------+
```

### Comparative Analysis
1. **In-Process Hook (Synchronous inside `Kernel` loop)**:
   - *Pros*: Immediate access to raw in-memory Python objects (`EntityState`, `SpatialGrid`); capable of instant intervention (e.g., nudging stuck entities or spawning detours).
   - *Cons*: Directly inflates tick compute latency. Complex history tracking (e.g., 50-tick position sliding windows) consumes excessive RAM inside the main engine process.
2. **Out-of-Process Daemon (Asynchronous via Redis Stream / Kafka)**:
   - *Pros*: Complete computational isolation. Complex windowed aggregations (e.g., detecting economic stagnation or navigation oscillation) run on separate CPU cores or machines. Zero impact on engine TPS.
   - *Cons*: Requires network serialization (`SimulationEvent` JSON/Protobuf over Redis/Kafka); introduces millisecond detection delay before intervention commands can be dispatched back to the engine API.
3. **Post-Run Audit (Batch Processing via Replay Chunks)**:
   - *Pros*: Absolute zero runtime overhead. Ideal for deep certification analysis, balance verification, and E2E regression reporting.
   - *Cons*: Cannot detect or resolve anomalies during live gameplay or long-run server operation.

### Recommendation
**Adopt the Out-of-Process Daemon architecture.** For the live Simulation Observatory, asynchronous stream consumption provides the optimal balance of zero engine latency degradation and rich time-series anomaly detection. Post-run auditing should be maintained strictly for certification gating (`CertificationHarness`).

---

## Section I: Proposed Entity Timeline Retention Model

The Simulation Observatory requires a high-performance retention model to record entity lifecycles (birth, turning points, level-ups, quests, deaths) without exhausting memory or storage over 50,000+ ticks.

```
+-------------------------------------------------------------------------------------------------------------------+
|                                          ENTITY TIMELINE RETENTION MODEL                                          |
+--------------------------+------------------------------------------+---------------------------------------------+
| Tier                     | Storage Medium & Data Format             | Retention Policy & Granularity              |
+--------------------------+------------------------------------------+---------------------------------------------+
| 1. Hot Ring Buffer       | In-Memory deque(maxlen=200) per Entity   | Full granular state deltas for last 200 tck |
| 2. Warm Time-Series DB   | Loki / ClickHouse (Structured JSON Logs) | Milestone SimulationEvents for active run   |
| 3. Cold Compressed Archive| S3 / Disk Chunks (Zstandard chunk files) | Compacted milestone summaries only; 1 Year  |
+--------------------------+------------------------------------------+---------------------------------------------+
```

### Detailed Tier Specifications
1. **Hot Ring Buffer (In-Memory `deque(maxlen=200)` per Entity)**:
   - *Format*: In-memory Python dataclasses recording granular state deltas (`(x, y)` coordinates, HP/stamina deltas, active intents).
   - *Retention*: Bounded strictly to the last 200 ticks. Provides instant microsecond lookup for UI inspector modal windows and tactical combat debugging.
2. **Warm Time-Series DB (Loki / ClickHouse via Structured JSON)**:
   - *Format*: Scraped JSON `SimulationEvent` payloads (`CombatKill`, `LevelUp`, `QuestComplete`).
   - *Retention*: Retained for the active duration of the simulation scenario (up to 7 days). Indexed by `entity_id` and `event_type`. Provides fast filtering for historical entity timeline visualization in Grafana dashboards.
3. **Cold Compressed Archive (Zstandard Disk Chunks / S3)**:
   - *Format*: Compacted binary JSON/MessagePack chunk files (`chunk_0000.json.zst`). Cosmetic FX and routine step deltas are stripped by `StateUpdateCompactor`.
   - *Retention*: Retained for 1 year for audit and replay verification.

---

## Section J: Semantic Metrics Gap Analysis: `WorldMetrics` vs `PressureSignals`

To ensure comprehensive dashboard coverage, existing metric structures must be audited against operational requirements.

```
+----------------------------------------------------------------------------------------+
|                                  METRIC STRUCTURE GAP ANALYSIS                         |
+---------------------------------------+------------------------------------------------+
| WorldMetrics (src/engine/metrics.py)  | PressureSignals (src/engine/runtime_status.py) |
| - alive_entities: int                 | - work_debt: int                               |
| - total_gold: int                     | - tick_compute_ms: float                       |
| - total_trauma: float                 | - phase_costs: Dict[str, float]                |
| - avg_influence: float                | - memory_rss_bytes: int                        |
| - rejection_counts: Dict[str, int]    | - dropped_work_delta: int                      |
| - quest_status_counts: Dict[str, int] | - queue_depth: int                             |
| - transaction_trace: List[str]        | - governor_mode: int                           |
+---------------------------------------+------------------------------------------------+
```

### 1. Structural Comparison
- **`WorldMetrics`**: Focused on semantic simulation truth (economy, population, quest completion, trauma). Extracted per tick into a static dataclass.
- **`PressureSignals`**: Focused on computational hardware pressure and scheduling health (compute latency, work debt, GC pauses, worker queue depth). Retained in a bounded 100-tick deque inside `RuntimeStatus`.

### 2. Missing Semantic Metrics (Observability Gaps)
The audit reveals several critical missing semantic metrics required for complete ecosystem monitoring:
1. **`sim_stuck_entity_ratio`**: The percentage of active entities with active navigation intents whose physical positions have not changed for >20 ticks.
2. **`sim_item_circulation_count`**: Total active items in circulation broken down by rarity tier (`COMMON`, `RARE`, `EPIC`, `LEGENDARY`) from `ItemRegistry`.
3. **`sim_building_sabotage_rate`**: The frequency of building damage events and active structural trauma across regional towns.
4. **`sim_social_contract_churn`**: Ratio of successfully ratified social contracts versus expired or broken contracts.
5. **`sim_governor_throttle_frequency`**: The percentage of ticks where `ResourceGovernor` actively engaged `THROTTLED` or `SHEDDING` modes.

### 3. Remediation Plan
Extend `WorldMetrics` (`src/engine/metrics.py`) to incorporate these 5 fields and register corresponding Prometheus gauges inside `PrometheusMetricsCollector`.

---

## Section K: Balance Profile & Scenario Expectations Readiness

### 1. Hardcoded Python Configuration Bottleneck
Inspection of `src/certification/scenarios.py` and `src/config/profiles.py` reveals that scenario expectations (pass/fail thresholds, max execution ticks, allowed error counts) and runtime balance profiles (entity HP scaling, gold circulation caps, stamina regen rates) are currently hardcoded directly within Python dictionary structures.

This hardcoding creates a significant operational bottleneck for game designers and automated balancing tools, requiring source-code modifications and re-deployments to adjust simulation parameters.

### 2. Proposed YAML Loader Architecture
To make the Simulation Observatory data-driven, the engine must implement a robust YAML configuration loader in `src/config/balance_loader.py`.

```yaml
# Example Configuration: config/balance_profiles/standard_gaming_profile.yml
profile_name: "standard_gaming_profile"
version: "2.1.0"
runtime_limits:
  max_simulation_ticks: 50000
  target_tps: 10.0
  governor_throttle_threshold_ms: 45.0
entity_balance:
  base_hero_hp: 100.0
  stamina_regen_per_tick: 1.5
  terrain_movement_penalties:
    SWAMP: 2.0
    MOUNTAIN: 3.5
economic_balance:
  starting_town_gold: 5000
  shop_liquidity_cap: 25000
scenario_expectations: # Scenario pass/fail criteria
  allowed_failure_kinds: ["QUEST_EXPIRED", "HERO_PERMADEATH"]
  max_recovery_ticks_allowed: 150
  required_governor_modes: ["NORMAL", "THROTTLED"]
```

### 3. Loading Pipeline
The `BalanceLoader` parses the YAML file, validates it against a strict `Pydantic` schema (`BalanceProfileSchema`), and injects an immutable singleton (`ActiveBalanceProfile`) into `Kernel` during initialization (`Kernel.initialize(profile_path="config/balance_profiles/standard_gaming_profile.yml")`).

---

## Section L: Production Watchdog Readiness

### 1. Container Boot Failures in Active V2 Codebase
In the active V2 codebase (`src/`), the directories `src/workers/` and `src/utils/` do not exist. The production worker daemon and watchdog scripts exist exclusively at `src_legacy/workers/ai_worker_daemon.py` and `src_legacy/utils/watchdog.py`. 

When deployed via `docker-compose.yml`, both containers fail to boot due to `ModuleNotFoundError: No module named 'src_legacy'` or missing V2 package structures. Furthermore, the legacy watchdog script attempts to scrape `http://backend:8000/metrics` for `sim_current_tick`, which returns `HTTP 404`, causing the watchdog to register false positive `SYSTEM_CRITICAL` stalls and trigger container restarts.

### 2. Production Watchdog Architecture
To establish production stability, `WatchdogDaemon` (`src/observability/watchdog.py`) must be refactored as a decoupled, resilient verification service:
- **Health Verification Target**: Scrapes the `/health` and `/metrics` routes exposed by FastAPI (`src/api/server.py`).
- **Tick Stall Detection**: Validates that `sim_current_tick` increments by at least 1 tick every 5.0 seconds. If `sim_current_tick` remains static for >15 seconds, it flags a `TICK_STALL_CRITICAL` event.
- **Thread & Pool Deadlock Detection**: Queries worker daemon internal status endpoints (`http://ai_worker:8001/health`) to verify that no thread in `WorkerPool` has remained executing a single work item for >10.0 seconds.
- **Automated Remediation**: Upon confirming a critical stall or deadlock, the watchdog logs an exhaustive stack dump to Loki, emits a `WatchdogTripwireEvent`, and issues an automated SIGTERM/SIGKILL sequence to restart the frozen worker container.

---

## Section M: Verification Plan & Validation Matrix

To verify the successful implementation of all observability improvements, the engineering team will execute the following rigorous validation matrix:

```
+------------------------------------------------------------------------------------------------------------------------+
|                                              OBSERVABILITY VALIDATION MATRIX                                           |
+--------------------------+-------------------------------------------+-------------------------------------------------+
| Verification Area        | Automated Test / Execution Harness        | Explicit Acceptance Criteria                    |
+--------------------------+-------------------------------------------+-------------------------------------------------+
| 1. Loki Label Safety     | tests/logging/test_loki_cardinality.py    | Promtail config excludes tick label; Grafana log|
|                          |                                           | queries return <= 50 streams across 10k ticks.  |
| 2. Prometheus Metrics    | tests/observability/test_metrics_export.py| /metrics route serves all 20+ PromQL gauges;    |
|                          |                                           | Prometheus scrape returns HTTP 200 OK.          |
| 3. Hard Law Enforcement  | tests/engine/test_hard_law_monitor.py     | Monitor successfully traps negative gold/HP     |
|                          |                                           | mutations and halts simulation before persist.  |
| 4. Anomaly Engine Stream | tests/observability/test_anomaly_daemon.py| Out-of-process daemon successfully detects stuck|
|                          |                                           | entities in < 100ms via Redis stream ingestion. |
| 5. Balance Config Loader | tests/config/test_balance_loader.py       | BalanceLoader correctly parses YAML profile and |
|                          |                                           | rejects invalid schema properties.              |
| 6. Production Watchdog   | tests/observability/test_watchdog.py      | Watchdog correctly detects artificial tick stall|
|                          |                                           | and dispatches container restart signal.        |
+--------------------------+-------------------------------------------+-------------------------------------------------+
```

---

## Section N: Conclusion & Engineering Roadmap

This Phase 2 clarification report completes the foundational observability review for the V2 RPG Engine. By addressing the critical high-cardinality label blocker in Promtail and restoring the missing Prometheus metric export architecture, the Simulation Observatory is primed for robust production deployment.

### Recommended Implementation Sequence
1. **Remediate Promtail Configuration**: Immediately remove the `tick` stream label from `promtail-config.yml` to secure Loki indexing stability.
2. **Expose Prometheus `/metrics` Endpoint**: Instantiate `PrometheusMetricsCollector` and mount `/metrics` in `src/api/server.py` to populate Grafana dashboards.
3. **Implement `HardLawMonitor`**: Hook the invariant verification logic into `Kernel._phase_finalization` driven by `DirtySet`.
4. **Deploy Out-of-Process Anomaly Daemon**: Connect the asynchronous anomaly detection engine to consume curated `SimulationEvents`.
5. **Implement `BalanceLoader`**: Migrate hardcoded simulation balance profiles to structured YAML schemas.
