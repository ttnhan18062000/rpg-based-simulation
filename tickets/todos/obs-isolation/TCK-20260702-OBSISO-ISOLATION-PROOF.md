---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260702-OBSISO-ISOLATION-PROOF
phase: open
date: 2026-07-02
tags: [performance, observability, simulation-quality, benchmark, queue-drops, regression-guard]
---

# TCK-20260702-OBSISO-ISOLATION-PROOF

## Title
Measure and guard engine overhead of SimQ modes; assert zero queue drops in calibration runs

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Requirement R1 ("engine performance not affected by external components") is currently asserted by contract, not proven by measurement. In-process SimQ shares the GIL with the engine; broker mode moves scoring out of process — neither cost is quantified. Separately, `BoundedObservabilityQueue` drops envelopes on overflow, and a drop during a calibration run silently degrades SimQ grades — the calibration/evaluation harness does not check `dropped_count`. Produce the benchmark, document the budget, and add the drop guard.

## Scope
- Benchmark harness: same scenario + seed (reuse a fast calibration anchor scenario, e.g. a 200-tick sandbox_world run) executed under three configs: (a) `QUALITY_SCORING_DISABLED=1`, (b) in-process mode, (c) broker mode with `QualityWorker` in a second process. Measure wall-clock ticks/sec and engine-process CPU time. Extend `tests/simulation_quality/test_performance.py` or add `tools/` script + a `slow`-marked test, following `docs/performance/perf_baseline_policy.md` conventions (hardware-class awareness, no absolute-time assertions on CI).
- Document results in `docs/performance/` (or the perf baseline policy's designated location): overhead budget table per mode, with the measured numbers and machine class.
- Regression guard: relative assertion in the slow lane — in-process SimQ overhead vs disabled stays under an agreed ratio (derive the threshold from measurement, then lock it; per perf policy, band-tolerance not exact).
- Queue-drop guard: `tools/calibrate_simq.py` and `tools/evaluate_simq.py` fail (or loudly warn + mark the run invalid) if `dropped_count > 0` or backpressure mode left NORMAL during the run — surface via existing `observability_status()` / `EventRecorder.pressure_report()` accessors.
- Verify SURVIVAL-mode interaction: when backpressure forces SURVIVAL, SimQ receives nothing — assert the run is flagged rather than silently graded.

## Out of Scope
- Optimizing any component (measurement first; findings become follow-up tickets)
- CI hardware provisioning changes
- Multi-run statistical benchmarking beyond the perf baseline policy's existing method

## Acceptance Criteria
- Benchmark runs produce a committed results table (docs) with ticks/sec and engine CPU for all three modes on at least one hardware class.
- Broker mode shows engine-process CPU within the agreed band of the disabled baseline (target from `docs/plans/observability_process_isolation.md` R1; exact band set from first measurement).
- `make evaluate` on a run with forced queue overflow (test-injected small queue size) fails/flags instead of producing grades.
- New tests pass in the `slow` lane; fast lanes unaffected.
- Perf baseline policy doc references the new benchmark; parity ledger `infrastructure.yaml` entry added for the drop guard.

## Related Tickets
TCK-20260702-OBSISO-BROKER-CONFIG + TCK-20260702-OBSISO-WORKER-PARITY (prerequisites — broker mode must work end-to-end to benchmark it), TCK-20260702-OBSISO-TRACE-ASYNC (its fix is part of what "off" vs "on" measures), TCK-20260702-OBSISO-EPIC

## Related Docs
docs/plans/observability_process_isolation.md (G5, §4.3, §4.4), docs/performance/perf_baseline_policy.md, docs/architecture/observability_hot_path_safety_contract.md (§5 backpressure), docs/engine/performance_contract.md

## Related Stored Artifacts
stored_artifacts/TCK-20260702-SIMQ-EVAL-HARNESS (evaluate harness design)

## Related Code Areas
tests/simulation_quality/test_performance.py, tools/calibrate_simq.py, tools/evaluate_simq.py, src/observability/queue.py (dropped_count), src/observability/event_recorder.py (pressure_report, observability_status), Makefile (evaluate targets)

## Assumptions / Open Questions
- Assumption: existing 200-tick anchor scenarios are long enough to produce a stable throughput signal; if noise dominates, use the 1000-tick anchors in the slow lane only.
- Open: whether the drop guard should hard-fail `make evaluate` or mark-and-continue — default to hard-fail for calibration (`calibrate_simq.py`) and warn for ad-hoc evaluation, unless maintainer prefers otherwise.

## Implementation Notes
Both dev machines are CPU-only; benchmark methodology must not assume GPU or containers. For the broker-mode measurement, launch `QualityWorker` via subprocess with env overrides and a fakeredis/real-redis fixture consistent with whatever TCK-20260702-OBSISO-BROKER-CONFIG establishes for integration tests.

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
