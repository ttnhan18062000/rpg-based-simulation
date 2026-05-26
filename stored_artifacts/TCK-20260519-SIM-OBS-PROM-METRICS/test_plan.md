# Observability Milestone 1 Test Plan

Exhaustive verification of Prometheus `/metrics` exporter route and metric computation.

## 1. Automated Tests

We will create a new test suite: `tests/observability/test_metrics_export.py`.

### Unit Verification

#### Metric Registration & Structure
- Assert that instantiating `V2EngineManager` registers the custom metrics collector to its private registry.
- Assert that calling `generate_latest` on the registry outputs standard, valid Prometheus text format.
- Assert that all P0 and P1 metric keys are present in the output with matching types and HELP/TYPE documentation headers.

#### Telemetry Computations
- **TPS Calculation**: Assert that `get_tps()` starts at `0.0` when no ticks have executed, and accurately reflects tick processing rates once ticks occur. Assert that pauses do not drift the TPS calculation.
- **Gold Circulation & Entity Counts**: Seed the world with a known number of alive entities and distinct inventory gold values. Assert that `/metrics` precisely exports `sim_active_entities` and `sim_gold_circulation_total` matching the ground truth.
- **Governor Mode Mapping**: Transition the governor mode (e.g. NORMAL, CONSTRAINED, DEGRADED) and verify that `sim_governor_mode` matches the integer mapping of the `RuntimeMode` enum.
- **Phase Timing Conversion**: Verify that `sim_phase_duration_seconds` converts millisecond costs from the engine status correctly to seconds, and labels them by phase.

### Integration Verification

#### API Scrape Endpoint
- Launch the FastAPI test client.
- Scrape `GET /metrics` and assert:
  - `status_code == 200`
  - `Content-Type` starts with `text/plain`
  - Body contains valid Prometheus series lines.
- Advance the simulation by a few ticks using the control endpoints and verify that the scrape metrics (like `sim_current_tick`) have updated dynamically.

#### Multi-lifecycle / Registry Collision Test
- Initialize multiple `V2EngineManager` instances in separate tests, simulating reset or hot-reload lifespans.
- Verify that no registration collisions or double-registration crashes occur.

---

## 2. Manual Verification

1. Start the API server locally:
   ```bash
   uvicorn src.api.server:app --reload
   ```
2. Retrieve raw metrics:
   ```bash
   curl -i http://localhost:8000/metrics
   ```
3. Assert that the response returns `HTTP/1.1 200 OK`, `content-type: text/plain; version=0.0.4; charset=utf-8`, and contains all key metric blocks (e.g. `sim_current_tick`).
