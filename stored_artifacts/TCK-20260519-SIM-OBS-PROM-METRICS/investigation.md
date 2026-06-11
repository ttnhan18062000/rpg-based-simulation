---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260519-SIM-OBS-PROM-METRICS
artifact_type: investigation
tags: [sim, obs, prom, metrics]
---

# Observability Milestone 1 Investigation

Researching and documenting core metric sources and exporter patterns.

## 1. Concurrency and Thread Safety

The FastAPI application server and the V2EngineManager simulation loop run in different threads:
- **Engine Loop Thread**: Created as `v2-engine-loop` by `V2EngineManager.start()`. It performs periodic execution (`self._kernel.tick_once()`) and updates state snapshot.
- **Request Threads**: Spawned by FastAPI (and Uvicorn) to handle HTTP traffic (including `GET /metrics`).

### Thread Isolation Strategy
To prevent requests from blocking the engine loop or causing locking contention:
- At the end of every simulation tick, the engine thread extracts a metrics snapshot containing:
  - RuntimeStatus signals (RSS, compute latencies, queue and worker stats)
  - WorldMetrics (alive entities count, total gold)
- This snapshot is stored in `V2EngineManager` as an immutable data structure.
- When `GET /metrics` is called, the request thread fetches this cached snapshot and maps it to Prometheus metric formats.
- Reading this snapshot is an O(1) operation guarded by `self._state_lock` (or atomic pointer assignment). This avoids lock starvation of the engine thread.

## 2. Metrics Availability and Mapping

All P0 and P1 metrics requested can be mapped from existing objects:

| Metric Name | Prometheus Type | Source in V2 Engine / Kernel |
| --- | --- | --- |
| `sim_current_tick` | Gauge | `self._state.tick` |
| `sim_active_entities` | Gauge | `MetricsService.extract_metrics(self._state).alive_entities` |
| `sim_ticks_per_second` | Gauge | Computed using sliding window timestamps of the last 100 ticks |
| `sim_tick_compute_ms` | Gauge | `self._status.signal_history[-1].tick_compute_ms` |
| `sim_worker_utilization` | Gauge | `self._status.signal_history[-1].worker_utilization` |
| `sim_queue_utilization` | Gauge | `self._status.signal_history[-1].queue_utilization` |
| `sim_memory_rss_bytes` | Gauge | `self._status.signal_history[-1].memory_estimate_mb * 1024 * 1024` |
| `sim_work_debt_total` | Gauge | `self._status.signal_history[-1].work_debt_total` |
| `sim_governor_mode` | Gauge | `self._status.current_mode` (IntEnum value) |
| `sim_gold_circulation_total` | Gauge | `MetricsService.extract_metrics(self._state).total_gold` |
| `sim_rejection_count_total` | Gauge | `state.rejection_registry` labeled by reason |
| `sim_quest_status_count` | Gauge | `MetricsService.extract_metrics(self._state).quest_status_counts` labeled by status |
| `sim_dropped_work_delta` | Gauge | `self._status.signal_history[-1].dropped_work_delta` |
| `sim_errors_total` | Counter | Cumulative tick exceptions count |
| `sim_phase_duration_seconds` | Gauge | `self._status.signal_history[-1].phase_costs_ms` / 1000.0 labeled by phase |

## 3. Exporter Pattern and Registry Safety

Standard `prometheus_client` default registry (`prometheus_client.REGISTRY`) is globally shared. This is highly vulnerable to double-registration errors if unit tests or live reloads construct multiple instances of `V2EngineManager`.
To solve this, each `V2EngineManager` holds its own private `CollectorRegistry` instance.
FastAPI resolves the manager dependency and generates the latest metric payload using the manager's private registry:
```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

@app.get("/metrics")
async def get_metrics(manager: V2EngineManager = Depends(get_engine_manager)):
    data = generate_latest(manager.metrics_registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
```
This guarantees isolation, safety under concurrent test runs, and zero side-effects.
