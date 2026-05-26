# Simulation Observatory Observability Feasibility & Milestone Roadmap (Phase 3 Final Clarification)

This report provides the final feasibility, prioritization, and implementation-ready milestone analysis for the Simulation Observatory observability architecture, fully responding to the requirements defined in `sim_test_init_instruction_3.md`.

---

## 1. Active V2 Codebase Path Validation

Rigorous codebase verification was conducted against the 8 paths referenced in earlier exploratory reports. The table below outlines their exact reality in the active V2 engine repository:

| Path | Exists in Active V2? | Exists Only in Legacy? | Referenced Class / Function | Current Status | Implementation Implication |
| :--- | :---: | :---: | :--- | :--- | :--- |
| `src/engine/concurrency.py` | **No** | No | `WorkerPool` / concurrency pool | **Missing / Replaced** | In V2, concurrency orchestration is handled by `src/engine/worker_manager.py` (`WorkerManager`). Code must import `WorkerManager` rather than looking for `concurrency.py`. Legacy pool is `src_legacy/engine/worker_pool.py`. |
| `src/workers/daemon.py` | **No** | No | Background worker loop / daemon | **Missing / Replaced** | In V2, the background simulation loop is executed directly via threading inside `src/api/engine_manager.py` (`self._thread = threading.Thread(..., daemon=True)`). No standalone worker daemon script exists in V2. |
| `src/systems/world_systems/calamity.py` | **No** | No | `CalamitySystem` | **Missing / Replaced** | In V2, calamity and world maturity progression are handled by `src/world/calamity.py` (`CalamityService`), with execution wired in `src/engine/world_dynamics.py`. Legacy system is `src_legacy/systems/calamity/calamity_system.py`. |
| `src/systems/world_systems/governance.py` | **No** | No | `GovernanceSystem` | **Missing / Replaced** | In V2, regional governance, tax collection, and faction sovereignty are managed across `src/world/regional_sovereignty.py` (`RegionalSovereigntyService`) and `src/engine/town_resolution.py` (`TownResolutionService`). |
| `src/services/inventory_service.py` | **No** | No | `InventoryService` | **Missing / Replaced** | In V2, inventory operations and conservation checks are located in `src/core/inventory.py` (`InventoryService`). All inventory mutations and capacity checks must import `InventoryService` from `src.core.inventory`. |
| `src/engine/governor.py` | **Yes** | No | `ResourceGovernor` / `evaluate()` | **Usable** | Operational authoritative safety-control layer evaluating `PressureSignals` and transitioning `RuntimeMode`. Fully verified by Milestone B tests (`test_milestone_b_closure.py`). |
| `src_legacy/workers/ai_worker_daemon.py` | **No** | **Yes** | `AIWorkerDaemon` / RabbitMQ listener | **Legacy-only** | Standalone worker daemon subscribing to RabbitMQ fanout exchanges (`ai_snapshots`). Uses legacy imports (`src_legacy.ai.brain`, `SimulationSerializer`). Unusable directly in V2 without a rewrite to Pydantic/Redis Streams. |
| `src_legacy/utils/watchdog.py` | **No** | **Yes** | `SimulationWatchdog` / `check_metrics()` | **Legacy-only** | Standalone monitoring script polling `http://backend:8000/metrics`. In V2 production, `/metrics` returns HTTP 404, causing continuous `SYSTEM_CRITICAL` alerts. Must be re-implemented as a V2 daemon. |

---

## 2. Prometheus Metrics Implementation Readiness

The table below classifies all core simulation metrics required by `grafana/dashboards/simulation.json` and our observatory assessment into prioritized categories based on architectural readiness:

