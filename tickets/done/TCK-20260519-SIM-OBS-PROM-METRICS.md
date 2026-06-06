# TCK-20260519-SIM-OBS-PROM-METRICS

## Title

Milestone 1: Prometheus `/metrics` Exporter Route and Telemetry Integration

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Add a standard `/metrics` endpoint to the FastAPI app serving the V2 Engine, exporting P0 and P1 simulation engine performance, resource, and economic indicators.

## Scope

- **Prometheus Metrics Collector Module**:
  - Implement a new `PrometheusMetricsCollector` that safely maps V2EngineManager cached snapshots into Prometheus gauge, counter, and labeled metrics.
  - Implement zero-blocking snapshot reading logic (O(1) lookup during Prometheus scrape).
- **Engine Manager Integration**:
  - Enable `V2EngineManager` to calculate precise real-time TPS using a sliding deque of recent tick timestamps.
  - Enable `V2EngineManager` to periodically extract and cache a `V2EngineMetricsSnapshot` at the end of every tick.
  - Register the metrics collector on a dedicated isolated `CollectorRegistry` instance associated with the manager to prevent hot-restart collisions.
- **FastAPI Endpoints**:
  - Expose `GET /metrics` route on the FastAPI server returning the formatted text representation of the collector registry.
- **Observability Policies Update**:
  - Document all exported metrics inside standard observability documentation.
- **Safety Test Suite**:
  - Develop tests in `tests/observability/test_metrics_export.py` ensuring type-compliance, value correctness, dynamic metric advancement, and crash-safe handling of empty snapshots.

## Out of Scope

- WebSocket event stream data (Milestone 4).
- Timeline deques and historical queries (Milestone 5).
- Invariant checking / HardLawMonitor (Milestone 3).

## Acceptance Criteria

- `GET /metrics` returns standard Prometheus text payload with HTTP 200 OK.
- Scrapes contain all P0 and P1 metrics: `sim_current_tick`, `sim_active_entities`, `sim_ticks_per_second`, `sim_tick_compute_ms`, `sim_worker_utilization`, `sim_queue_utilization`, `sim_memory_rss_bytes`, `sim_work_debt_total`, `sim_governor_mode`, `sim_gold_circulation_total`, `sim_rejection_count_total`, `sim_quest_status_count`, `sim_dropped_work_delta`, `sim_errors_total`, and `sim_phase_duration_seconds`.
- Scrape duration does not block or slow down simulation tick loops.
- Re-instantiating `V2EngineManager` or calling resets does not cause registration collisions.
- Automated metrics integration tests pass successfully.

## Related Tickets

- None

## Related Docs

- `docs/observability/phase_1.md`
- `docs/observability/prometheus_metrics.md`
- `obs_sim_phase1.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260519-SIM-OBS-BASE-LOKI/`

## Related Code Areas

- `src/api/server.py`
- `src/api/engine_manager.py`
- `src/engine/metrics.py`
- `src/observability/prometheus_collector.py`

## Assumptions / Open Questions

- Assumes `prometheus_client` is available in the environment (confirmed successfully installed).
- Zero-overhead footprint is achieved by performing cheap `MetricsService.extract_metrics(state)` at the end of each tick directly on the engine thread and assigning it to a cached field, eliminating expensive O(N) calculations on request threads.

## Implementation Notes

- Avoided global standard `prometheus_client.REGISTRY` to prevent duplicate metric definition exceptions.
- Leveraged a custom `CollectorRegistry` for each manager instance.
- Built a dynamic async test harness `test_metrics_endpoint_direct` in pytest to test route endpoint response logic without the `httpx` module dependency.

## Test Summary

- Ran 4 newly implemented automated unit and integration tests in `tests/observability/test_metrics_export.py` ensuring registry structure, direct async route execution, and full background subprocess integration test over http. All 4 tests passed cleanly (4.29s).
- Ran all performance regression baseline suites (`test_perf_regression_baseline.py` and `test_perf_idle.py`) with zero performance degradation detected.

## Files Changed

- `src/observability/prometheus_collector.py`
- `src/api/engine_manager.py`
- `src/api/server.py`
- `docs/observability/prometheus_metrics.md`
- `tests/observability/test_metrics_export.py`

## Completion Summary

- Implemented standard Prometheus metrics `/metrics` route integrating full P0, P1, and Phase timing diagnostics in the FastAPI server.
- Integrated thread-safe cached telemetry updates and TPS computation at tick completion.
- Authored formal specification doc and passed comprehensive verification suite.
