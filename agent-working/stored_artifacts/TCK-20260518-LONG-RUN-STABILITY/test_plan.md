---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260518-LONG-RUN-STABILITY
artifact_type: test_plan
tags: [long, run, stability]
---

# Test Plan: Long-Run Stability Certification (Milestone 18)

## 1. Test Targets
- `LongRunStabilityHarness` in `src/perf/long_run_harness.py`.
- `tests/certification/test_cert_long_run_stability.py`.

## 2. Automated Test Cases
1. **`test_long_run_pure_stability`**:
   - Initializes 1,000 entities in `metropolis` scenario.
   - Runs 5,000 ticks in `PURE` mode (governor disabled).
   - Asserts peak RSS < 512MB, memory delta ratio < 2.0.
   - Asserts p95 latency drift ratio < 1.5.
   - Asserts cache sizes remain bounded.
2. **`test_long_run_runtime_stability`**:
   - Initializes 1,000 entities in `mixed` scenario.
   - Runs 5,000 ticks in `RUNTIME` mode (governor enabled).
   - Asserts governor active throttling under pressure.
   - Asserts peak RSS and p95 latency bounds.
3. **`test_long_run_determinism`**:
   - Runs two identical 1,000-tick runs with 500 entities.
   - Asserts exact hash parity across all ticks and final shutdown state.

## 3. Execution Scope
Run via pytest:
```bash
pytest -s tests/certification/test_cert_long_run_stability.py
```
