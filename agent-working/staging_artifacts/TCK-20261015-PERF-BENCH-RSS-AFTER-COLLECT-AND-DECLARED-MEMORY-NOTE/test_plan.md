---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE
date: 2026-10-16
tags: [performance, benchmarking]
---

# Test plan: TCK-20261015-PERF-BENCH-RSS-AFTER-COLLECT-AND-DECLARED-MEMORY-NOTE

Scope: `tests/unit/perf/test_bench_harness_memory.py` (new) plus edits to `test_benchmark_record.py` / `test_bench_harness_record.py`; `tests/tools` perf and guard files. No heavy run. The harness is driven with a **fake Kernel** (monkeypatched in `src.perf.bench_harness`) so no engine tick runs.

| Test | What it proves | AC |
|---|---|---|
| garbage-making fake tick (reference cycles holding `mmap` pages, returned to the OS on free) | old `rss_delta` / `rss_high_water` large; `rss_collected_delta_mb` small; `gc_unreachable_objects` >= the cycles made; `allocated_blocks_delta` small | AC1 |
| old fields byte-for-byte: a fixed fake run's `mem_rss_mb`, `peak_rss_mb`, `memory_delta_mb` equal the values computed from the same sampled RSS; the result dict's key set is exactly `LEGACY_KEYS` | the new reading is carried outside the legacy dict | AC2 |
| docs text: the schema doc and `_build_record` docstring say the old fields include uncollected garbage (string pin) | documented | AC2 |
| `rss_over_declared == rss_after_collect_mb / profile.max_ram_mb` exactly, for two profiles; `declared_ram_mb == profile.max_ram_mb`; a separate, named peak ratio key if added | the formula | AC3 |
| report-only: a record with `rss_over_declared` 3.0 vs the same record without the keys gives identical `compare` outcome and identical `baseline_lifecycle.promote` decision; a ratio above 1.0 raises nothing in `run_benchmark` | never a gate | AC3 |
| ordering, event log: `cpu_times` (end) is recorded, then `gc.collect` (end), and the collector's `isenabled()` after `run_benchmark` equals its value before, for both an initially-enabled and an initially-disabled collector; no extra `gc.enable()/disable()` call besides the existing ones | the end collect is outside both timed spans and leaves gc state as found | AC5 |
| during the sampled loop `gc.isenabled()` is False (asserted inside the fake tick); `protocol.gc_disabled` still True; `measured_ticks`/`warmup_ticks` unchanged | latency protocol unchanged | AC5 |
| the record is additive: `_build_record` failing on the new keys is swallowed (monkeypatch a failing reader), result dict still returned | never fails a run | AC3 |
| cross-version compare: a 1.2 candidate vs a 1.1 baseline and the reverse give the same outcome as 1.1 vs 1.1 (no INCONCLUSIVE, no warning); MAJOR 2.0 still INCONCLUSIVE; a 1.1 record (no new keys) loads via `from_dict` and re-serialises without gaining keys | MINOR bump is non-blocking; tripwire accepts it (`tripwire` compares through `compare`) | AC2, AC5 |
| tripwire pin: `TRIPWIRE_SCENARIOS` unchanged (already pinned) | nothing in the nightly lane changes | AC5 |
| resource rule: the evidence run is one process under `MemoryMax=3G`, lead told before (process, not a test) | | AC6 |
| AC4 (owner approves the schema edit; ledger lines updated) | not a test: the schema-doc commit body says "pending owner approval"; the ledger line is checked by `tests/tools` docs/frontmatter checks and read in review | AC4 |
