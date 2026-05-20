# Test Plan - TCK-20260520-SIM-OBS-M37

## Automated Verification

### 1. Unit Tests (`tests/unit/observability/test_live_anomaly_worker.py`)
- **Config Validation**: Assert that `LiveWorkerConfig` parses and validates valid/invalid inputs.
- **Rolling Window Eviction**: Validate that events older than the configured `window_ticks` are evicted correctly and memory remains bounded.
- **Deduplication Cooldown**: Assert that duplicate alerts are suppressed within the cooldown period and allowed once it expires.
- **Rule Implementations**:
  - `HardLawViolationLive`: Feed `InvariantViolation` event, assert anomaly is raised.
  - `NavigationStuckLive`: Feed multiple movement events with identical positions for an entity over time, assert anomaly is raised.
  - `EventDropRateHigh`: Feed multiple drop-related events or exceed target drop counts, assert anomaly is raised.
  - `GovernorDegradedLive`: Feed `GovernorModeChanged` events with `mode="DEGRADED"` and verify anomaly is emitted after 5 ticks of dwell.
  - `CriticalEventObserved`: Feed a critical severity event and assert anomaly is raised.
- **Graceful Fallback**: Mock Redis stream connection failure, assert worker handles disconnect gracefully, reports error to status, and attempts reconnection or falls back.

### 2. Integration Tests
- Instantiate a temporary `LiveAnomalyWorker` alongside a live local running kernel (using the `in_process` or mocked Redis stream adapter).
- Run a short 20-tick simulation where anomalies are deliberately induced.
- Verify that `anomaly_events.jsonl` contains the exact expected notifications and the worker's status file updates with non-zero counts.

## Manual/Ad-Hoc Verification
- Start a mock Redis server and run `perf/long_run_harness.py` with `SIM_STREAM_BACKEND=redis`.
- Run the worker standalone and tail `anomaly_events.jsonl` to ensure live anomalies are outputting in real-time.