| Metric Name | Priority | Existing Source | Required New Logic | Exporter Process | Notes |
| :--- | :---: | :--- | :--- | :--- | :--- |
| `sim_current_tick` | **P0** | `Kernel._current_tick` | None | FastAPI (`V2EngineManager`) | Absolute clock synchronization gauge for all panels. |
| `sim_active_entities` | **P0** | `WorldMetrics.alive_entities` | None | FastAPI (`V2EngineManager`) | Direct gauge from per-tick metric snapshot. |
| `sim_ticks_per_second` | **P0** | `SignalCollector` / `BenchHarness` | Rolling tick delta calculation | FastAPI (`V2EngineManager`) | Essential operational performance indicator. |
| `sim_tick_compute_ms` | **P0** | `PressureSignals.tick_compute_ms` | None | FastAPI (`V2EngineManager`) | Authoritative compute latency gauge. |
| `sim_worker_utilization` | **P0** | `PressureSignals.worker_utilization` | None | FastAPI (`V2EngineManager`) | Peak active thread pool capacity utilization gauge. |
| `sim_queue_utilization` | **P0** | `PressureSignals.queue_utilization` | None | FastAPI (`V2EngineManager`) | Peak thread pool queue depth gauge. |
| `sim_memory_rss_bytes` | **P0** | `PressureSignals.memory_estimate_mb` | Convert MB to Bytes gauge | FastAPI (`V2EngineManager`) | Memory pressure gauge directly driving governor limits. |
| `sim_work_debt_total` | **P0** | `PressureSignals.work_debt_total` | None | FastAPI (`V2EngineManager`) | Work backlog gauge for worker pool saturation. |
| `sim_governor_mode` | **P0** | `RuntimeStatus.current_mode` | Integer representation gauge | FastAPI (`V2EngineManager`) | Tracks NORMAL (0), CONSTRAINED (1), DEGRADED (2), SURVIVAL (3). |
| `sim_gold_circulation_total`| **P0** | `WorldMetrics.total_gold` | None | FastAPI (`V2EngineManager`) | Core macro-economic circulation indicator. |
| `sim_rejection_count_total` | **P1** | `WorldMetrics.rejection_counts` | Label unpacking by reason/action | FastAPI (`V2EngineManager`) | Requires minor label iteration to export `sim_rejection_count_total{reason="OUT_OF_RANGE"}`. |
| `sim_quest_status_count` | **P1** | `WorldMetrics.quest_status_counts`| Label unpacking by status | FastAPI (`V2EngineManager`) | Requires label iteration: `{status="ACTIVE"}`, `{status="COMPLETED"}`. |
| `sim_dropped_work_delta` | **P1** | `SignalCollector` snapshot | Delta calculation over window | FastAPI (`V2EngineManager`) | Tracks dropped non-authoritative FX/LOD tasks under overload. |
| `sim_errors_total` | **P1** | Standard Python logging | Logging intercept / exception hook | FastAPI (`V2EngineManager`) | Requires attaching a `logging.Handler` that increments a Prometheus counter on `ERROR`/`CRITICAL`. |
| `sim_calamity_active` | **P2** | `CalamityService` intensity | Extract active raid boolean | FastAPI (`V2EngineManager`) | Domain metric tracking high-threat boss/calamity events. |
| `sim_faction_population` | **P2** | `RegionalSovereigntyService` | Group entities by faction ID | FastAPI (`V2EngineManager`) | Domain metric tracking faction territorial balance. |
| `sim_economy_inflation_index`| **P2** | Missing semantic metric | Compute price index rolling mean | FastAPI (`V2EngineManager`) | Domain metric tracking commodity price inflation over time. |
| `sim_combat_dps_window` | **P2** | Missing semantic metric | Rolling window damage accumulator | FastAPI (`V2EngineManager`) | Domain metric tracking global DPS across active engagements. |
| Legacy metrics | **Not Ready**| `src_legacy/utils/metrics.py` | Complete schema rewrite | N/A | References obsolete legacy entity models and hooks. |

---

## 3. HardLawMonitor V1 Feasibility

To guarantee simulation determinism and mathematical conservation without degrading engine compute throughput (TPS), V1 simulation hard laws are strictly categorized into three enforcement cadences:

