---
status: active
layer: performance
authority: P1
audience: developer
---

# Engine Performance Baseline Policy

## 1. Purpose and Scope

This document is the **calibration procedure** for performance baselines. It is not where performance
is defined, measured, compared, or claimed: since PERF-D4 (approved 2026-10-03) that is
`docs/engine/performance_contract.md`, the single clause-level authority. Hardware classes are
defined once, in `docs/engine/contracts/certification_contract.md` §3. The row-by-row evidence for
this restructuring is `docs/performance/performance_clause_inventory.md`.

What this document used to contain, and where it went:

| Earlier content | Now |
|---|---|
| Benchmark protocol (100 warmup, 1,000 sampled ticks) | `performance_contract.md` §3.2, as capacity-run minimums |
| Hardware-class table (`CLASS_A`/`B`/`C` by cores and RAM) | Removed. It contradicted `certification_contract.md` §3 (for example `CLASS_A` here was 8+ cores and 16 GB, there 16 logical cores and 32 GB). The per-class entity targets moved to `performance_contract.md` §5.1, keyed to the certification classes |
| CI regression thresholds (p50 5%, p95 10%, p99 15%; RSS and GC bounds) and the `UnacceptableRegressionError` rule | Moved to `performance_contract.md` §5 and §5.1 as documented targets that no check enforces yet. The mechanism the old text described did not run: `PerfRegressionGate` has no production caller and no `UnacceptableRegressionError` exists |
| Calibration steps | Rewritten below to name what exists |

---

## 2. Calibration procedure

A baseline is a reference for a comparison made by a projection of the performance contract
(`performance_contract.md` §3.3). Which projection it serves decides what it may be used for.

### 2.1 What a baseline is, today

- The 15 JSON files in `tests/perf/baselines/` are **tripwire references only**. They carry no capacity
  claim. 12 of them are 20-tick samples taken by the smoke benchmark; only the three `simq_corpus_*`
  files record 1,000 sampled ticks.
- The synthetic-scenario files (`idle_100_local.json`, `movement_100_local.json`, ...) have the shape
  and file names produced by `tools/perf/run_benchmarks.py` (one JSON per scenario, scale and mode, with
  `matrix_scenario`, `matrix_scale`, `matrix_mode` fields). No script copies them into
  `tests/perf/baselines/`; the only tool that writes there is `tools/bench_corpus_world.py --commit`
  (§3 below).
- The live comparison reads the committed JSON directly and compares `avg_tick_compute_ms` only
  (`tests/perf/test_perf_regression_baseline.py`). A missing file is skipped. Under the performance
  contract a missing or incompatible baseline is `INCONCLUSIVE`; that outcome is not implemented yet
  (`PERF-M2-T03`).

### 2.2 To refresh a tripwire reference

1. **Isolate the machine.** No other CPU- or disk-heavy process should be running. Pin to isolated
   cores if available. Record the environment: interpreter version and build, OS, architecture, and the
   hardware class that `certification_contract.md` §3 assigns to the host (the PERF-D2 runtime identity;
   storing it in the file is pending `PERF-M2-T02`).
2. **Run the benchmark.** `python3 tools/perf/run_benchmarks.py --smoke` writes one JSON per scenario
   (the same 10-warmup, 20-sample sizes as the committed references). Use the same profile name the
   existing file records in its `profile` field.
3. **Check the run stayed in `NORMAL`.** The result's `mode_sequence` must contain only `NORMAL`; a
   baseline measured while the governor left `NORMAL` is not valid (`performance_contract.md` §3.1).
4. **Compare before committing.** Run `python3 -m pytest tests/perf/test_perf_regression_baseline.py -m "slow"`
   against the old file, then replace the file. A change that raises the baseline needs its rationale
   recorded in the commit message (`performance_contract.md` §5).
5. **Commit** the changed `tests/perf/baselines/*.json` files with a commit message that names the
   scenario and the reason. Nothing else (no timestamp in `performance_contract.md`) is updated: that
   document carries no baseline revision.

No capacity-run baseline exists, and there is no calibration procedure for one yet (`PERF-M2-T04`).

### 2.3 Named benchmark results

- **SimQ mode isolation overhead** (`QUALITY_SCORING_DISABLED=1` vs. in-process vs. broker):
  `docs/performance/simq_isolation_overhead.md`, produced by
  `tests/perf/test_simq_isolation_overhead.py`. This is a **comparative** result in the sense of
  `performance_contract.md` §3.3.

---

## 3. SimQ Corpus World Baselines (`TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION`)

Prior to 2026-08-08, all committed baselines (`tests/perf/baselines/*.json`) covered only
synthetic scenarios (`combat_10`, `idle_100`, `mixed_200`, `movement_100`, `resource_100`,
`strategic_100`, via `src/perf/scenarios.py`'s raw `State` builders) — none of the real, authored
SimQ world corpus (`data/worlds/`) had ever been perf-measured.

`tools/bench_corpus_world.py --world {name} [--commit]` benchmarks a real corpus world: reuses
`tools/calibrate_simq.py::_load_world_state()` to build the same real, `WorldCompiler`-compiled
`AuthoritativeState` SimQ calibration uses (no synthetic content, no separate authoring), then runs
`BenchHarness(PERF_PROFILES["PERF_512MB_LOCAL"]).run_benchmark(...)` — a genuinely separate,
dedicated benchmark execution (NOT a free byproduct of a calibration run — `BenchHarness` runs its
own warmup+sample tick loop). Writes the same raw-dict JSON shape as the existing baselines
(`avg_tick_compute_ms`, `tick_ms{}`, `mem_rss_mb{}`, `phase_breakdown{}`), so
`tests/perf/test_perf_regression_baseline.py`'s own real, live comparison logic applies unchanged
— committed baselines are added as new `(scenario_id, builder_fn, kwargs)` rows in that file's own
`parametrize` list.

**Coverage so far**: `simq_corpus_frontier_extended` (59 entities), `simq_corpus_frontier_marches`
(62 entities), `simq_corpus_crowded_frontier` (38 entities) — the corpus's largest 3 worlds by
entity count at the time this ticket ran. Extending coverage to the remaining corpus worlds, or to
`TCK-20260808-SIMQ-LARGE-SCALE-WORLD-VALIDATION`'s own new large world once it exists, is a
natural follow-up using the same `tools/bench_corpus_world.py --commit` command — not automated in
this ticket.
