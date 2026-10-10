---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261010-PERF-M2-T04-CAPACITY-RUN
phase: done
date: 2026-10-10
tags: [performance, benchmarking, certification]
---

# TCK-20261010-PERF-M2-T04-CAPACITY-RUN

## Title
PERF-M2-T04: Capacity projection with a capacity_run tool

## Status
DONE

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
- Harden the samples pointer that #483 added: BenchHarness._build_record names the file f"{scenario}_{profile}_{int(timestamp)}", so two runs in the same second overwrite each other and the earlier record's sha256 goes stale. Make the stem unique (sub-second or a run id). Any tripwire run over MAX_EMBEDDED_SAMPLES (500) also writes to the cwd-relative reports/perf/samples/ by default. tests/perf/test_perf_stress.py (1000 ticks) does this, so pass samples_dir=tmp_path there (perf-planner review of #483)
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
- [x] Running tools/perf/capacity_run.py on a scenario with --repetitions N emits N schema-1.0 BenchmarkRecords (or one aggregated record), each with gate.tier=capacity_run, gate.projection=capacity_run, protocol warmup=100, sampled=1000, and runner.controlled=false
- [x] Two records written in the same second for the same scenario and profile point to different files, and each sha256 matches its own file. No test under tests/ writes into reports/perf/samples/.
- [x] samples.tick_wall_ms is a {uri, sha256} pointer, and the sha256 matches the written file under reports/perf/
- [x] A unit test with a fixed sample list asserts the exact nearest-rank p50/p95/p99/max values, protocol.percentile_method == 'nearest_rank', and the presence of memory_mb.rss_high_water
- [x] When the coefficient of variation across repetitions exceeds the declared limit, the outcome is INCONCLUSIVE with a reason naming variance
- [x] A run with engine.dirty_src=true is rejected or INCONCLUSIVE, never PASS
- [x] LongRunStabilityReport no longer exposes passed_certification. Its record mapping has outcome in {PASS, REGRESSION, INCONCLUSIVE, NOT_APPLICABLE} and keeps warmup_ticks, the samples and the per-sample active_mode. tests/certification/test_cert_long_run_stability.py asserts outcome.
- [x] Paired mode (--base/--head) runs each side in a fresh process and returns compare(base, head) outcomes
- [x] No pyperf import exists in the tool or harness, and the tool's output and docs contain no capacity claim
- [x] Tests use a tiny scenario or a mocked tick loop and are not in the default CI selection

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
- agent-working/stored_artifacts/TCK-20261010-PERF-M2-T04-CAPACITY-RUN/ (plan.md, investigation.md, test_plan.md)

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
- Decisions are in `agent-working/stored_artifacts/TCK-20261010-PERF-M2-T04-CAPACITY-RUN/plan.md`. Reviewer-relevant: an unpaired run is never PASS (`INCONCLUSIVE` or `NOT_APPLICABLE`, exit 0 meaning it ran and reported); variance is the CV of avg latency across repetitions (limit 0.10); `identity.runner` is a new optional section so the schema is **1.1**; paired mode takes two checkouts and runs each side in fresh processes under its own `src/`; the long-run record is `gate.tier = comparative` (perf-planner's ruling on #493, matching `performance_contract.md` §3.3; the ticket text said `capacity_run`) with projection `long_run_stability`, so it is never compared with a `BenchHarness` capacity run.
- **Found and fixed in this ticket: `BenchHarness` statistics covered only the last 100 sampled ticks** (`RuntimeStatus.signal_history` is a 100-slot deque) and `compute_tps` was overstated by `sample_ticks / 100`. DEV-021 (Bug Fix). It changes reported numbers for any run over 100 ticks; the three 1000-tick `simq_corpus_*` baselines get a second reason to be re-recorded (invalidation ledger row). `runtime_status.py` was not touched.
- **`docs/engine/performance_contract.md` §3.3 is not edited here:** it is rpg-owned P1 (route: rpg-planner). The proposed text is in the PR body for the owner.
- Samples files: unique name plus exclusive create; `PERF_SAMPLES_DIR` redirects them; both perf test directories set it, and `test_perf_stress.py` passes `samples_dir`.
- A real run at the default protocol (20 entities, 3 repetitions, 2m10s, clean tree) gave CV 0.020 and 1000 compute samples per repetition; numbers in `investigation.md`, provisional, no claim.
- Not verified: the two `extra_slow` certification tests were edited to assert `outcome` but not run (5000 ticks on 1000 entities); 100 entities at the default protocol did not finish in 15 minutes on this VM.

## Test Summary
- New: `tests/unit/perf/test_capacity_run.py` (15; the 4 that start subprocesses are marked `slow`, so they are outside the default CI selection: 11 in the default set, 4 under `-m slow`), `test_long_run_record.py` (8), additions to `test_bench_harness_record.py` and `test_benchmark_record.py`, `tests/unit/perf/conftest.py`. `tests/unit/perf` + `tests/perf/test_bench_harness.py` + `tests/perf/test_profiler_integrity.py`: 175 passed.
- The DEV-021 regression test fails on the previous harness (100 samples against 150).
- `python3 -m codebase.health check`: 0 new, 0 worse. mypy on `src/`: no new errors (3 existing baseline rows in `long_run_harness.py`). Parity gate OK, wall-clock inventory regenerated and in sync, `tests/tools/test_agent_working_paths_guard.py` passes.
- Not run: the full suite; the two `extra_slow` certification tests.

## Files Changed
- Code: `src/perf/benchmark_record.py`, `src/perf/bench_harness.py`, `src/perf/long_run_harness.py`, `tools/perf/capacity_run.py` (new).
- Tests: `tests/unit/perf/test_capacity_run.py`, `test_long_run_record.py`, `conftest.py` (new); `test_bench_harness_record.py`, `test_benchmark_record.py`, `test_baseline_lifecycle.py`; `tests/perf/conftest.py`, `tests/perf/test_perf_stress.py`; `tests/certification/test_cert_long_run_stability.py`.
- Docs: `docs/performance/benchmark_identity_schema.md`, `docs/performance/baseline_invalidation_ledger.md`, `docs/performance/wall_clock_inventory.{json,md}`, `docs/guidelines/intentional_divergences.md` (DEV-021), `docs/parity_ledger/infrastructure.yaml` (INFRA-432), `docs/REGISTRY.yaml`.
- Tickets and artifacts: this ticket, `agent-working/stored_artifacts/TCK-20261010-PERF-M2-T04-CAPACITY-RUN/`.

## Completion Summary
`tools/perf/capacity_run.py` runs N fresh-process repetitions of `BenchHarness` (100 warmup, 1000 sampled ticks) and emits a schema-1.1 record per repetition with `gate.tier = capacity_run`, `runner.controlled = false` and a pointed-to samples file; variance above the declared limit, a dirty tree, an excursion, a crash or a single repetition is `INCONCLUSIVE`, otherwise `NOT_APPLICABLE`, never PASS, and it states no capacity claim. Paired mode compares the median repetition of each side. `LongRunStabilityReport` has `outcome` in place of `passed_certification`, nearest-rank percentiles, and maps into a record. Samples files are unique and created exclusively. A real run exposed that `BenchHarness` statistics covered only the last 100 ticks; fixed and recorded as DEV-021. Left open: the §3.3 text for `performance_contract.md` (rpg-owned, a proposal in the PR), the two `extra_slow` certification tests not run, and no controlled runner (OD-5), so nothing here is a capacity claim.