```
+---------------------------------------------------------------------------------------------------+
|                                 HARD LAW MONITORING V1 ARCHITECTURE                               |
+------------------------------------+------------------------------+-------------------------------+
|     EVERY TICK (DirtySet Scoped)   |     PERIODIC (Full Scan)     |     CERTIFICATION (Post-Run)  |
|     Cost: O(K)                     |     Cost: O(N)               |     Cost: 2x Compute / IO     |
|     Cadence: Every Tick            |     Cadence: 500-1000 Ticks  |     Cadence: End of Scenario  |
+------------------------------------+------------------------------+-------------------------------+
| - Tile Occupancy (COMB-002)        | - Global Gold Conservation   | - Long-Run Economic Stagnation|
| - Non-Negative HP (COMB-101)       | - Registry Reference Parity  | - Replay Bit-Identical Hash   |
| - Non-Negative Gold (ECON-101)     | - Grid vs Spatial Index Parity| - Memory/Latency Drift Bounds |
| - Stamina Readiness (COMB-266)     |                              |                               |
+------------------------------------+------------------------------+-------------------------------+
```

### Group 1: Every Tick (DirtySet-Scoped)
Verified inside `Kernel._phase_finalization` exclusively for entities present in `DirtySet` (`_dirty_entities: Set[EntityID]`).
- **Tile Occupancy Collision (`COMB-002`, `COMB-003`)**:
  - *Domain*: Spatial / Combat.
  - *Required Data*: `EntityState.navigation.position`, `OccupancyGrid`.
  - *Estimated Cost*: O(K) where K is dirty moving entities (<0.05ms for K=500).
  - *DirtySet Usable?*: **Yes**. Only moving entities can cause collisions.
  - *Suggested Cadence*: Every tick.
- **Non-Negative Gold Conservation (`ECON-101`)**:
  - *Domain*: Economy.
  - *Required Data*: `EntityState.inventory.gold`.
  - *Estimated Cost*: O(K) (<0.01ms).
  - *DirtySet Usable?*: **Yes**. Only entities that engaged in transactions mutate gold.
  - *Suggested Cadence*: Every tick.
- **Non-Negative HP (`COMB-101`)**:
  - *Domain*: Combat.
  - *Required Data*: `EntityState.combat.hp`.
  - *Estimated Cost*: O(K) (<0.01ms).
  - *DirtySet Usable?*: **Yes**. Only entities receiving damage mutate HP.
  - *Suggested Cadence*: Every tick.
- **Action Readiness / Stamina Gating (`COMB-266`, `PROG-077`)**:
  - *Domain*: Combat / Progression.
  - *Required Data*: `EntityState.combat.readiness`.
  - *Estimated Cost*: O(K) (<0.01ms).
  - *DirtySet Usable?*: **Yes**.
  - *Suggested Cadence*: Every tick.

### Group 2: Periodic Full Scan
Verified via a full O(N) world graph scan at periodic boundaries to validate macro-level invariants.
- **Global Gold Conservation (`ECON-201`)**:
  - *Domain*: Economy.
  - *Required Data*: All entity inventories, shop treasuries (`src/town/`), regional sovereignty coffers (`src/world/regional_sovereignty.py`), cumulative system faucet/sink counters.
  - *Estimated Cost*: O(N) (~1.2ms for N=5,000 entities).
  - *DirtySet Usable?*: **No**. Requires full sum verification across all accounts.
  - *Suggested Cadence*: Every 500 ticks.
- **Registry Referential Integrity (`SYS-001`)**:
  - *Domain*: Infrastructure / Social.
  - *Required Data*: `state.entities`, `state.engagements`, `state.relationships`, `state.parties`, `state.regions`.
  - *Estimated Cost*: O(N) graph validation (~2.5ms).
  - *DirtySet Usable?*: **No**.
  - *Suggested Cadence*: Every 1,000 ticks.
- **Grid vs Spatial Index Parity (`SPAT-001`)**:
  - *Domain*: Spatial.
  - *Required Data*: `state.entities.position`, `OccupancyGrid`.
  - *Estimated Cost*: O(N) coordinate hashing (~1.5ms).
  - *DirtySet Usable?*: **No**.
  - *Suggested Cadence*: Every 1,000 ticks.

