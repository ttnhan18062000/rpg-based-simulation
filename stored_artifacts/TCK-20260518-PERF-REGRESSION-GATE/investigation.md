# PerfRegressionGate Investigation

## Context & Problem
To ensure performance gains are preserved across ongoing development, the engine requires a formal automated regression gate (`PerfRegressionGate`). While `BenchHarness` generates detailed metrics (p95, p99, peak RSS, memory delta, phase breakdown, compute TPS), there is currently no structural mechanism comparing these results against committed baselines.

Additionally, comparisons must strictly evaluate deterministic compute metrics (`compute_tps`, compute tick ms) rather than noisy wall-clock metrics (`wall_clock_tps`), and CI environments must never silently pass if a baseline file is missing or unreadable.

## Technical Details
We will define the following models:
- `PerfBaseline`: Holds committed baseline figures for p95, p99, peak RSS, memory delta, compute TPS, raw vs compacted updates, and phase p95 breakdowns.
- `PerfResult`: Holds the newly benchmarked metrics (structured identically or parsed from `BenchHarness.run_benchmark` dict).
- `PerfGateResult`: Represents the outcome (`passed: bool`, `reasons: List[str]`, `warnings: List[str]`).

## Gate Logic
In `PerfRegressionGate(ci_mode: bool = True, tolerance_percent: float = 10.0)`:
1. If `baseline` is None or incomplete:
   - If `ci_mode` is True: raise `MissingBaselineError("CI cannot silently skip missing baseline")` or return failed result.
   - If `ci_mode` is False: return `PerfGateResult(passed=True, warnings=["Missing baseline in local mode; skipping verification"])`.
2. Compare metrics with tolerance:
   - `p95_tick_compute_ms`: current <= baseline * (1 + tolerance/100)
   - `p99_tick_compute_ms`: current <= baseline * (1 + tolerance/100)
   - `peak_rss_mb`: current <= baseline * (1 + tolerance/100)
   - `memory_delta_mb`: current <= baseline + max(5.0, baseline * (tolerance/100))
   - `compute_tps`: current >= baseline * (1 - tolerance/100)
   - Phase-level p95 costs: for each phase, current_phase_p95 <= baseline_phase_p95 * (1 + tolerance/100)
   - `wall_clock_tps`: explicitly ignored for pass/fail decisions.
3. If any threshold is breached, record the specific discrepancy and set `passed=False`.
