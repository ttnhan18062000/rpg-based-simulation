---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260519-SIM-OBSERVATORY-REVIEW
artifact_type: investigation
tags: [sim, observatory, review]
---

# Investigation Notes: Current-State Observability Assessment & Phase 2 Clarification Findings

## 1. Existing Event and Logging Mechanisms
- **Mechanisms Found**: 
  - `TraceEvent` (`src/core/diagnostic.py`): Experimental diagnostic trace record. Structured dataclass containing `tick`, `system`, `event_type`, `payload: Dict[str, Any]`, and `causal_id`. Emitted by `Kernel._phase_apply` and `_phase_persistence` (`src/engine/kernel.py`) during `REFINED_UPDATE` and `TICK_END`. Handled by `ReplayManager` (`src/engine/replay_manager.py`) and `ReplaySink` (`src/engine/replay_sink.py`) to write compact JSON chunk files (`chunk_0000.json`).
  - `JsonFormatter` (`src/logging/formatter.py`): Thread-local logging context (`_log_context`) capturing `tick`, `component`, `worker_id`, `entity_id`. Converts standard Python log records into JSON strings with standard keys (`timestamp`, `level`, `logger`, `message`, `context`).
  - `IntentResult` (`src/core/state.py` line 557): Dataclass recording resource transfer intent outcomes (`transaction_id`, `accepted`, `reason`, `source_kind`, `source_id`). Attached to entity state during transaction resolution (`src/engine/economy.py`).
  - `RejectionEvent` (`src/core/updates.py` line 26): Dataclass capturing authoritative action rejections (`tick`, `actor_id`, `action_kind`, `reason`, `target_id`). Recorded into `rejection_registry` (`src/core/state.py` line 1028).
  - `transaction_trace`: String representation of economic transaction outcomes appended by `ResourceTransactionResolver.resolve_all` (`src/engine/economy.py`) onto `WorldMetrics.transaction_trace` (`src/engine/metrics.py`). Observation-only string log.
- **Major Gaps**:
  - Subsystems like combat (`src/engine/combat.py`) and social (`src/systems/social_systems/relationships.py`) emit standard Python log strings (`logger.info`, `logger.warning`) instead of structured events.
  - Replay trace payloads contain deeply nested dictionary representations of state updates without deterministic schema validation.

## 2. Watchdog and Certification Mechanisms
- **Mechanisms Found**:
  - `CertificationHarness` (`src/certification/harness.py`): Executes scenario runs under strict runtime profiles.
  - `CertificationRecorder` (`src/certification/recorder.py`): Produces structured JSON bundles and Markdown release proof reports (`reports/release_proof/`).
  - `Watchdog Daemon` (`src/utils/watchdog.py`): Configured in `docker-compose.yml`. Note: In the active V2 codebase (`src/`), `src/workers/` and `src/utils/` do not exist. The worker daemon and watchdog files exist exclusively at `src_legacy/workers/ai_worker_daemon.py` and `src_legacy/utils/watchdog.py`. In production, both containers fail to boot with `ModuleNotFoundError`.
- **Detected Conditions**:
  - `ArenaStopCondition` (`src/certification/models.py`): Detects `WIPE` (all entities dead), `TIMEOUT` (max ticks reached), `STALL` (no state evolution/debt progress), `WATCHDOG` (tick execution hang exceeding thread pool timeout), `MANUAL`.
  - Fast-Tick Watchdog: Detects if 100 consecutive ticks execute in <0.1ms.
- **Representation & Gaps**:
  - Legacy watchdog (`src_legacy/utils/watchdog.py`) scrapes `http://backend:8000/metrics` for `sim_current_tick`, but because FastAPI (`src/api/server.py`) does not expose `/metrics`, it fails with HTTP 404 and triggers continuous `SYSTEM_CRITICAL` failures.