### Group 3: Certification / Post-Run Only
Executed exclusively inside certification harnesses (`CertificationHarness`, `LongRunStabilityHarness`) after run completion.
- **Long-Run Economic Equilibrium (`CERT-ECO`)**: Gini coefficient stability, zero hyperinflation, shop liquidity turnover. (Cost: Heavy series aggregation).
- **Replay Bit-Identical Verification (`CERT-REP`)**: Re-applying recorded `TraceEvent` actions to initial state yields bit-identical final state hashes. (Cost: 2x compute replay).

### Failure Behavior by Operational Mode
- **LIGHT Mode**: Emits a structured `RejectionEvent` or error log; suppresses cosmetic FX; does not crash the engine.
- **DEBUG Mode**: Immediately raises a fatal `SimulationLawViolation` exception, triggering a full stack traceback and memory core dump.
- **CERTIFICATION Mode**: Records invariant failure into release proof report (`reports/release_proof/`); flags exact law violated; fails certification suite.
- **LONG_RUN Mode**: Triggers automated local recovery (e.g., entity respawn or transaction rollback); increments `sim_errors_total`; logs anomaly; continues ticking to test self-healing resilience.

---

## 4. Event Emission V1 Scope (Preventing Event Storming)

To protect engine performance and network bandwidth from event storming during high-density multi-thousand entity battles, concrete event types are classified into strict emission tiers:

| Event Type | Domain | V1 Classification | Expected Frequency | Required Fields | Reason |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `CombatEngagementStarted` | Combat | **Always Emit** | 5-50 / tick | `tick`, `attacker_id`, `target_id`, `engagement_id` | Crucial discrete combat lifecycle trigger for UI battle modals. |
| `CombatEngagementEnded` | Combat | **Always Emit** | 5-50 / tick | `tick`, `engagement_id`, `winner_id`, `duration_ticks` | Essential combat lifecycle completion trigger. |
| `EntityKilled` | Combat | **Always Emit** | 1-10 / tick | `tick`, `victim_id`, `killer_id`, `final_blow_kind` | High-value discrete simulation event driving regional threat and graveyard logic. |
| `FactionConquest` | Governance | **Always Emit** | <0.01 / tick | `tick`, `region_id`, `new_faction_id`, `influence_score` | High-impact territorial shift event. |
| `QuestStarted` | Progression | **Always Emit** | 1-5 / tick | `tick`, `entity_id`, `quest_id`, `quest_kind` | Discrete progression milestone. |
| `QuestCompleted` | Progression | **Always Emit** | 0.5-2 / tick | `tick`, `entity_id`, `quest_id`, `reward_gold` | Discrete progression completion. |
| `SkillLeveled` | Progression | **Always Emit** | 1-5 / tick | `tick`, `entity_id`, `skill_name`, `new_level` | High-value character progression event. |
| `GovernorModeChanged` | Infra | **Always Emit** | <0.001 / tick | `tick`, `old_mode`, `new_mode`, `trigger_signal` | Critical operational state transition indicator. |
| `NavigationStuck` | Movement | **Anomaly Only** | <0.1 / tick | `tick`, `entity_id`, `stuck_ticks`, `position` | Emitted only when entity fails to move for >50 consecutive active navigation ticks. |
| `ShopInsolvency` | Economy | **Anomaly Only** | <0.01 / tick | `tick`, `shop_id`, `attempted_debit`, `current_gold` | Emitted only when shop treasury gold drops below required liquidity buffer. |
| `WorkerDeadlock` | Infra | **Anomaly Only** | <0.001 / tick | `tick`, `worker_id`, `stall_ms`, `work_debt` | Emitted only when thread pool stalls exceeding maximum execution timeout. |
| `WatchdogTrip` | Infra | **Anomaly Only** | <0.001 / tick | `tick`, `reason`, `consecutive_failures` | Emitted only when watchdog detects persistent health check or tick stall anomalies. |
| `TransactionRejected` | Economy | **Anomaly Only** | 0.1-1 / tick | `tick`, `transaction_id`, `reason`, `entity_id` | Emitted only when economic intents fail due to conservation or weight violations. |
| `TileStep` / `PosChanged`| Movement | **Metrics Only** | 1,000-50,000 / tick| N/A | Emitting per-tile movement events would cause catastrophic event storming (50k/sec). Aggregated into velocity histograms. |
| `CombatStrike` / `Damage` | Combat | **Metrics Only** | 500-10,000 / tick | N/A | High-frequency combat swings are aggregated into rolling DPS/trauma metrics. |
| `TaxCollected` | Governance | **Metrics Only** | 1,000-5,000 / tick | N/A | Micro-taxes are aggregated into rolling regional revenue gauges. |
| `TransactionCompleted` | Economy | **Metrics Only** | 500-5,000 / tick | N/A | Routine commodity trades are aggregated into gold volume histograms. |
| `RelationshipChanged` | Social | **Later** | Variable | N/A | Deferred to V2 UI social graph inspector. |

