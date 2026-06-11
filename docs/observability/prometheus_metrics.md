---
status: active
layer: observability
authority: P1
audience: developer
---

# Prometheus Metrics Telemetry Specification

The V2 Simulation Engine exposes a standard `/metrics` endpoint serving Prometheus-compatible text representation of live telemetry data.

## 1. Zero-Blocking Thread Architecture

To maintain the strict performance and determinism requirements of the RPG engine:
- The `/metrics` endpoint is serviced entirely from a cached telemetry snapshot updated at the end of every simulation tick on the engine loop thread.
- Scrape requests perform an O(1) read of this snapshot under light locking (`_state_lock`), ensuring that scraping never blocks the tick execution thread.
- Standard default registries are bypassed in favor of a private `CollectorRegistry` instance bound to each `V2EngineManager` instance, ensuring safe resets and preventing duplicate registration errors.

## 2. Exported Metric Reference

All duration-based metrics are exported in **seconds** in accordance with standard Prometheus conventions.

### P0 Metrics (Core Health & Load)

| Metric Name | Type | Description | Labels |
| --- | --- | --- | --- |
| `sim_current_tick` | Gauge | Current simulation tick index. | None |
| `sim_active_entities` | Gauge | Number of active (alive) entities in the state. | None |
| `sim_ticks_per_second` | Gauge | Empirical ticks completed per second over the last 100 ticks. | None |
| `sim_tick_compute_ms` | Gauge | Compute latency of the last completed tick in milliseconds. | None |
| `sim_worker_utilization` | Gauge | Active worker threads utilized vs max pool capacity. | None |
| `sim_queue_utilization` | Gauge | Thread pool task queue utilization ratio. | None |
| `sim_memory_rss_bytes` | Gauge | Resident Set Size (RSS) memory footprint of the simulation process. | None |
| `sim_work_debt_total` | Gauge | Total outstanding system work debt (D1, D2, ...). | None |
| `sim_governor_mode` | Gauge | Active governor mode mapping: `0=NORMAL`, `1=CONSTRAINED`, `2=DEGRADED`, `3=SURVIVAL`. | None |
| `sim_gold_circulation_total` | Gauge | Total gold in circulation across all entity inventories. | None |

---

### P1 Metrics (Detailed Behavioral Telemetry)

| Metric Name | Type | Description | Labels |
| --- | --- | --- | --- |
| `sim_rejection_count_total` | Gauge | Cumulative counts of rejected actions grouped by rejection code. | `reason` |
| `sim_quest_status_count` | Gauge | Active quests in the simulation grouped by current lifecycle state. | `status` |
| `sim_dropped_work_delta` | Gauge | Work items shed in the current tick. | None |
| `sim_errors_total` | Counter | Cumulative simulation tick loop execution errors. | None |

---

### Phase Duration Telemetry

Phase duration tracking allows deep visibility into where compute budget is spent inside the deterministic 17-phase execution pipeline.

- **Metric**: `sim_phase_duration_seconds{phase="..."}`
- **Type**: Gauge
- **Approved Labels (`phase`)**:
  - `init`
  - `scheduling`
  - `collection`
  - `resolution`
  - `cleanup`
  - `advancement`
  - `persistence`
  - *Other specific engine execution sub-phases*
