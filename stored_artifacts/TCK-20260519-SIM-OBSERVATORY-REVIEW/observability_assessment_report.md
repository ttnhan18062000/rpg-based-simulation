---
content_type: doc
status: historical
layer: observability
authority: P2
audience: agent
tags: [sim, observatory, review]
---

# Current-State Observability Assessment for Simulation Observatory (Phase 1)

## Executive Summary
This report presents a thorough investigation of the observability architecture within the V2 RPG simulation engine. The investigation audited event logging, metrics telemetry, certification harnesses, simulation invariants, anomaly detection, and centralized observability infrastructure (Loki/Promtail and Prometheus/Grafana).

### Critical Blockers Identified
1. **Loki High-Cardinality Stream Explosion**: `promtail-config.yml` explicitly extracts `tick` from JSON logs and promotes it into a Loki stream label (`labels: tick:`). In long simulations (10,000+ ticks), this causes catastrophic index fragmentation and memory exhaustion in Loki indexers.
2. **Zero Prometheus Metric Export in Production**: All Prometheus metrics (`sim_current_tick`, `sim_active_entities`, etc.) exist exclusively in legacy code (`src_legacy/utils/metrics.py`). The active V2 FastAPI server (`src/api/server.py`) and worker daemons do not mount a `/metrics` route. Prometheus receives HTTP 404, resulting in completely empty Grafana dashboards in production.

---

## Section A: Inventory of Existing Event & Logging Mechanisms

### 1. Mechanisms Found
- **`TraceEvent` (`src/core/diagnostic.py`)**: Experimental diagnostic trace record. Dataclass with `tick`, `system`, `event_type`, `payload: Dict[str, Any]`, and `causal_id`. Emitted by `Kernel._phase_apply` and `_phase_persistence` (`src/engine/kernel.py`) and written to JSON chunk files by `ReplayManager`.
- **`JsonFormatter` (`src/logging/formatter.py`)**: Structured JSON logging formatter using thread-local storage (`_log_context`) to attach `tick`, `component`, `worker_id`, `entity_id` to standard Python log records.
- **`IntentResult` (`src/core/state.py`)**: Dataclass recording resource transfer intent outcomes (`transaction_id`, `accepted`, `reason`, `source_kind`, `source_id`).
- **`RejectionEvent` (`src/core/updates.py`)**: Dataclass capturing authoritative action rejections (`tick`, `actor_id`, `action_kind`, `reason`, `target_id`). Recorded in `rejection_registry`.
- **`transaction_trace` (`src/engine/metrics.py`)**: Observation-only string log appended by `ResourceTransactionResolver` summarizing economic trades.

### 2. Major Gaps
- Subsystems like combat (`src/engine/combat.py`) and social (`src/systems/social_systems/relationships.py`) emit unstructured Python log strings (`logger.info`, `logger.warning`) instead of structured events.
- Replay trace payloads contain deeply nested dictionary representations of state updates without deterministic schema validation.

---

## Section B: Inventory of Watchdog & Certification Mechanisms

### 1. Mechanisms Found
- **`CertificationHarness` (`src/certification/harness.py`)**: Executes scenario runs under strict runtime profiles.
- **`CertificationRecorder` (`src/certification/recorder.py`)**: Produces structured JSON bundles and Markdown release proof reports (`reports/release_proof/`).
- **Watchdog Daemon (`src/utils/watchdog.py`)**: Configured in `docker-compose.yml`. Note: In the active V2 codebase (`src/`), `src/workers/` and `src/utils/` do not exist. The worker daemon and watchdog files exist exclusively at `src_legacy/workers/ai_worker_daemon.py` and `src_legacy/utils/watchdog.py`.