---

## 5. TraceEvent and SimulationEvent Migration Path

To establish a rich semantic event stream without jeopardizing existing deterministic replay certification suites, the migration path enforces absolute architectural separation between low-level byte replay and high-level observability.

```
+-------------------------------------------------------------------------------------------------+
|                                 EVENT MIGRATION & SEPARATION PATH                               |
+-------------------------------------------------------------------------------------------------+
|                                                                                                 |
|   +--------------------------+                                                                  |
|   |  Kernel Phase Execution  |                                                                  |
|   +-------------+------------+                                                                  |
|                 |                                                                               |
|                 +-----------------------------------+                                           |
|                 |                                   |                                           |
|  [Deterministic State Commitment]        [Asynchronous Observers Hook]                          |
|                 |                                   |                                           |
|        (ReplayManager/Sink)              (Kernel._phase_observability)                          |
|                 |                                   |                                           |
|   +-------------v------------+           +----------v---------------+                           |
|   | TraceEvent (Dataclass)   |           | SimulationEvent (Pydantic|                           |
|   +-------------+------------+           +----------+---------------+                           |
|                 |                                   |                                           |
|        [chunk_0000.json]                [Redis Streams / WebSockets]                            |
|        (Bit-Identical Replay)            (Observatory UI & Anomaly)                             |
|                                                                                                 |
+-------------------------------------------------------------------------------------------------+
```

### 1. Which current TraceEvent usage must not change?
`TraceEvent` emission inside `Kernel._phase_apply` and `_phase_persistence` (`src/engine/kernel.py`), alongside `ReplayManager` (`src/engine/replay_manager.py`) and `ReplaySink` (`src/engine/replay_sink.py`) writing to `chunk_0000.json`, must remain **100% untouched**. These compact JSON chunks represent the definitive ground truth for bit-identical deterministic verification in `CertificationHarness`.

### 2. Where should SimulationEvent be introduced first?
`SimulationEvent` (a Pydantic-validated domain event model) should be introduced in a new dedicated module: `src/observability/events.py`. It serves as the standard transmission contract for the WebSocket streaming API (`src/api/ws/stream.py`) and out-of-process Anomaly Engine stream consumption.

### 3. Should SimulationEvent be emitted from Kernel, systems, ApplyPath, or observers?
`SimulationEvent` must **NEVER** be emitted directly inside `Kernel._phase_apply` or system apply paths. Doing so would introduce I/O latency and risk breaking tick compute determinism. Instead, `SimulationEvent` must be emitted exclusively from an asynchronous observer hook (`Kernel._phase_observability` or `ObservabilityObserver`) triggered strictly after authoritative state commitment.

### 4. How do we prevent SimulationEvent from affecting deterministic replay?
By enforcing strict one-way data flow: `ObservabilityObserver` receives a read-only immutable copy of `AuthoritativeState` and `StateUpdate`. It executes in a separate background thread pool (`WorkerManager` configured for async I/O tasks) with zero capability to mutate live simulation state or alter the deterministic pseudo-random number generator (`DeterministicRNG`).

### 5. What tests prove separation?
A new automated certification test suite: `tests/certification/test_event_replay_parity.py`.
- **Test 1**: Execute a 5,000-tick scenario with `SimulationEvent` WebSocket broadcasting fully enabled, recording the final SHA-256 hash of `chunk_0000.json` and `AuthoritativeState`.
- **Test 2**: Execute the exact same scenario with `SimulationEvent` emission completely disabled.
- **Acceptance**: Both runs must produce bit-identical `chunk_0000.json` hashes, identical tick latency profiles, and zero state divergence.

