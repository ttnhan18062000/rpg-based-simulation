# Milestone 1: Prometheus Exporter and Core Telemetry

Expose core RPG simulation engine metrics through `/metrics` on the FastAPI server using `prometheus_client`.

## User Review Required

> [!IMPORTANT]
> - **Zero Engine Tick Loop Block**: To adhere strictly to non-blocking runtime rules, the `/metrics` endpoint reads from a thread-safe telemetry snapshot cached in `V2EngineManager` at the end of each tick. No heavy world state scans or lock contentions are triggered on the request thread.
> - **Modular Registry Design**: We will use a dedicated `CollectorRegistry` instance for each `V2EngineManager` instance instead of the global default registry. This prevents duplicate registration errors and avoids cross-test pollution when resetting or starting multiple engine lifespans.

## Proposed Changes

### Observability Foundation

#### [NEW] [prometheus_collector.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/prometheus_collector.py)
Create a new custom Prometheus metric collector `PrometheusMetricsCollector` using standard `prometheus_client` collector APIs.
It collects:
- **P0 metrics**:
  - `sim_current_tick`
  - `sim_active_entities`
  - `sim_ticks_per_second` (computed TPS)
  - `sim_tick_compute_ms` (compute duration of last tick)
  - `sim_worker_utilization`
  - `sim_queue_utilization`
  - `sim_memory_rss_bytes` (RSS memory of the process)
  - `sim_work_debt_total`
  - `sim_governor_mode` (NORMAL=0, CONSTRAINED=1, DEGRADED=2, SURVIVAL=3)
  - `sim_gold_circulation_total` (total gold in world)
- **P1 metrics**:
  - `sim_rejection_count_total{reason="..."}`
  - `sim_quest_status_count{status="..."}`
  - `sim_dropped_work_delta`
  - `sim_errors_total` (exceptions caught)
- **Phase Duration**:
  - `sim_phase_duration_seconds{phase="..."}` (init, scheduling, collection, resolution, cleanup, advancement, persistence, etc.)

---

### Core Simulation API

#### [MODIFY] [engine_manager.py](file:///home/vboxuser/Work/rpg-based-simulation/src/api/engine_manager.py)
Modify `V2EngineManager` to:
- Instatiate and cache a `V2EngineMetricsSnapshot` at the end of every tick on the engine thread.
- Maintain a sliding window of recent tick end times to calculate real-time TPS (ticks completed per second).
- Expose a thread-safe `get_metrics_snapshot()` method.
- Register `PrometheusMetricsCollector` to its dedicated custom `CollectorRegistry`.

#### [MODIFY] [server.py](file:///home/vboxuser/Work/rpg-based-simulation/src/api/server.py)
Register the `GET /metrics` endpoint.
- It will resolve the `V2EngineManager` dependency, access its `CollectorRegistry`, and generate the standard Prometheus exporter text response.

---

## Verification Plan

### Automated Tests
We will add standard unit and integration tests:
- `tests/observability/test_metrics_export.py`

Tests will assert:
1. `GET /metrics` endpoint returns `200 OK` with the `text/plain` content type.
2. The endpoint contains all P0 and P1 metric keys.
3. Metric updates occur dynamically after simulation ticks advance.
4. TPS computation handles paused simulation states correctly (returns `0.0` or doesn't drift).
5. Scrape requests never cause locking or crash when the engine is not yet started or paused.

### Manual Verification
- Execute `curl http://localhost:8000/metrics` and verify Prometheus text compatibility.
