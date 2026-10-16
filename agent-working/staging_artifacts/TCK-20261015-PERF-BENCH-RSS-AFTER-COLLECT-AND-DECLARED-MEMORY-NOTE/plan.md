---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE
date: 2026-10-16
tags: [performance, benchmarking]
---

# Plan: TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE

Not implemented. Sent to perf-planner for review; the branch (same as the T08-NOISY batch, or a fresh one from origin/main if perf-planner prefers separate PRs) is theirs to say.

## Changes (all in `src/perf/`, plus docs and tests)
1. `bench_harness.py::run_benchmark`: after the existing `gc.collect()` read `rss_before_window_mb` and `sys.getallocatedblocks()`; the sampled loop and `gc.disable()` are untouched. After `wall_end_ts` and `cpu_end` are taken (outside both timed spans): `gc.enable()` if it was enabled, `t = perf_counter(); unreachable = gc.collect(); collect_s = ...`, then read `rss_after_collect_mb` and `allocated_blocks_after`. Put them in the result dict under `mem_after_collect`.
2. The old `mem_rss_mb`, `peak_rss_mb`, `memory_delta_mb` stay byte-for-byte; their docstring/doc text now says they include garbage the collector was told not to collect.
3. `_build_record`: `memory_mb` gains the optional keys `rss_before_window_mb`, `rss_after_collect_mb`, `rss_collected_delta_mb`, `allocated_blocks_delta`, `gc_unreachable_objects`, `gc_collect_s`, `declared_ram_mb`, `rss_over_declared`. All inside the existing never-fails-the-benchmark `try`.
4. `benchmark_record.SCHEMA_VERSION` 1.1 -> 1.2; `benchmark_identity_schema.md` (the `memory_mb` row and JSON schema, section 4 note) edited **only after the owner approves** (P1).
5. Report-only note: when `rss_over_declared > 1.0` the report (`tools/perf` summary / record `notes`, whichever the record already prints) says so; no exit code, gate or promotion reads it. `baseline_lifecycle.promote` is not touched.
6. Ledger: the two corpus lines (`simq_corpus_frontier_extended` 1703 MB, `simq_corpus_frontier_marches` 1568 MB) say the RSS was harness garbage, not engine memory; point at `tick_cost_growth.md` section 5 and the new fields.

## Tests (no heavy run)
- Fake kernel (monkeypatch `Kernel` in the harness module) whose tick builds N reference cycles: old `rss_delta` large, `rss_collected_delta_mb` small, `gc_unreachable_objects` > 0, `allocated_blocks_delta` small.
- Protocol unchanged: during the sampled loop `gc.isenabled()` is False (fake tick asserts it), and True again after `run_benchmark`; `protocol.gc_disabled` untouched; the timed spans exclude the end collect (fake clock or ordering test: `wall_end_ts` is taken before the collect).
- Old fields unchanged in value for a fixed fake run.
- Report-only: a record with `rss_over_declared` 3.0 leaves `compare`/`promote` outcomes and exit codes identical to one without the keys.
- Older 1.0/1.1 records still load (absent keys are unknown).

## Evidence run (after the gate opens; one run, not a promotion)
`simq_corpus_frontier_extended` on `PERF_512MB_LOCAL`, one process, `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`, lead told first (the old process peaked at 1.7 GB, close to the 3 GB line), quiet-window check recorded. Expect `rss_after_collect_mb` about 100-200 MB.

## Close
Scoped tests (`tests/unit/perf`, `tests/tools` perf/guard files), ruff/mypy gates as before, paths guard, `make knowledge-index-update`, tell perf-planner before commits, owner approves the schema edit and the push.