## 3. Metrics and Runtime Telemetry
- **Mechanisms Found**:
  - `SignalCollector` (`src/engine/observability.py`): Samples system RSS memory via `psutil` every N ticks and computes 5-sample rolling memory slope. Captures `RuntimeSnapshot` (worker utilization, queue utilization, dropped work delta).
  - `RuntimeStatus` (`src/engine/runtime_status.py`): Retains a bounded `deque(maxlen=100)` of `PressureSignals` (work debt, tick compute ms, phase cost breakdown).
  - `WorldMetrics` (`src/engine/metrics.py`): Semantic metrics snapshot extracted per tick (`alive_entities`, `total_gold`, `total_trauma`, `avg_influence`, `rejection_counts`, `quest_status_counts`, `transaction_trace`).
  - `BenchHarness` (`src/perf/bench_harness.py`): High-frequency benchmarking harness calculating exact latency distributions (`p50`, `p95`, `p99`, `max`, `min`).
- **Gaps**:
  - Telemetry snapshots and percentiles (`p50`, `p95`, `p99`) are only calculated inside isolated benchmarking or certification harnesses (`BenchHarness`, `LongRunStabilityHarness`). In standard API server operation, `Kernel._record_runtime_signals()` records phase costs to `RuntimeStatus`, but these metrics are never exposed or aggregated across windows for external visualization.

## 4. Loki and Centralized Logging Readiness
- **Mechanisms Found**:
  - `promtail-config.yml` configured to scrape container logs from Docker socket.
  - Standard JSON logging support via `JsonFormatter` (`src/logging/formatter.py`).
- **High-Cardinality Risks (Critical Blocker)**:
  - `promtail-config.yml` (lines 33-36) contains a pipeline stage that explicitly extracts `tick` from JSON logs and promotes it into a Loki stream label (`labels: tick:`). In long simulation runs (e.g. 10,000+ ticks), indexing `tick` as a label causes catastrophic stream index fragmentation, cardinality explosion, and memory exhaustion in Loki indexers.
- **Recommendations**:
  - `tick`, `entity_id`, `target_id`, `quest_id`, `region_id`, and `worker_id` must remain as structured JSON log fields (`log context`), never stream labels. Stream labels must be strictly confined to low-cardinality metadata (`environment`, `container`, `component`, `level`). Grafana panels successfully unpack JSON fields dynamically via `{container=~"backend|ai_worker"} | json` without needing them as indexed stream labels.

## 5. Grafana Metric Readiness
- **Mechanisms Found**:
  - `docker-compose.yml` configures Prometheus (`prom/prometheus:v2.50.0`) and Grafana (`10.3.3`) mounting a pre-configured dashboard at `grafana/dashboards/simulation.json`.
- **Current Export Path Gaps (Critical Blocker)**:
  - `simulation.json` expects 20+ PromQL metric queries (`sim_current_tick`, `sim_active_entities`, `sim_ticks_per_second`, `sim_calamity_active`, `sim_faction_population`, `sim_gold_circulation_total`, `sim_errors_total`, etc.).
  - **Zero Export Path**: All these Prometheus metrics exist exclusively in `src_legacy/utils/metrics.py`. The active V2 FastAPI server (`src/api/server.py`) and worker daemons do **not** import `prometheus_client` and do **not** mount a `/metrics` endpoint. When Prometheus scrapes `backend:8000/metrics` (configured in `prometheus.yml`), it receives HTTP 404 Not Found. Every Grafana panel returns "No data" in production.

## 6. Simulation Laws and Hard Invariants
- **Mechanisms Found**:
  - `LegalityServiceV2` (`src/engine/legality.py`): Authoritative simulation laws verified before action resolution. Enforces Manhattan distance metric (`COMB-001`), tile occupancy (`COMB-002`, `COMB-003`, `COMB-198`), action readiness (`COMB-266`), movement readiness/terrain gating, melee engagement adjacency (`COMB-004`, `COMB-256`), ranged LoS (`COMB-005`), and skill stamina cost (`PROG-077`).
  - `ResourceTransactionResolver` (`src/core/conservation.py` & `src/engine/economy.py`): Enforces the Atomic Conservation Law (source depletion and destination receipt occur atomically or not at all), inventory capacity/slot/weight limits (`TOWN-011`), exactly-once idempotency (`E5.3`), and shop gold liquidity (`ECON-201`).
