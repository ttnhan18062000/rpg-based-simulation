---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261016-PERF-BENCH-COLLECTOR-ON-MEMORY-PASS
date: 2026-10-18
tags: [performance, benchmarking]
---

# Investigation: TCK-20261016-PERF-BENCH-COLLECTOR-ON-MEMORY-PASS

Read-only. Sources: `src/perf/bench_harness.py` (`run_benchmark`, `_collect_and_read`, `_memory_mb`), `src/perf/benchmark_record.py` (`SCHEMA_VERSION` 1.2, `Result.memory_mb: Dict[str, float]`), `tools/perf/rerun_baselines.py` (`measure_record`, `cmd_measure`, `cmd_record`), `docs/performance/benchmark_identity_schema.md` rows for `memory_mb`, `docs/performance/tick_cost_growth.md` §5, and the collector-on diagnostics kept in `reports/perf/rss_evidence/`.

## What the harness does today
- Timed pass: warm-up, `gc.collect()`, pre-window RSS and blocks, `gc.disable()`, sampled loop, `gc.enable()` in a `finally`, clocks stop, then (outside both timed spans) `gc.collect()` + `malloc_trim(0)` + RSS read. The disabled collector's freed garbage leaves fragmented arenas that the trim cannot fully release: 311 MB after trim on `simq_corpus_frontier_extended` (1000 ticks), against about 106 MB engine working set.
- `memory_mb` is `Dict[str, float]` with free optional keys; every value is a number (basis flags are 1.0 / 0.0, as `rss_over_declared_basis_trim` already is). `compare` reads only the MAJOR schema version, so a MINOR bump is safe.
- `rerun_baselines.py measure` runs one timed record per fresh process (`subprocess.run` of itself); `record` calls it 3 or 5 times. That is the corpus measuring path (`CORPUS_WORLDS`). `bench_corpus_world.py` only prints the harness dict (CORPUS removed its writer); no flag is added there.

## Collector-on evidence (the AC1 target)
- 1100-tick diagnostic (`rss_diagnose.py`, collector ON): 100.6 MB after warm-up, 131.9 MB at window end, **106.2 MB after collect + trim**; `allocated_blocks_delta` +211,691 (the same as collector off).
- 200-tick diagnostics, collector ON, `frontier_extended`: after end collect 109.4 (canonical), 107.9 (pinned), 108.5 (no harness); after warm-up 99.9 to 103.9; window growth +3.1 to +11.5 MB.
- So collector-on readings of the same world span about 99.9 to 109.4 across ticks, contract and harness use.

## Decisions
1. **Fresh process** (ticket default). The timed pass leaves fragmented arenas in its process; a same-process second pass would inherit them and could not show a working set. Cost: one more child process per record that asks for it. The child rebuilds the state from the same name, seed and RunSpec tick counts (deterministic), so it measures the same run shape.
2. **Opt-in** (`--memory-pass` on `rerun_baselines.py measure` and `record`), off by default and off in nightly and the tripwire. A record says whether the pass ran by the presence of the `working_set_*` keys.
3. **Merge, don't re-time.** The parent writes the timed record first (`<run>.timed.json`), then merges only `memory_mb` keys (and `schema_version`) into it. The timed fields cannot change because the pass runs after the timed window, in another process, and the merge touches nothing else. The real-run evidence for AC2 is the in-run equality of the merged record's timed fields with `<run>.timed.json`; two separate timed runs differ by host noise regardless of the pass (the same code on the same host varied up to 4.3x in an identical spin, and the record-level spread rule exists for that), so a byte-for-byte comparison of two separate runs would test the host, not the pass.
4. **Schema 1.3** (MINOR, additive).
5. **AC1 error bound**: ±10 % of 106.2 MB, i.e. **95.6 to 116.8 MB**. Reason: the collector-on readings above span 99.9 to 109.4 MB (about ±5 % around 104.7) before any process-to-process variation, so ±10 % brackets them with a margin and is far from the old 311 MB after-trim reading. Second condition: `working_set_delta_mb` below 25 MB (collector-on window growth was +3.1 to +11.5 MB at 200 ticks and +5.6 MB over warm-up at 1100). A value outside the bound is reported as it is; the bound is not edited to fit.

## Conflicts / ownership
- `src/perf/**` and `tools/perf/**`, `tests/unit/perf/**`, `docs/performance/**` are ours. No `src/` outside `src/perf/`.
- Heavy run only after perf-planner clears it with lead (platform's compose build goes first). The code and tests need no run.
