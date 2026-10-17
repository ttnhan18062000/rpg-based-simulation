---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261016-PERF-BENCH-COLLECTOR-ON-MEMORY-PASS
date: 2026-10-18
tags: [performance, benchmarking]
---

# Plan: TCK-20261016-PERF-BENCH-COLLECTOR-ON-MEMORY-PASS

Approved by perf-planner with four changes, all applied below (2026-10-18): (1) `SCHEMA_VERSION` is 1.3 for every new record and `with_working_set` changes `result.memory_mb` only; (2) in-run AC2 evidence; (3) `record --memory-pass` runs the pass once, after the last timed run, merged into the candidate (not per attempt); (4) the child echoes scenario id, seed, profile and tick counts and the parent refuses a mismatching merge.

## Changes
1. `src/perf/bench_harness.py`: `run_memory_pass(profile, initial_state, scenario_id, warmup_ticks, sample_ticks) -> MemoryPassReading` (M1 default flags, as `run_benchmark`; the reading type lives in `benchmark_record.py` to avoid an import cycle). Same Kernel construction and flags as `run_benchmark`; warm-up, `gc.collect()`, read; the sampled ticks run with the collector **enabled** (enabled for the call if the caller had it off, restored after); no clock, no per-tick sampling; end `gc.collect()` + `_malloc_trim()`, read. Kernel shut down in a `finally`. `run_benchmark` is untouched.
2. `src/perf/benchmark_record.py`: `SCHEMA_VERSION` 1.2 -> 1.3 (every new record is stamped 1.3, as 1.2 did for its keys); `MemoryPassReading` (it echoes `scenario_id`, `seed`, `profile_name`, `warmup_ticks`, `sample_ticks`); `working_set_mismatch(record, reading)`; `with_working_set(record, reading, declared_ram_mb)` refuses a mismatch and returns a new record whose only change is `result.memory_mb`. New keys: `working_set_mb` (after trim, or after collect where the trim is unavailable), `working_set_delta_mb` (that minus the pass's pre-window RSS), `working_set_basis_trim` (1.0 trim, 0.0 collect), `working_set_allocated_blocks_delta`, `working_set_gc_collected_objects`, `working_set_measured_ticks`. `rss_over_declared` becomes `working_set_mb / declared_ram_mb`, `rss_over_declared_basis_working_set` = 1.0, and the old ratio is kept as `rss_over_declared_timed_pass`. Absent pass: nothing changes (no keys). Report-only (OD-8): no gate or `promote` reads any of them.
3. `tools/perf/rerun_baselines.py`: `measure --memory-pass` and `record --memory-pass`. `cmd_measure` writes `<out>` (timed, as today) then, when asked, spawns a child `memory-pass --name N --out F` (fresh process, rebuilds state through `measure_record`'s own builders), reads its reading JSON, writes the merged record to `<out>` and the unmerged one to `<out stem>.timed.json`. A child failure never fails the measurement: the record stays without the keys and stderr says why. `record --memory-pass` runs the pass **once**, after the last timed run, and merges it into `candidate.json` only (the pass is untimed, so a pass per attempt would triple the cost for nothing); quiet-window, spread and median logic are unchanged. Precedence (one place, the schema doc): when `rss_over_declared_basis_working_set` is 1.0, `rss_over_declared = working_set_mb / declared_ram_mb` and `working_set_basis_trim` says trim or collect; when the pass is absent the 1.2 meaning applies unchanged and `rss_over_declared_basis_trim` describes the timed pass. The parent does `gc.collect()` + trim before spawning the child and the evidence reports peak scope memory.
4. Docs (P1, owner approves in the PR): `benchmark_identity_schema.md` (version line, `memory_mb` rows, JSON schema properties, §4 MINOR note); ledger: the two corpus rows get the working-set figure after the run; `tick_cost_growth.md` §5 pointer; `perf_baseline_policy.md` only if it names the memory fields.

## Not changed
Latency protocol, tripwire RunSpecs, `NOISE_BUDGET`, compare thresholds, `src/` outside `src/perf/`, nightly, the `bench_corpus_world.py` printer.

## Evidence run (needs perf-planner/lead go)
One local `measure --name simq_corpus_frontier_extended --memory-pass` under `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`, quiet window, foreground. AC1: `working_set_mb` within 95.6 to 116.8 MB and `working_set_delta_mb` < 25 (bound stated in investigation.md before the run). AC2: merged record's timed fields equal `<run>.timed.json`. No baseline is promoted.

## Commits
(1) tickets + staging (this plan); (2) code + tests; (3) docs + ledger rows (after the run). Tell perf-planner before each; the schema doc edit is approved by the owner in the PR.