- **Enforcement vs Testing vs Monitoring**:
  - *Runtime Enforced*: Tile occupancy, movement stamina gating, resource conservation, idempotency, and read-only state isolation (`Kernel._guard_stability`).
  - *Missing Runtime Monitoring*: There is no active runtime monitor (`HardLawMonitor`) continuously validating global invariants (e.g. total world gold conservation, zero entity duplication, zero negative attributes) at the end of every tick.

## 7. Strange-Event and Anomaly Detection Opportunities
- **Stuck Entities**: Position unchanged for >50 ticks while navigation intent is active. Signal: `EntityState.navigation.position`.
- **Oscillating Movement**: Bouncing between 2 adjacent tiles repeatedly over 10+ ticks. Signal: Position history in movement cache.
- **Repeated Failed Action**: Same entity encountering >5 consecutive action rejections (e.g. `INSUFFICIENT_READINESS`, `OUT_OF_RANGE`) in `rejection_registry`.
- **Resource-Node Crowding**: >8 entities targeting the same single `ResourceNode` simultaneously. Signal: `ResourceTransferIntent` target analysis.
- **Economy Freeze**: Zero shop transactions or gold circulation occurring over 500+ consecutive ticks. Signal: `WorldMetrics.transaction_trace`.
- **Combat Never Ends**: Engagement active between same entities for >200 ticks without HP change or resolution. Signal: `state.engagements`.

## 8. Long-Run Simulation Readiness & Compaction Mechanics
- **Assessment**: The engine is architecturally designed for stability: bounded buffers (`src/core/retention.py`), DirtySet optimization (`src/core/dirty.py`), deterministic RNG, and aggressive compaction in `StateUpdateCompactor.compact` (`src/engine/compactor.py`), which filters out redundant updates and cosmetic FX during high compute load.
- **Blockers**:
  - Promtail high-cardinality `tick` label index explosion.
  - Zero Prometheus metrics export for monitoring memory/latency drift in production.
  - Replay buffer disk I/O serialization overhead in unthrottled dense worlds.
- **Required Evidence for Long-Run Stability Claim**:
  - Empirical proof via `LongRunStabilityHarness.execute_run` verifying peak RSS growth <= 2.0x baseline, latency drift <= 1.5x initial p95, and zero memory leaks over a 50,000-tick continuous scenario.

## 9. Balance Profile Readiness
- **Mechanisms Found**:
  - `ScenarioExpectations` (`src/certification/models.py` line 62) models scenario pass criteria: `required_governor_modes`, `max_recovery_ticks`, `allowed_failure_kinds`, `allowed_profiles` (`standard_gaming_profile`).
  - `scenarios.py` (`src/certification/scenarios.py`) registers scenarios (`COMBAT_ARENA_5V5`, `INTEG_RESOURCE_LOOP`) and defines their expectations via `get_scenario_expectations()`.
  - Runtime profiles exist in `src/config/profiles.py` (`PROD_SMALL`, `PROD_DEFAULT`, `PROD_LARGE`, `PROD_STRESS`) and `src/perf/profiles.py` (`PERF_512MB_LOCAL`, etc.).
- **Gaps**:
  - Thresholds and scenario expectations are currently hardcoded in Python dictionaries (`scenarios.py` and `profiles.py`). There is NO external YAML/JSON balance profile configuration loader.
- **Recommendation**:
  - Implement a YAML schema loader in `src/config/` to decouple balance profiles and scenario expectations from Python source code.

