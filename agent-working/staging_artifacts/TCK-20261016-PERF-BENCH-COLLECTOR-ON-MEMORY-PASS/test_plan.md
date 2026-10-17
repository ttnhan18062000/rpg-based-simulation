---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261016-PERF-BENCH-COLLECTOR-ON-MEMORY-PASS
date: 2026-10-18
tags: [performance, benchmarking]
---

# Test plan: TCK-20261016-PERF-BENCH-COLLECTOR-ON-MEMORY-PASS

Files: `tests/unit/perf/test_bench_harness_memory.py` (extend), `test_benchmark_record.py`, `test_rerun_baselines.py`. Fake Kernel monkeypatched in `src.perf.bench_harness`; no engine tick, no heavy run.

| Case | Test | Expect |
|---|---|---|
| collector on | fake tick asserts `gc.isenabled()` inside `run_memory_pass`; a caller that had it off gets it back off | on during the pass, restored after |
| outside timed spans | `run_memory_pass` calls no clock (monkeypatched `perf_counter` raises); `run_benchmark` unchanged (existing ordering tests) | passes |
| cyclic garbage | fake tick makes N reference cycles per tick | `working_set_delta_mb` small, old `rss_delta` of the timed pass large (same fake) |
| timed fields identical | `with_working_set(record, reading, 512)` vs record | only `schema_version` and `memory_mb` differ (compare `to_dict()` minus those) |
| ratio basis | with the pass: `rss_over_declared` = working_set/declared, `rss_over_declared_basis_working_set` 1.0, old ratio kept; report-only: `compare`/`promote` outcome identical with and without the keys | as stated |
| absent pass | record without the pass | valid, no `working_set_*` key, `rss_over_declared` as today |
| trim unavailable | reading with `rss_after_trim_mb=None` | basis falls back to collect, `working_set_basis_trim` 0.0 |
| old records | 1.0, 1.1, 1.2 records load | pass |
| CLI | `measure --memory-pass` with a fake child: merged record written, `.timed.json` kept; child exit 1 -> record still written without keys, rc 0; `record --memory-pass` passes the flag; default off | as stated |
| mutation proof | break the collector-enable (leave it disabled) and the basis switch in a scratch copy | the matching test fails for that reason |