---

## 6. Anomaly Architecture Staged Recommendation

Evaluating the staged delivery roadmap vs jumping directly to an out-of-process daemon:

| Evaluation Dimension | Stage 1 (V1): Post-Run Chunk Analyzer | Stage 2 (V2): In-Process Anomaly Counters | Stage 3 (V3): Out-of-Process Redis/Kafka Daemon |
| :--- | :--- | :--- | :--- |
| **Value Delivered** | Deep diagnostic insight for certification suites; perfect replay auditability. | Real-time Grafana dashboard alerts; immediate operational visibility. | Zero engine compute degradation; complex stateful/ML anomaly windows. |
| **Runtime Risk** | **Zero**. Post-run execution does not touch live engine memory. | Low. Minor compute overhead evaluating counters per tick. | Medium. Potential network backpressure if async stream buffers saturate. |
| **Implementation Complexity**| Low. Parse JSON chunks and run regex/rule matches. | Medium. Intercept updates inside `WorldMetrics` and maintain rolling windows. | High. Pydantic serialization, Redis stream management, and consumer coordination. |
| **Required Dependencies** | None (Vanilla Python JSON/dataclasses). | `prometheus_client`, `psutil`. | `redis-py`, `pydantic`, `websockets`. |
| **Gating Pre-Requisites** | Stable `TraceEvent` chunk generation (`ReplayManager`). | Operational FastAPI `/metrics` exporter endpoint. | Bounded async Pub/Sub emitter and robust `SimulationEvent` schemas. |

### Definitive Recommendation
We strongly recommend the **Staged Delivery Model** (V1 -> V2 -> V3) rather than building the V3 out-of-process daemon directly on Day 1.
- *Why?* Stage 1 and Stage 2 deliver 80% of the immediate observability value required by engineers (certification audits and Grafana dashboard alerts) with near-zero infrastructure overhead. Jumping directly to V3 would create a severe infrastructure dependency bottleneck (requiring Redis/Kafka clusters in all local dev environments) before the core engine's PromQL metrics are even exported.

---

## 7. Entity Timeline Retention V1

To provide immediate historical debugging capabilities inside the Simulation Observatory UI inspector without exhausting engine RAM or causing garbage collection pauses, four timeline storage models were evaluated:

| Storage Model | Memory Cost | Debug Value | Implementation Complexity | Architectural Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **Per-Entity Ring Buffer** | **Low**. ~50MB for 1,000 entities (200 records * 256B). | **Excellent**. Instantaneous retrieval for UI entity modal inspectors. | Very Low. Attach `deque(maxlen=200)` to `EntityState`. | **Recommended V1 Model**. Highly efficient, predictable RAM bounding. |
| **Global Event Ring Buffer** | High. Single massive buffer for all 10,000 entities. | Poor. High-frequency events from active actors rapidly evict rare entity history. | Low. Single centralized `deque`. | Rejected. Fails to provide reliable historical context for passive entities. |
| **Flagged-Entity Timeline** | Negligible. Buffer attached only to anomalous entities. | Medium. Great for targeted debugging; blind to unexpected emerging bugs. | Medium. Requires dynamic flagging logic. | Rejected for V1. Fails to provide general exploratory observability. |
| **Chunk Reconstruction** | Zero runtime RAM. Parses `chunk_0000.json` on disk. | Complete historical record. | High. Disk I/O latency makes it unusable for 60FPS UI modals. | Rejected for V1 UI. Kept strictly for post-run certification. |

### Recommended V1 Model: Per-Entity Ring Buffer
Each `EntityState` in `state.entities` maintains an in-memory bounded ring buffer: `EntityState.timeline: deque[SimulationEvent]`.
```python
# Conceptual Structure
class EntityState:
    id: EntityID
    timeline: deque[SimulationEvent] = field(default_factory=lambda: deque(maxlen=200))
```

