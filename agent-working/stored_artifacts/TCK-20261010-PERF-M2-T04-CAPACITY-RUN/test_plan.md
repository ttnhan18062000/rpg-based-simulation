---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261010-PERF-M2-T04-CAPACITY-RUN
date: 2026-10-10
tags: [performance, benchmarking, documentation]
---

# Test plan: TCK-20261010-PERF-M2-T04-CAPACITY-RUN

`tests/unit/perf/test_capacity_run.py` (15), `test_long_run_record.py` (8), additions to `test_bench_harness_record.py`, `test_benchmark_record.py` and a `conftest.py` that keeps samples files in a
temporary directory; `tests/perf/conftest.py` does the same and `test_perf_stress.py` passes `samples_dir`. Tiny scenarios only; the real subprocess tests use 15 entities, 10 ticks.

## Proof Plan

| Criterion | Level | Proof kind | Oracle source | Expected effect | Selected commands |
|---|---|---|---|---|---|
| N records, capacity_run, 100/1000 protocol, runner.controlled=false | unit + real subprocess | behaviour | the T04 acceptance criteria | one schema-1.1 record per repetition; defaults are 100 and 1000 | `pytest tests/unit/perf/test_capacity_run.py` |
| Unique samples files, matching sha256, none under `reports/perf/samples/` | unit | behaviour | the T04 follow-up from the #483 review | distinct files in one second; each digest matches its own file; the perf tests redirect | same, `test_long_run_record.py` |
| Exact nearest-rank p50/p95/p99/max | unit | behaviour | worked by hand (1..20: 10, 19, 20, 20) | exact values, `percentile_method` nearest_rank, `rss_high_water` present | same |
| Variance, dirty tree, excursion, one repetition | unit | behaviour | the T04 acceptance criteria | INCONCLUSIVE naming variance or the cause, never PASS | same |
| Paired mode: fresh process per side, compare() | unit | behaviour | OD-2/T04 | each side under its own root; a side that cannot emit records is INCONCLUSIVE | same |
| `passed_certification` gone, `outcome` present | unit | behaviour | the T04 acceptance criteria | report has `outcome`, keeps warmup, samples, per-sample `active_mode` | `pytest tests/unit/perf/test_long_run_record.py` |
| Stats cover every sampled tick (DEV-021) | unit | regression | the 100-slot deque | 150 ticks give 150 samples (fails on the old harness: 100) | `pytest tests/unit/perf/test_bench_harness_record.py` |
| No pyperf, no claim | static + CLI output | check | OD-5, OD-7 | no pyperf import; the output states `CLAIM: none` | same |
| Nothing else regressed | gates | regression | the repo's own gates | all pass | `python3 -m codebase.health check`; `pytest tests/tools/test_perf_inventories_committed_in_sync.py tests/tools/test_agent_working_paths_guard.py` |

Not proven: the two `extra_slow` certification tests were not run.
