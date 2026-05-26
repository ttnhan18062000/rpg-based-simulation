# Plan — Milestone 41: Production Readiness Validation

## Objective
Prove the V2 Observatory platform works without damaging the engine via failure injection, overhead benchmarks, and formal readiness reporting.

## Approach
We will implement 4 test files as specified in the phase 7 spec, plus a `ProductionReadinessHarness` that orchestrates scenario execution and report generation.

### Test Files
1. `tests/perf/test_production_observatory_overhead.py` — Runs kernel ticks with and without observatory enabled, measures p95 overhead
2. `tests/integration/test_observatory_stream_outage.py` — Simulates Redis unavailable, verifies engine continues, backpressure visible, alerts generated
3. `tests/integration/test_observatory_warehouse_outage.py` — Simulates ClickHouse unavailable, verifies local artifacts preserved, engine continues
4. `tests/integration/test_anomaly_worker_failure.py` — Simulates worker crash, verifies engine continues, worker status shows failed, alert generated

### Harness
- `src/observability/readiness/harness.py` — `ProductionReadinessHarness` orchestrates scenario runs and collects results
- `src/observability/readiness/report.py` — `ReadinessReportGenerator` formats collected results into a markdown report
