---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE
date: 2026-10-16
tags: [performance, benchmarking]
---

# Investigation: TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE

Read-only; no run. Sources: `src/perf/bench_harness.py` (run_benchmark, `_build_record`), `src/perf/benchmark_record.py`, `docs/performance/benchmark_identity_schema.md`, `docs/performance/tick_cost_growth.md` section 5.

## What the code does today
- `run_benchmark`: warm-up, then `gc.collect()`, `gc.disable()`, then the sampled ticks; RSS is read every 10th tick (`i % 10 == 0`); the `finally` re-enables the collector, **after** the last tick and **before** `wall_end_ts` / `cpu_end`. Nothing collects after the window, so the last read is at garbage-high-water.
- `mem_rss_mb.{avg,max,delta}` comes from those samples; `peak_rss_mb` = max, `memory_delta_mb` = delta. The record's `memory_mb` is `{rss_high_water, rss_delta, sample_every_ticks}` (`Dict[str, float]` in the typed model, so extra keys need no model change; `_build_record` is the only writer; `tests/unit/perf/test_long_run_record.py:62` reads the old keys).
- Consumers of the old keys: the corpus baseline check (`mem_rss_mb` exists), the regression gate on `peak_rss_mb`. They must see unchanged values.
- Declared memory is `RuntimeProfile.max_ram_mb` (`src/config/profiles.py:31`); `identity.runtime.ram_mb` is the **host's** RAM, not the declared one, so the ratio needs the profile's number (the harness holds `self._profile`).

## Schema rule
Section 4 of the schema doc: a MINOR bump is "additive; absent optional fields are unknown" and is recorded, not blocking. The new keys are optional additions to `memory_mb` (its JSON schema lists `required` but sets no `additionalProperties: false`), so the bump is **1.1 -> 1.2** and `SCHEMA_VERSION` in `benchmark_record.py` follows. Needs the owner's approval for the doc edit (P1).

## Design questions and answers
1. **Where to read.** The collector stays disabled for the whole latency window (protocol unchanged). Read the collected baseline right after the existing `gc.collect()` (before `gc.disable()`), and read the collected end value **after `wall_end_ts` and `cpu_end` are taken**, so neither collect nor the extra RSS reads are inside any timed span. The end reading re-enables the collector (already done by the `finally`), calls `gc.collect()` and reads RSS once. This is cheaper and clearer than a separate gc-on pass; it also gives the number of unreachable objects the collect found, a direct garbage-per-window figure.
2. **Freed-but-retained arenas.** After a collect, CPython/glibc often keeps freed arenas, so RSS may not fall back to the working set; the after-collect RSS is an upper bound on the engine's working set, not the exact figure. Mitigation without a tracemalloc cost inside the window: also record `sys.getallocatedblocks()` before the window (after the first collect) and after the end collect, a malloc-independent growth count of live Python blocks. `tracemalloc` is not used in the harness (it changes the timing of every allocation); the #597 investigation used it offline.
3. **Q1 (end reading vs periodic).** The end reading is enough: #597 measured growth as linear per tick (+1.42 MB/tick gc-off, +0.14 MB/tick gc-on), so one collected-to-collected delta over the window carries the slope.
4. **Declared-memory note, report-only (OD-8).** `rss_over_declared = rss_after_collect_mb / profile.max_ram_mb`; recorded as a number plus a boolean-like `over_declared` (1.0 or 0.0) in `memory_mb`, or a note string in the record's report. It must never raise, gate, or change the outcome: it is computed inside the existing "record is additive" path whose failure is already logged and swallowed.

## Expected values (to check with one local run later, not promoted)
`simq_corpus_frontier_extended`: engine working set about 110-130 MB per #597; after-collect RSS should be of the order of 100-200 MB (AC1), against 1703 MB in the old fields.

## Risks
- The end `gc.collect()` on a 1000+-tick corpus world with about 1.4 GB of garbage may take seconds and spike RSS briefly; it is after the timed window, but it is wall time added to the run (the corpus record is about 70 s today). Report the collect duration in the record.
- Memory at the end collect can exceed the profile cap under `systemd-run MemoryMax` only if the garbage itself is near the cap; the old run already reached 1.7 GB, so the 3 GB rule from lead applies to the AC1 run.

## Diagnostics after the first evidence run (2026-10-16): the after-collect RSS was not the working set
First run, `simq_corpus_frontier_extended`, 1 process, 100 + 1000 ticks: `rss_after_collect_mb` 1701.8 against `rss_before_window_mb` 100.1, `gc_unreachable_objects` 1355, `allocated_blocks_delta` +211,398 (AC1 expected 100-200 MB; not met as written). Script `rss_diagnose.py` in this folder; 200 ticks after 100 warm-up on the same world, one process at a time under `MemoryMax=3G`, loadavg1 1.1 to 2.3 (diagnostics, not measurements):

| run | warm-up MB | end of window MB | growth | after end collect | modes |
|---|---|---|---|---|---|
| gc off, canonical (census) | 102 | 402 | +285 | 402 | NORMAL 40, CONSTRAINED 44, DEGRADED 14, SURVIVAL 102 |
| gc off, pinned | 97 | 404 | +292 | 404 | NORMAL 200 |
| gc on, canonical | 102 | 113 | +9 | 109 | as above |
| gc on, pinned | 100 | 113 | +11.5 | 108 | NORMAL 200 |
| no BenchHarness, gc on, canonical | 104 | 109 | +3 | 109 | as above |
| tracemalloc, gc off, canonical | 98 | 442 | +332 | 442 | as above |
| gc off, canonical, then `malloc_trim(0)` | 100 | 402 | | 402, **125.6 after trim** | |

- **Named cause:** the disabled collector lets cyclic garbage pile up (about 1.4 MB per tick); freeing it does not return the memory to the OS. Mode and the harness's history list are ruled out (pinned and canonical match; no-harness with the collector on is flat). `tracemalloc`: Python peak 324.6 MB during the window, 11.1 MB at its end; RSS minus traced 431 MB. Census (`gc.get_objects()`): 121k tracked objects at the end against 103k at warm-up, about 6 MB shallow growth (sets 3.2, dicts 1.8): no large holder.
- **The unreachable-count puzzle** (a full collect found only 1230-1355 objects although about 325 MB was freed): explanation proposed by perf-planner and built into the harness, checked by the new `gc_collected_objects` (the `gc.get_stats()` collected total over the window and the end collect): `gc.disable()` leaves new objects in generation 0, and the `finally`'s `gc.enable()` comes before the clocks stop, so the first allocation after it triggers an automatic generation-0 collection that takes all of it; the explicit collect finds the leftovers. The 1000-tick run with the new keys is the test of it.
- **Consequence for the design:** the first design (an after-collect reading) could not describe engine memory; the harness now trims straight after the end collect (outside the timed spans, never before the window, so the sampled ticks fault no pages they do not fault today) and `rss_over_declared` uses the after-trim reading, with `rss_over_declared_basis_trim` saying which basis was used.
