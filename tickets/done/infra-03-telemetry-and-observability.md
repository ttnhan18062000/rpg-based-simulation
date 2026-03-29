# [DONE] infra-03: Production Telemetry and Observability

## Objective
Instrument the `WorldLoop` and FastAPI layer with OpenTelemetry traces and Prometheus metrics to eliminate performance guesswork.

## Rationale
Standard terminal logging is insufficient to detect sub-component degradation over thousands of ticks or narrow down sporadic latency spikes. If the simulation stalls at tick 120,400, we need trace spans to identify exactly which AI phase (Schedule, Collect, Resolve, Cleanup) failed.

## Scope & Affected Systems
- **Target Files**: `src/engine/world_loop.py`, `src/api/app.py`, `src/api/routes/state.py`.
- **Implementation Steps**:
  1. Add `opentelemetry-api` and `prometheus_client` to `requirements.txt`.
  2. In `src/api/app.py`, initialize the OpenTelemetry meter provider and expose `/metrics` endpoint using `prometheus_client.make_asgi_app()`.
  3. In `src/engine/world_loop.py`, instrument `_step()` to record phase durations (scheduling, collect, resolve, subsystem) as histogram metrics.
  4. Track business logic metrics: `ticks_per_second`, `action_queue_latency_ms`, and `active_entities`.

## Dependencies
- Non-blocking. Can be implemented concurrently with other infrastructure tasks. Highly recommended before `infra-05` (Multiprocessing) to establish a performance baseline.

## Acceptance Criteria
- `/metrics` endpoint correctly resolves in standard Prometheus format.
- Spans successfully emit to an OpenTelemetry collector or console exporter.
- Tick performance overhead remains negligible (< 2ms added per tick).