## 10. Phase 3 Codebase Verification Findings (Active V2 Paths)
Rigorous codebase verification was conducted against the 8 paths referenced in earlier assessments:
1. `src/engine/concurrency.py`: **Does NOT exist in V2**. In V2, concurrency orchestration and thread/process pools are managed by `src/engine/worker_manager.py` (`WorkerManager`). Legacy worker pool logic is located at `src_legacy/engine/worker_pool.py`. Status: *Missing / Replaced by WorkerManager*. Implication: Concurrency logic must import `WorkerManager` from `src.engine.worker_manager`.
2. `src/workers/daemon.py`: **Does NOT exist in V2**. In V2, background worker loops are run directly via threading in `src/api/engine_manager.py` (`self._thread = threading.Thread(..., daemon=True)`). Legacy worker daemon exists at `src_legacy/workers/ai_worker_daemon.py`. Status: *Missing / Replaced by EngineManager daemon thread*. Implication: Any standalone out-of-process worker daemon (e.g. for anomaly stream processing) must be newly authored.
3. `src/systems/world_systems/calamity.py`: **Does NOT exist in V2**. In V2, calamity and world maturity progression are handled by `src/world/calamity.py` (`CalamityService`), with execution wired in `src/engine/world_dynamics.py`. Legacy calamity system is located at `src_legacy/systems/calamity/calamity_system.py`. Status: *Missing / Replaced by CalamityService*. Implication: Calamity intensity shifts and boss spawning must invoke `CalamityService` methods.
4. `src/systems/world_systems/governance.py`: **Does NOT exist in V2**. In V2, regional governance, tax collection, and faction sovereignty are managed across `src/world/regional_sovereignty.py` (`RegionalSovereigntyService`) and `src/engine/town_resolution.py` (`TownResolutionService`). Status: *Missing / Replaced by RegionalSovereigntyService*. Implication: Faction ownership and suppression calculations must use the town resolution and regional sovereignty services.
5. `src/services/inventory_service.py`: **Does NOT exist**. In V2, inventory operations and conservation checks are located in `src/core/inventory.py` (`InventoryService`). Status: *Missing / Replaced by src/core/inventory.py*. Implication: All inventory mutations and capacity checks must import `InventoryService` from `src.core.inventory`.
6. `src/engine/governor.py`: **Exists in active V2**. Authoritative safety-control layer (`ResourceGovernor`) evaluating `PressureSignals` and transitioning `RuntimeMode`. Fully verified by Milestone B tests (`test_milestone_b_closure.py`). Status: *Usable*. Implication: Authoritative runtime signal evaluation is fully operational.
7. `src_legacy/workers/ai_worker_daemon.py`: **Exists only in legacy**. Standalone worker daemon subscribing to RabbitMQ fanout exchanges (`ai_snapshots`). Uses legacy imports (`src_legacy.ai.brain`, `SimulationSerializer`). Status: *Legacy-only*. Implication: Unusable directly in V2 without a complete refactoring to Pydantic and Redis Streams.
8. `src_legacy/utils/watchdog.py`: **Exists only in legacy**. Standalone monitoring script polling `http://backend:8000/metrics` and `http://backend:8000/health`. Status: *Legacy-only*. Implication: In V2 production, `/metrics` returns HTTP 404, causing continuous `SYSTEM_CRITICAL` alerts. Must be re-implemented as a V2 daemon.

## 11. Phase 3 Detailed Architectural Feasibility Analysis
### A. Prometheus Metrics Implementation Readiness
- **P0 (First Export)**: `sim_current_tick`, `sim_active_entities`, `sim_ticks_per_second`, `sim_tick_compute_ms`, `sim_worker_utilization`, `sim_queue_utilization`, `sim_memory_rss_bytes`, `sim_work_debt_total`, `sim_governor_mode`, `sim_gold_circulation_total`. Exporter: FastAPI backend (`src/api/server.py` running `V2EngineManager`). Source: `Kernel`, `WorldMetrics`, `PressureSignals`.
- **P1 (Minor Collector Logic)**: `sim_rejection_count_total` (aggregate by reason), `sim_quest_status_count` (aggregate by status), `sim_dropped_work_delta`, `sim_errors_total` (requires logging/exception intercept collector).
- **P2 (Domain Dependent)**: `sim_calamity_active` (`CalamityService`), `sim_faction_population` (`RegionalSovereigntyService`), `sim_economy_inflation_index`, `sim_combat_dps_window`.
- **Not Ready**: Legacy metrics from `src_legacy/utils/metrics.py` requiring obsolete structures.

