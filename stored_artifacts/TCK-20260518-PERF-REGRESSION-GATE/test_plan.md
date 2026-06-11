---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260518-PERF-REGRESSION-GATE
artifact_type: test_plan
tags: [perf, regression, gate]
---

# Test Plan - PerfRegressionGate

## Automated Unit Tests
File: `tests/unit/perf/test_perf_regression_gate.py`

### Test Cases
1. `test_perf_gate_passes_within_threshold`:
   - Initialize baseline and current results where current metrics are identical or slightly better/within 5% tolerance.
   - Verify `result.passed is True` and `reasons` is empty.
2. `test_perf_gate_fails_when_p95_regresses_too_much`:
   - Set current `p95_tick_compute_ms` to 20ms vs baseline 10ms (100% regression > 10% tolerance).
   - Verify `result.passed is False` and `reasons` contains "p95_tick_compute_ms".
3. `test_perf_gate_fails_when_phase_regresses_too_much`:
   - Set current `phase_p95_ms["movement"]` to 15ms vs baseline 5ms.
   - Verify `result.passed is False` and `reasons` highlights "Phase 'movement'".
4. `test_perf_gate_fails_when_memory_regresses_too_much`:
   - Set current `peak_rss_mb` or `memory_delta_mb` significantly higher than baseline.
   - Verify `result.passed is False` and `reasons` highlights memory regression.
5. `test_perf_gate_ignores_wall_clock_tps_for_compute_regression`:
   - Set current `wall_clock_tps` to 10 vs baseline 1000 (huge wall-clock drop due to OS noise). Keep `compute_tps` within tolerance.
   - Verify `result.passed is True`, proving complete isolation from non-deterministic wall-clock variance.
6. `test_missing_baseline_fails_in_ci_mode`:
   - Pass `baseline=None` to gate initialized with `ci_mode=True`.
   - Verify `MissingBaselineError` is raised.
7. `test_missing_baseline_warns_or_skips_in_local_mode`:
   - Pass `baseline=None` to gate initialized with `ci_mode=False`.
   - Verify `result.passed is True` and `warnings` contains a notice about missing baseline in local mode.

## Verification
- Run `pytest tests/unit/perf/test_perf_regression_gate.py`
