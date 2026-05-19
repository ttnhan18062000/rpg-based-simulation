# Test Plan - HardLawMonitor V1 & Observability Mode Config

We will construct a comprehensive test suite validating all aspects of the monitor, config, failure policies, and metrics.

## 1. Unit Tests (`tests/engine/test_hard_law_monitor.py`)
- **Clean State**: Verify that clean, valid entities yield zero violations.
- **Negative Attributes**: Verify that negative HP, negative gold, negative stamina, and negative readiness are properly detected.
- **Position Checks**: Verify that non-finite coordinates (NaN/inf) are caught.
- **Deleted Entities**: Verify that deleted or missing dirty entities are ignored safely.
- **Occupancy Collision**: Verify that two dirty moving entities ending on the same tile are caught.
- **Mismatched Occupancy**: Verify that a dirty mover colliding with a clean static entity is caught.
- **Result Schema**: Verify the shape of `HardLawViolation` (contains law ID, entity ID, severity, message, etc.).

## 2. Integration Tests (`tests/integration/observability/test_hard_law_kernel_integration.py`)
- **Kernel Hooking**: Verify that the Kernel runs the `HardLawMonitor` every tick.
- **LIGHT Mode Policy**: Verify that violations only log a warning and increment metrics without failing.
- **DEBUG Mode Policy**: Verify that a violation raises `HardLawViolationError` and interrupts tick execution.
- **CERTIFICATION Mode Policy**: Verify that a violation halts execution and marks the run failed.
- **Persistence Prevention**: Verify that a violation in fail-fast modes prevents saving/committing to persistence.

## 3. Performance Tests (`tests/perf/test_hard_law_monitor_overhead.py`)
- **Benchmarking TPS**: Run a heavy simulation tick benchmark with and without checks to verify overhead is negligible (< 1%).
- **No Global Scans**: Profile the call graph to assert no O(N) full-world scans are made.