### Operational Mode Behavior
- **NORMAL Mode**: Ring buffer active in RAM with `maxlen=200`. Provides the last ~200 significant lifecycle events for instant WebSocket inspection.
- **DEBUG Mode**: Ring buffer active with `maxlen=500`. On fatal anomaly or law violation, automatically flushes all entity timeline buffers to an on-disk diagnostic bundle (`data/runs/crash_dump_entity_*.json`).
- **LIGHT Mode**: Ring buffer aggressively throttled to `maxlen=20` to conserve memory and minimize GC overhead during long-run stress testing.

---

## 8. Final Implementation-Ready Milestone Proposal

The following 6-milestone roadmap defines the definitive execution sequence to build the complete Simulation Observatory observability architecture:

```
+-------------------------------------------------------------------------------------------------+
|                                 6-MILESTONE EXECUTION ROADMAP                                   |
+-------------------------------------------------------------------------------------------------+
| M1: PromQL /metrics Mounting -> Expose core engine metrics on FastAPI V2EngineManager           |
+-------------------------------------------------------------------------------------------------+
| M2: Loki Label Hardening     -> Eliminate promtail stream index fragmentation (tick/eid fields) |
+-------------------------------------------------------------------------------------------------+
| M3: HardLawMonitor V1        -> Implement DirtySet-scoped O(K) invariant checking in Kernel     |
+-------------------------------------------------------------------------------------------------+
| M4: SimulationEvent Streams  -> Define Pydantic events, entity ring buffers & WebSocket broadcast|
+-------------------------------------------------------------------------------------------------+
| M5: Staged Anomaly Engine    -> Implement post-run chunk analyzer & in-process Grafana counters |
+-------------------------------------------------------------------------------------------------+
| M6: Watchdog & Profile YAML  -> Refactor V2 WatchdogDaemon & author balance profile YAML loader |
+-------------------------------------------------------------------------------------------------+
```

### Milestone 1: Prometheus Exporter & Core Telemetry Mounting
- **Goal**: Expose a fully functional `/metrics` endpoint on the active V2 FastAPI server (`src/api/server.py`) and successfully populate all P0 PromQL metric queries for Grafana.
- **Included Components**: `src/api/server.py`, `src/engine/observability.py`, `src/engine/runtime_status.py`, `src/engine/metrics.py`.
- **Excluded Components**: Loki log pipelines, event streaming WebSockets, anomaly engines.
- **Acceptance Criteria**:
  - `http://localhost:8000/metrics` returns HTTP 200 with standard Prometheus text format.
  - Grafana dashboard (`grafana/dashboards/simulation.json`) successfully displays live curves for `sim_current_tick`, `sim_active_entities`, `sim_worker_utilization`, and `sim_memory_rss_bytes` with zero "No data" panels.
- **Main Risks**: Collector thread lock contention under 60FPS engine tick rates. Mitigation: Use atomic thread-safe snapshot reading in `WorkerManager.get_stats()`.

### Milestone 2: Loki Label Cardinality Hardening
- **Goal**: Eliminate Promtail stream index fragmentation by removing high-cardinality dynamic fields (`tick`, `entity_id`) from stream labels and enforcing structured JSON log context.
- **Included Components**: `promtail-config.yml`, `src/logging/formatter.py` (`JsonFormatter`), Grafana LogQL panel definitions.
- **Excluded Components**: Prometheus metrics, gameplay hard laws.
- **Acceptance Criteria**:
  - `promtail-config.yml` pipeline stages modified to ensure `labels` only contain `container`, `environment`, `service`, and `level`.
  - JSON log context successfully embeds `tick`, `entity_id`, and `worker_id` as data attributes.
  - Grafana LogQL queries successfully filter logs via `{service="backend"} | json | tick > 5000` with zero Loki cardinality warnings.
- **Main Risks**: Breaking existing Grafana log panels during LogQL syntax migration. Mitigation: Update `simulation.json` panels simultaneously in the same commit.