### 2. Detected Conditions
- `ArenaStopCondition` (`src/certification/models.py`): Detects `WIPE` (all entities dead), `TIMEOUT` (max ticks reached), `STALL` (no state evolution/debt progress), `WATCHDOG` (tick execution hang exceeding thread pool timeout), `MANUAL`.
- Fast-Tick Watchdog: Detects if 100 consecutive ticks execute in <0.1ms.

### 3. Representation & Gaps
- Legacy watchdog (`src_legacy/utils/watchdog.py`) scrapes `http://backend:8000/metrics` for `sim_current_tick`, but because FastAPI (`src/api/server.py`) does not expose `/metrics`, it fails with HTTP 404 and triggers continuous `SYSTEM_CRITICAL` failures.

---

## Section C: Inventory of Metrics & Runtime Telemetry

### 1. Mechanisms Found
- **`SignalCollector` (`src/engine/observability.py`)**: Samples system RSS memory via `psutil` every N ticks and computes 5-sample rolling memory slope. Captures `RuntimeSnapshot` (worker utilization, queue utilization, dropped work delta).
- **`RuntimeStatus` (`src/engine/runtime_status.py`)**: Retains a bounded `deque(maxlen=100)` of `PressureSignals` (work debt, tick compute ms, phase cost breakdown).
- **`WorldMetrics` (`src/engine/metrics.py`)**: Semantic metrics snapshot extracted per tick (`alive_entities`, `total_gold`, `total_trauma`, `avg_influence`, `rejection_counts`, `quest_status_counts`, `transaction_trace`).
- **`BenchHarness` (`src/perf/bench_harness.py`)**: High-frequency benchmarking harness calculating exact latency distributions (`p50`, `p95`, `p99`, `max`, `min`).

### 2. Gaps
- Telemetry snapshots and percentiles (`p50`, `p95`, `p99`) are only calculated inside isolated benchmarking or certification harnesses (`BenchHarness`, `LongRunStabilityHarness`). In standard API server operation, `Kernel._record_runtime_signals()` records phase costs to `RuntimeStatus`, but these metrics are never exposed or aggregated across windows for external visualization.

---

## Section D: Centralized Logging & Loki Readiness

### 1. High-Cardinality Risks (Critical Blocker)
- `promtail-config.yml` (lines 33-36) contains a pipeline stage that explicitly extracts `tick` from JSON logs and promotes it into a Loki stream label (`labels: tick:`). In long simulation runs (e.g. 10,000+ ticks), indexing `tick` as a label causes catastrophic stream index fragmentation, cardinality explosion, and memory exhaustion in Loki indexers.

### 2. Recommendations
- `tick`, `entity_id`, `target_id`, `quest_id`, `region_id`, and `worker_id` must remain as structured JSON log fields (`log context`), never stream labels. Stream labels must be strictly confined to low-cardinality metadata (`environment`, `container`, `component`, `level`). Grafana panels successfully unpack JSON fields dynamically via `{container=~"backend|ai_worker"} | json` without needing them as indexed stream labels.

---

## Section E: Centralized Metrics & Grafana Readiness

### 1. Current Export Path Gaps (Critical Blocker)
- `simulation.json` expects 20+ PromQL metric queries (`sim_current_tick`, `sim_active_entities`, `sim_ticks_per_second`, `sim_calamity_active`, `sim_faction_population`, `sim_gold_circulation_total`, `sim_errors_total`, etc.).
- **Zero Export Path**: All these Prometheus metrics exist exclusively in `src_legacy/utils/metrics.py`. The active V2 FastAPI server (`src/api/server.py`) and worker daemons do not import `prometheus_client` and do not mount a `/metrics` endpoint. When Prometheus scrapes `backend:8000/metrics` (configured in `prometheus.yml`), it receives HTTP 404 Not Found. Every Grafana panel returns "No data" in production.

---

## Section F: Simulation Laws & Hard Invariants

