---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260817-RUNTIMEMODE-BENCH-SCOPING
phase: open
date: 2026-08-17
tags: [performance, engine, documentation]
---

# TCK-20260817-RUNTIMEMODE-BENCH-SCOPING

## Title
Add RuntimeMode as a required Scoped-Claims dimension and enforce NORMAL-mode sampling in the perf-baseline CI gate

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
performance_contract.md §3.1 requires performance claims to bind to 4 dimensions (Runtime Profile, Hardware Class, Scenario, Execution Mode), none of which is RuntimeMode. RuntimeMode is recorded (long_run_harness.py:225) but never asserted on; the live CI gate (test_perf_regression_baseline.py) computes one blended avg_tick_compute_ms with no RuntimeMode==NORMAL check. A benchmark that degrades mid-run gets cheaper ticks blended into the average, potentially offsetting a real regression — this conflicts with the spirit of certification_contract.md §6's "no modification of kernel laws for benchmark vanity" discipline, which today only applies to full cert runs, not the everyday CI gate. RuntimeMode needs to be added as a required Scoped-Claims dimension, plus enforcement in the perf-baseline test that fails/flags a run if the Governor ever left NORMAL during sampling.

## Scope
- Add RuntimeMode as a required 5th dimension in performance_contract.md §3.1 Scoped Claims (alongside Runtime Profile, Hardware Class, Scenario, Execution Mode)
- Record Governor RuntimeMode per sampled tick inside BenchHarness.run_benchmark()'s tick loop (mirroring long_run_harness.py:225's active_mode pattern), exposed in the result dict (e.g. mode_sequence)
- Make tests/perf/test_perf_regression_baseline.py::test_regression_vs_baseline fail or explicitly non-silently flag when any sampled tick's RuntimeMode != NORMAL, independent of the avg_tick_compute_ms threshold result
- Add a new unit test that forces the Governor out of NORMAL mid-sample and asserts the gate surfaces the excursion rather than silently blending it into the average

## Out of Scope
- Extending PressureSignals (src/core/governance.py) with a mode field — it is explicitly FROZEN (Resource Phase 4 Milestone 1); implement via per-tick sampling inside BenchHarness instead, not a PressureSignals schema change
- Reusing/importing certification's ConformanceEvaluator degradation-order logic wholesale — decide only whether a simpler NORMAL-only assertion suffices for the fast CI gate
- Recalibrating the 26 scenario builders' warmup/sample tick counts, even if some legitimately dip out of NORMAL under real load — flag as a follow-up if found, don't silently loosen the gate to compensate

## Acceptance Criteria
- [ ] performance_contract.md §3.1 Scoped Claims includes RuntimeMode as a required 5th dimension
- [ ] BenchHarness.run_benchmark() (or its caller) records Governor RuntimeMode per sampled tick, exposed in the result dict (e.g. mode_sequence)
- [ ] tests/perf/test_perf_regression_baseline.py::test_regression_vs_baseline fails or explicitly non-silently flags when any sampled tick's RuntimeMode != NORMAL, independent of whether avg_tick_compute_ms stayed within threshold
- [ ] A new unit test forces the Governor out of NORMAL mid-sample and asserts the gate surfaces the excursion rather than silently blending it in

## Related Tickets
- TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC

## Related Docs
- docs/engine/performance_contract.md
- docs/engine/contracts/certification_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/perf/bench_harness.py
- src/perf/long_run_harness.py
- src/core/governance.py
- src/engine/runtime_status.py
- src/engine/kernel.py
- src/certification/conformance.py
- src/certification/models.py
- tests/perf/test_perf_regression_baseline.py
- tests/perf/test_bench_harness.py
- tests/perf/conftest.py

## Assumptions / Open Questions
- PressureSignals is frozen/slots — a narrower per-tick sampling fix inside BenchHarness (not touching PressureSignals) is the intended implementation route pending Plan-phase confirmation; if Plan disagrees and requires a PressureSignals schema change, this may need Architecture Review
- Whether to reuse certification's ConformanceEvaluator logic or write an independent simpler NORMAL-only assertion is an open Plan-phase decision
- Need to confirm the 26 scenario builders (10 warmup/50 sample ticks) don't already legitimately dip out of NORMAL under real load before enabling the gate as blocking, to avoid false positives

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