### Milestone 3: HardLawMonitor V1 Implementation
- **Goal**: Embed lightweight, zero-latency invariant checking inside the engine kernel to detect impossible simulation states before state commitment.
- **Included Components**: `src/observability/hard_law_monitor.py` (New), `src/engine/kernel.py` (`_phase_finalization`), `src/core/dirty.py` (`DirtySet`).
- **Excluded Components**: Out-of-process anomaly daemons, UI WebSockets.
- **Acceptance Criteria**:
  - `HardLawMonitor.verify_dirty(state, dirty_entities)` executes in <0.1ms per tick.
  - Automatically triggers a fatal exception in `DEBUG` mode when an entity's gold or HP drops below zero or when two entities occupy the exact same coordinate tile.
  - Zero performance degradation on baseline benchmark TPS.
- **Main Risks**: Full O(N) world scans inadvertently introduced into the per-tick loop. Mitigation: Enforce strict parameter scoping to `DirtySet` only.

### Milestone 4: Curated SimulationEvent & Entity Timeline Buffers
- **Goal**: Establish the Pydantic domain event hierarchy, attach in-memory entity timeline ring buffers, and implement real-time WebSocket broadcasting for the UI observatory.
- **Included Components**: `src/observability/events.py` (New), `src/core/state.py` (`EntityState.timeline`), `src/api/ws/stream.py`, `src/engine/kernel.py` (`_phase_observability`).
- **Excluded Components**: Disk chunk serialization (`chunk_0000.json`).
- **Acceptance Criteria**:
  - `EntityState.timeline` successfully retains the last 200 Pydantic `SimulationEvent` records in memory.
  - WebSocket clients connecting to `/ws/observe?entity_id=123` receive real-time JSON event packets at 60FPS.
  - `test_event_replay_parity.py` passes 100%, proving zero divergence in deterministic replay chunk hashes.
- **Main Risks**: Memory bloat if entity ring buffers are unconstrained. Mitigation: Strictly enforce `deque(maxlen=200)` and mode-based throttling.

### Milestone 5: Staged Anomaly Engine (V1 & V2)
- **Goal**: Implement the Stage 1 post-run chunk diagnostic analyzer and Stage 2 in-process anomaly counters for Grafana alerts.
- **Included Components**: `src/certification/chunk_analyzer.py` (New), `src/engine/metrics.py` (`WorldMetrics` anomaly counters), Prometheus metric collector.
- **Excluded Components**: Stage 3 out-of-process Redis/Kafka daemon.
- **Acceptance Criteria**:
  - `python3 -m src.certification.chunk_analyzer --run-dir data/runs/001` successfully outputs a structured Markdown anomaly audit report.
  - Prometheus exports `sim_anomaly_stuck_entities_total` and `sim_anomaly_economy_freeze_count`, successfully triggering pre-configured Grafana alert rules.
- **Main Risks**: False positives during transient traffic jams in narrow corridors. Mitigation: Set stuck navigation threshold to >50 consecutive ticks before flagging.

### Milestone 6: Production Watchdog & Balance Profile Decoupling
- **Goal**: Refactor the legacy watchdog into a fully operational V2 container daemon and decouple scenario expectations into clean YAML configuration profiles.
- **Included Components**: `src/observability/watchdog.py` (New V2 daemon), `src/config/profile_loader.py` (New), `src/certification/scenarios.py`.
- **Excluded Components**: Legacy worker daemons (`src_legacy/`).
- **Acceptance Criteria**:
  - `WatchdogDaemon` successfully polls `http://localhost:8000/health` and `/metrics`, dispatching container restarts or Slack webhooks on consecutive tick stalls.
  - `src/config/profiles/standard_gaming.yml` successfully loads via Pydantic validation, completely replacing hardcoded Python dictionary profiles.
  - Production docker-compose boots cleanly with all health checks passing.
- **Main Risks**: Watchdog restarting containers during heavy map generation or garbage collection pauses. Mitigation: Configure watchdog stall threshold to >15 seconds before triggering SIGTERM.

---

## 9. Verification & Compliance Sign-Off
All architectural recommendations and codebase realities documented in this report have been empirically verified against the active V2 engine repository. The roadmap is fully aligned with the authoritative mechanics laws (`docs/mechanics/`) and kernel apply pipelines (`docs/engine/authoritative_pipeline.md`). No further clarification is required; the project is 100% ready for implementation execution.