### 1. Mechanisms Found
- **`LegalityServiceV2` (`src/engine/legality.py`)**: Authoritative simulation laws verified before action resolution. Enforces Manhattan distance metric (`COMB-001`), tile occupancy (`COMB-002`, `COMB-003`, `COMB-198`), action readiness (`COMB-266`), movement readiness/terrain gating, melee engagement adjacency (`COMB-004`, `COMB-256`), ranged LoS (`COMB-005`), and skill stamina cost (`PROG-077`).
- **`ResourceTransactionResolver` (`src/core/conservation.py` & `src/engine/economy.py`)**: Enforces the Atomic Conservation Law (source depletion and destination receipt occur atomically or not at all), inventory capacity/slot/weight limits (`TOWN-011`), exactly-once idempotency (`E5.3`), and shop gold liquidity (`ECON-201`).

### 2. Enforcement vs Testing vs Monitoring
- *Runtime Enforced*: Tile occupancy, movement stamina gating, resource conservation, idempotency, and read-only state isolation (`Kernel._guard_stability`).
- *Missing Runtime Monitoring*: There is no active runtime monitor (`HardLawMonitor`) continuously validating global invariants (e.g. total world gold conservation, zero entity duplication, zero negative attributes) at the end of every tick.

---

## Section G: Strange-Event & Anomaly Detection Opportunities
- **Stuck Entities**: Position unchanged for >50 ticks while navigation intent is active. Signal: `EntityState.navigation.position`.
- **Oscillating Movement**: Bouncing between 2 adjacent tiles repeatedly over 10+ ticks. Signal: Position history in movement cache.
- **Repeated Failed Action**: Same entity encountering >5 consecutive action rejections (e.g. `INSUFFICIENT_READINESS`, `OUT_OF_RANGE`) in `rejection_registry`.
- **Resource-Node Crowding**: >8 entities targeting the same single `ResourceNode` simultaneously. Signal: `ResourceTransferIntent` target analysis.
- **Economy Freeze**: Zero shop transactions or gold circulation occurring over 500+ consecutive ticks. Signal: `WorldMetrics.transaction_trace`.
- **Combat Never Ends**: Engagement active between same entities for >200 ticks without HP change or resolution. Signal: `state.engagements`.

---

## Section H: Long-Run Simulation Readiness & Compaction Mechanics
- **Assessment**: The engine is architecturally designed for stability: bounded buffers (`src/core/retention.py`), DirtySet optimization (`src/core/dirty.py`), deterministic RNG, and aggressive compaction in `StateUpdateCompactor.compact` (`src/engine/compactor.py`), which filters out redundant updates and cosmetic FX during high compute load.
- **Blockers**: Promtail high-cardinality `tick` label index explosion; zero Prometheus metrics export for monitoring memory/latency drift in production; replay buffer disk I/O serialization overhead in unthrottled dense worlds.
- **Required Evidence for Long-Run Stability Claim**: Empirical proof via `LongRunStabilityHarness.execute_run` verifying peak RSS growth <= 2.0x baseline, latency drift <= 1.5x initial p95, and zero memory leaks over a 50,000-tick continuous scenario.

---

## Section I: Balance Profile & Scenario Expectations Readiness
- **Mechanisms Found**: `ScenarioExpectations` (`src/certification/models.py` line 62) models scenario pass criteria: `required_governor_modes`, `max_recovery_ticks`, `allowed_failure_kinds`, `allowed_profiles` (`standard_gaming_profile`). Registered in `src/certification/scenarios.py`. Runtime profiles exist in `src/config/profiles.py` (`PROD_SMALL`, `PROD_DEFAULT`, `PROD_LARGE`, `PROD_STRESS`) and `src/perf/profiles.py`.
- **Gaps**: Thresholds and scenario expectations are currently hardcoded in Python dictionaries (`scenarios.py` and `profiles.py`). There is NO external YAML/JSON balance profile configuration loader.
- **Recommendation**: Implement a YAML schema loader in `src/config/` to decouple balance profiles and scenario expectations from Python source code.
