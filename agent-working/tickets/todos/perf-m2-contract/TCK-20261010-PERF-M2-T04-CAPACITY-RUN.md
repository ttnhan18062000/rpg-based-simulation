---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261010-PERF-M2-T04-CAPACITY-RUN
phase: open
date: 2026-10-10
tags: [performance, benchmarking, certification]
---

# TCK-20261010-PERF-M2-T04-CAPACITY-RUN

## Title
PERF-M2-T04: Capacity projection with a capacity_run tool

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add tools/perf/capacity_run.py: 100 warmup and 1000 sampled ticks, N process repetitions, an optional paired mode, p50/p95/p99/max, variance (above the limit means INCONCLUSIVE), RSS high-water, and records with gate.projection = capacity_run. Map the long-run report (schema F22) into the record via src/perf/long_run_harness.py, and replace passed_certification with outcome. OD-5: it runs on one named host labelled runner.controlled = false, and makes no capacity claim. OD-7: no pyperf. Depends on T02b and T05. A capacity run is the only clause kind that may later support a 'sustains X on class Y' claim, and today it does not exist.

Source concern IDs: C5.

## Scope
- Add tools/perf/capacity_run.py using BenchHarness with process-level repetitions (no pyperf): 100 warmup and 1000 sampled ticks, --repetitions N, and optional --base/--head paired mode with a fresh process per side through compare()
- Emit schema-1.0 BenchmarkRecords with gate.tier=capacity_run, gate.projection=capacity_run, runner.controlled=false, nearest-rank p50/p95/p99/max, memory_mb{rss_high_water, rss_delta, sample_every_ticks}, validity fields, and samples.tick_wall_ms as a {uri, sha256} pointer to an uncommitted file under reports/perf/
- Declare a variance limit (coefficient of variation across repetitions). Exceeding it gives INCONCLUSIVE naming variance, and dirty_src=true is rejected or INCONCLUSIVE.
- Migrate src/perf/long_run_harness.py to nearest-rank percentiles and map the F22 report into a capacity_run record (scenario_id, entity_count, seed, final_state_hash, memory, warmup_ticks, samples, per-sample active_mode). Replace passed_certification with outcome.
- Update tests/certification/test_cert_long_run_stability.py to assert outcome instead of passed_certification
- Update docs/engine/performance_contract.md §3.3, the benchmark_identity_schema gate.projection cell, and the parity ledger (infrastructure.yaml) in the same session

## Out of Scope
- Any capacity claim or enforcement of §5.1 targets until the owner names an approved runner (OD-5)
- Adding pyperf (OD-7)
- Making any check blocking (OD-8)
- Running the capacity tool in default CI
- Tripwire projection (PERF-M2-T03)

## Acceptance Criteria
- [ ] Running tools/perf/capacity_run.py on a scenario with --repetitions N emits N schema-1.0 BenchmarkRecords (or one aggregated record), each with gate.tier=capacity_run, gate.projection=capacity_run, protocol warmup=100, sampled=1000, and runner.controlled=false
- [ ] samples.tick_wall_ms is a {uri, sha256} pointer, and the sha256 matches the written file under reports/perf/
- [ ] A unit test with a fixed sample list asserts the exact nearest-rank p50/p95/p99/max values, protocol.percentile_method == 'nearest_rank', and the presence of memory_mb.rss_high_water
- [ ] When the coefficient of variation across repetitions exceeds the declared limit, the outcome is INCONCLUSIVE with a reason naming variance
- [ ] A run with engine.dirty_src=true is rejected or INCONCLUSIVE, never PASS
- [ ] LongRunStabilityReport no longer exposes passed_certification. Its record mapping has outcome in {PASS, REGRESSION, INCONCLUSIVE, NOT_APPLICABLE} and keeps warmup_ticks, the samples and the per-sample active_mode. tests/certification/test_cert_long_run_stability.py asserts outcome.
- [ ] Paired mode (--base/--head) runs each side in a fresh process and returns compare(base, head) outcomes
- [ ] No pyperf import exists in the tool or harness, and the tool's output and docs contain no capacity claim
- [ ] Tests use a tiny scenario or a mocked tick loop and are not in the default CI selection

## Related Tickets
- TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA
- TCK-20261003-PERF-M2-CLAUSE-INVENTORY
- TCK-20261004-PERF-OPTIMIZATION-PROOF-HONEST-CLAIMS
- TCK-20260518-LONG-RUN-STABILITY
- TCK-20261004-PERF-M1-DEBT-HARNESS-CORRECTNESS
- TCK-20261009-PERF-GATE-PASSES-VACUOUSLY-AGAINST-PRE-M1-BASELINE

## Related Docs
- docs/engine/performance_contract.md
- docs/performance/benchmark_identity_schema.md
- docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md
- docs/performance/perf_baseline_policy.md
- docs/parity_ledger/infrastructure.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/perf/long_run_harness.py
- src/perf/bench_harness.py
- src/perf/profiles.py
- src/certification/hardware.py
- tools/perf/run_benchmarks.py
- tools/perf/_profiling_common.py
- docs/performance/benchmark_identity_schema.md
- docs/engine/performance_contract.md
- docs/performance/perf_baseline_policy.md

## Assumptions / Open Questions
- Lift boundary (roadmap RPG-core gate item 8, owner 2026-10-09): `src/` edits are limited to `src/perf/bench_harness.py`, `src/perf/profiles.py`, `src/perf/long_run_harness.py`, new `src/perf/benchmark_record.py`, `src/observability/reporting/baseline_comparator.py` and `sweep_report.py`. Any other `src/` path listed under Related Code Areas is read-only here; editing it needs a new owner lift.
- Blocked until PERF-M2-T02b (BenchmarkRecord, compare(), identity collector, nearest-rank) and PERF-M2-T05 (baseline_lifecycle.py) land
- Editing src/perf/long_run_harness.py needs the OD-8 owner lift, and measurements stay provisional
- The variance limit value is not set anywhere. The ticket or the owner must declare it. Dev hosts are VMs, so INCONCLUSIVE is likely, and OD-7 says to revisit pyperf only if the variance check fails.
- Within-run trend checks (rss_bounded, latency_stable) are comparative per contract §3.3. Their mapping to outcome must not become a capacity claim.
- Readers of reports/certification/long_run_*.json that rely on passed_certification must be updated

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
