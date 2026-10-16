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
