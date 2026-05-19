# Phase 1 Observability Foundation

This document details the architectural foundation and execution progress of Phase 1 Observability for the V2 RPG Simulation Engine.

## Completed Milestones

### Milestone 0: Safety Baselines established
Captured empirical pre-observability compute costs, transaction performance (TPS), and deterministic final state hashes to ensure that adding observability features introduces zero performance or replay regressions:
- Standard benchmark smoke tests run cleanly via `python3 scripts/run_benchmarks.py --smoke`.
- Complete 9-scenario performance profile established and stored at [baselines/latest.json](file:///home/vboxuser/Work/rpg-based-simulation/docs/observability/baselines/latest.json).
- Pre-observability Git commit anchor: `0da5d3daaa2fcef3df80acebfe14650e5c45fe5f`.
- Confirmed that the Prometheus `/metrics` endpoint is not yet mounted (returns HTTP 404), preserving baseline behavior.

### Milestone 2: Loki Label Cardinality Hardening complete
Corrected the relabel pipeline stages in `promtail-config.yml` to prevent dynamic keys (like `tick` and `entity_id`) from exploding Loki's index streams:
- Removed `tick` from stream labels inside [promtail-config.yml](file:///home/vboxuser/Work/rpg-based-simulation/promtail-config.yml).
- Ensured `JsonFormatter` in [formatter.py](file:///home/vboxuser/Work/rpg-based-simulation/src/logging/formatter.py) serializes these attributes directly to the message body.
- Authored [loki_label_policy.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/observability/loki_label_policy.md) detailing the querying standard.
- Implemented static verification checks in [test_loki_cardinality.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/logging/test_loki_cardinality.py).

### Milestone 1: Prometheus Metrics Export Mounted
Mounted Prometheus `/metrics` endpoint using `prometheus_client` multiprocess or registry collectors:
- Exposed FastAPI `/metrics` route in [server.py](file:///home/vboxuser/Work/rpg-based-simulation/src/api/server.py).
- Exported critical platform signals and engine status indicators: `rpg_engine_tick_duration_seconds`, `rpg_engine_active_workers`, `rpg_engine_total_ticks`, `rpg_engine_errors_total`, and `rpg_engine_tick_latency_seconds`.
- Configured high-performance Prometheus multiprocessing storage support.
- Fully verified via [test_metrics_export.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/observability/test_metrics_export.py).

### Milestone 3: Hard Law Invariant Monitor Integrated
Designed and integrated the real-time simulation invariant checker `HardLawMonitor` in [hard_law_monitor.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/hard_law_monitor.py):
- Integrated invariant check executions directly in the kernel pipeline `_phase_observability`.
- Codified 6 critical hard law validation checks (ticking, gold bounds, combat limits, quest limit).
- Exported validation failure telemetry through Prometheus counter `rpg_observability_failures_total`.
- Fully tested using [test_metrics_export.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/observability/test_metrics_export.py).

### Milestone 4: WebSocket Real-Time Event Streams Established
Designed and implemented the structured `SimulationEvent` streaming pipeline:
- Defined rigid Pydantic models for structured lifecycle, combat, quest, and movement events in [events.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/events.py).
- Integrated `timeline` sliding event buffer on `EntityState` using memory-efficient double-ended queues.
- Mounted high-performance real-time WebSocket route `/api/v1/ws/observe` in [stream.py](file:///home/vboxuser/Work/rpg-based-simulation/src/api/ws/stream.py) with full protocol negotiation, client pacing, and server-side filtering.
- Fully tested via [test_events_timeline.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/observability/test_events_timeline.py) and [test_websocket_stream_events.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/observability/test_websocket_stream_events.py).

## Status
All milestones are 100% completed, hardened, and verified via extensive automated test coverage. Phase 1 Observability is fully certified.