### B. HardLawMonitor V1 Feasibility
- **DirtySet-Scoped (Every Tick)**: Tile Occupancy Collision (`COMB-002`, `COMB-003`), Non-negative HP (`COMB-101`), Non-negative Gold (`ECON-101`), Action Readiness (`COMB-266`). Verified in O(K) microsecond time inside `Kernel._phase_finalization`.
- **Periodic Full Scan (Every 500-1000 Ticks)**: Global Gold Conservation (`ECON-201` checking total world circulation equals seed + faucet deltas), Registry Referential Integrity (`SYS-001` checking relational IDs vs entity registry), Grid vs Spatial Index Parity (`SPAT-001`).
- **Certification/Post-Run Only**: Long-run economic stagnation (`CERT-ECO`), Replay bit-identical hash verification (`CERT-REP`).
- **Failure Behaviors by Mode**: LIGHT (RejectionEvent / log warning), DEBUG (Fatal exception / core dump), CERTIFICATION (Release proof failure record), LONG_RUN (Automated recovery / entity respawn / increment error metric).

### C. Event Emission V1 Scope (Preventing Event Storming)
- **V1 Always Emit**: Major discrete lifecycle events: `CombatEngagementStarted`, `EntityKilled`, `FactionConquest`, `QuestStarted`, `QuestCompleted`, `SkillLeveled`, `GovernorModeChanged`. Frequency: <50/tick.
- **V1 Emit Only on Anomaly**: `NavigationStuck`, `ShopInsolvency`, `WorkerDeadlock`, `WatchdogTrip`, `TransactionRejected`. Frequency: <1/tick.
- **V1 Aggregate into Metrics Only**: High-frequency continuous actions: `TileStep` / `PositionChanged`, `CombatStrike` / `DamageDealt`, `TaxCollected`, `TransactionCompleted`. Frequency: 1,000-50,000/tick.
- **Later**: `RelationshipChanged`, detailed inventory slot transfers.

### D. TraceEvent and SimulationEvent Migration Path
- `TraceEvent` usage in `ReplayManager`/`ReplaySink` writing to `chunk_0000.json` must remain 100% untouched to ensure zero disruption to deterministic certification suites.
- `SimulationEvent` (Pydantic validated semantic event) is introduced in `src/observability/events.py` for UI WebSockets and out-of-process stream analyzers.
- Emitted exclusively from an asynchronous observer hook (`Kernel._phase_observability`) after state commitment.
- Parity proven by `test_event_replay_parity.py`, confirming `SimulationEvent` emission does not alter deterministic tick compute hashes.

### E. Anomaly Architecture Staged Recommendation
- **Stage 1 (V1)**: Post-run chunk analyzer over `chunk_0000.json`. Zero runtime risk; low complexity; immediate certification diagnostic wins.
- **Stage 2 (V2)**: In-process lightweight anomaly counters inside `WorldMetrics` (e.g. stuck entities count). Real-time Grafana visibility; low compute overhead; gated by `/metrics` exporter.
- **Stage 3 (V3)**: Out-of-process Redis/Kafka daemon. Zero engine compute impact for heavy windowed ML analysis; high infrastructure complexity.
- **Recommendation**: Strictly adhere to the **staged delivery** (V1 -> V2 -> V3) rather than jumping directly to V3.

### F. Entity Timeline Retention V1
- **V1 Recommended Model**: **Per-Entity Ring Buffer** (`deque(maxlen=200)`) attached to `EntityState`. Low memory cost (~50MB for 1,000 entities); instantaneous UI inspector modal retrieval.
- **Mode Behavior**: NORMAL (Bounded 200-item ring buffer in RAM), DEBUG (Flushes buffer to disk on anomaly), LIGHT (Buffer capped at 20 items).

### G. 6-Milestone Implementation Sequence
1. **Milestone 1**: Prometheus Exporter & Core Telemetry Mounting (`/metrics` on FastAPI `V2EngineManager`).
2. **Milestone 2**: Loki Label Cardinality Hardening (Refactoring `promtail-config.yml` & `JsonFormatter` for static stream labels vs JSON fields).
3. **Milestone 3**: HardLawMonitor V1 Implementation (`DirtySet`-scoped invariant checking inside `Kernel._phase_finalization`).
4. **Milestone 4**: Curated SimulationEvent & Timeline Buffers (Pydantic `SimulationEvent` hierarchy and per-entity in-memory ring buffers).
5. **Milestone 5**: Staged Anomaly Engine (V1 post-run chunk analyzer & V2 in-process anomaly counters).
6. **Milestone 6**: Production Watchdog & Balance Profile Decoupling (V2 `WatchdogDaemon` and YAML balance profile loader).


