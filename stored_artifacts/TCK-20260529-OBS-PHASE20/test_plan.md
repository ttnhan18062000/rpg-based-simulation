# Test Plan - TCK-20260529-OBS-PHASE20

We will implement unit and integration tests to verify the Phase 20 Runtime Performance Profiling Lane:

## 1. Phase Profiler Unit Tests
Location: `tests/unit/observability/performance/test_phase20_phase_profiler.py`
Verify:
- `PhaseTimingRecord` correctly maps custom fields.
- `PhaseProfiler` profiles a block correctly, measuring actual duration and tracking count updates successfully.
- Exception-safe handling inside `PhaseProfileScope` context manager.
- Low-overhead no-op behavior when `OBS_RUNTIME_PROFILING` flag is disabled.

## 2. Metric Window Extension Unit Tests
Location: `tests/unit/observability/performance/test_phase20_metric_window_extension.py`
Verify:
- Schema compatibility: loading an older `MetricWindowRecord` shape (missing the new optional fields) succeeds with zero issues and safe default values.
- Serialization and deserialization of Extended `MetricWindowRecord` including the phase timings JSON string fields.

## 3. Observability Overhead and Integration Tests
Location: `tests/integration/observability/test_phase20_phase_timing_integration.py`
Verify:
- Integrating `PhaseProfiler` and timing snapshots directly inside a mock simulation pipeline.
- Resolving separate timing reporting for simulation tick/phases vs. observability overhead timing.
