# Milestone 13 Investigation: Structural Discovery & Proof Instrumentation

## Executive Summary
Milestone 13 of the V2 Performance Roadmap (`perf_plan_v2.md`) requires generating empirical proof reports comparing unoptimized vs optimized performance across core benchmark scenarios. Extensive discovery revealed a critical flaw in existing instrumentation: non-time metrics (like candidate counts) were being placed into phase cost dictionaries, causing the kernel to sum them as nanosecond/millisecond compute durations.

## Key Findings

### 1. Metric Distortion in Kernel
In `Kernel.tick_once()`, total compute duration is calculated as:
```python
self._final_compute_ms = sum(self._phase_costs.values())
```
Because candidate counts (e.g., `movement_candidates = 500`) were added to phase cost dictionaries, `_final_compute_ms` was artificially inflated by hundreds of milliseconds.

### 2. Metric Decoupling Architecture
To resolve this without breaking backward compatibility or deterministic execution:
- `StateUpdate` will receive a new `metric_counters: Dict[str, int]` field.
- `AuthoritativeState` and its caches (`MovementPlanCache`, `WorldIndexService`) will track hit/miss counts.
- `Kernel` will maintain a separate `_metrics: Dict[str, float]` dictionary.
- `PressureSignals` will receive a separate `metrics: Dict[str, float]` field.
- `BenchHarness` will aggregate `metrics` separately from `phase_costs_ms`.

### 3. Historical Baseline Availability
Pristine, pre-optimization baseline data is preserved in `stored_artifacts/TCK-20260512-PERF-COMPLETION/latest.json`. Copying this data to `reports/perf/baseline.json` provides an exact unoptimized baseline for `generate_optimization_proof.py`.
