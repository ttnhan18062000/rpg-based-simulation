# Performance Hardening Test Plan

## Performance Tests
- `tests/perf/test_perf_passive_scaling.py`: Scaling test with 100, 1000, 5000 entities.
  - Measure Avg TPS, p95 Latency, and Max RSS.
  - Baseline: p95 < 50ms for 100 entities.

## Regression Tests
- `tests/integration/pipeline/test_authoritative_apply.py`: Ensure pipeline determinism.
- `tests/unit/core/test_authoritative_state_contract.py`: Ensure immutability.

## Automated Verification
- Run `pytest` on all affected areas.
- Compare throughput before/after optimization (Target: 2-3x improvement for idle state).
