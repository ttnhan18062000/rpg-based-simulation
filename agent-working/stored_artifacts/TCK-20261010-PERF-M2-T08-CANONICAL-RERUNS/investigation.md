---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS
date: 2026-10-13
tags: [performance, benchmarking, regression]
---

# Investigation: TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS

1. **Hunting batch is merged** (#536, `b396080cc`; main is 06aa3a20c): no pre-hunting label; `combat_10_*` and fighting corpus worlds still `WORK_MODEL_V1` (`contract.work_model_version`, set by `collect_identity`).
2. **The 15 legacy files** are listed in `baseline_lifecycle.LEGACY_TRIPWIRE_REFERENCES`; a promoted baseline is `<name>.vNNNN.json`, and `tripwire.load_baseline` reads the latest version, so replacing a legacy file means promote, then delete it and drop it from that set. `tests/perf/test_perf_regression_baseline.py` reports INCONCLUSIVE for a legacy file and executes no head run, so the policy 2.2 step 4 check against the old file is cheap; its output is kept.
3. **Protocols to keep:** `*_local/_concurrent` were 10 warmup + 20 sampled ticks (`run_benchmarks.py --smoke`, `sample_ticks: 20` in every file); `simq_corpus_*` were 100 + 1000 on `PERF_512MB_LOCAL` (`bench_corpus_world.py` defaults). Old peak RSS (max): 38-48 MB for the scenario files, 696 / 1506 / 1405 MB for the three corpus worlds.
4. **No existing tool makes a corpus-world record**: `capacity_run` builds `SCENARIO_BUILDERS` only; `bench_corpus_world.py` writes the legacy dict. A small `tools/perf/rerun_baselines.py` (perf-owned) is needed; it imports `calibrate_simq._load_world_state` read-only.
5. **Step 6 shape:** `src gate` / `compare-sweep` do `BaselineConfig.model_validate` (`baseline_generator.BaselineConfig`, `baseline_v1`) and `tick_cost_incomparable_reason` needs `cost_accounting_version == COST_ACCOUNTING_VERSION`. A schema-1.1 `BenchmarkRecord` does not validate. The honest replacement is a generated `BaselineConfig` from a real sweep. `docs/observability/baselines/*` other than `latest.json` have no code consumer (ledger 3.2).
6. **Lift boundary:** `baseline_comparator.py` and `sweep_report.py` are in the OD-8 lift, `src/cli/entry.py` is not; no change to any is planned.
7. **Open before the first run:** the `combat` scenario's builder arguments for `combat_10` (read from `run_benchmarks.py`, team_a = team_b = scale) and what `evaluate_simq.py` costs (unknown RSS; first run measured under a 2.5 GB cap).

## Added on perf-planner's go (2026-10-13, conditions 2 to 4)

### A. No-consumer evidence for the 16 files to delete (condition 2)
Search: `grep -rIn -F "observability/baselines"` over `src/ tools/ tests/ .github/ Makefile docs/ agent-working/tickets` (excluding `.git`, `.venv`, `data/`, `reports/`), plus a per-basename search `grep -rIl -F "<name>.json"` over `src tools tests .github Makefile docs`. The per-basename search is ambiguous for 15 names (the same basenames exist under `tests/perf/baselines/`, so `tools/perf/baseline_lifecycle.py`'s legacy set, `tests/unit/perf/test_baseline_lifecycle.py`, `tests/tools/test_corpus_perf_baseline.py` and the policy/inventory docs match them by basename only), so the path-qualified search is the deciding one:
- **Code (src, tools, tests, .github, Makefile): no file reads or writes any `docs/observability/baselines/*` file other than `latest.json`.** `tools/perf/perf_report.py` reads `reports/perf/matrix_full.json` (its `input_dir` is `Path("reports/perf")`, git-ignored, written by `run_benchmarks.py`), not the docs copy. `tools/perf/run_perf_baseline.py` writes `reports/perf/latest.json`, not the docs path. `test_perf_idle_baseline` is only a test function name (`tests/perf/test_perf_idle.py`), not the file.
- **Docs that mention the directory:** `docs/performance/baseline_invalidation_ledger.md` (updated by this ticket), `docs/guides/observability.md:157,161` and `docs/guides/simulation.md:98` (they name `latest.json` only, which stays at the same path; the surrounding sentence gets a note on what the file is), `docs/archive/observability/foundation.md:17` (archive, names `latest.json`; left as written), two plan docs that name `latest.json` or T08 (history). None names a matrix file or `matrix_full.json` as a thing to read. `docs/performance/benchmark_identity_schema.md` F5 is `reports/perf/matrix_full.json`, a different, git-ignored path.
- Therefore the 14 per-profile files, `matrix_full.json` and `test_perf_idle_baseline.json` have no consumer, and the docs-only mentions that exist are updated in this PR (ledger) or concern `latest.json` (kept). `src gate` / `compare-sweep` read `latest.json` only.

### B. The combat adapter (condition 3), copied from `tools/perf/run_benchmarks.py`
`run_matrix`: `if scenario_name == "combat": state = builder(team_a_count=scale, team_b_count=scale)` (builder = `SCENARIO_BUILDERS["combat"]` = `build_combat_arena_state(*, team_a_count, team_b_count, seed=42)`), so `combat_10` is `team_a_count=10, team_b_count=10`, default `seed=42`. The other scenarios: `resource`: `builder(entity_count=scale, node_count=scale // 2)`; everything else: `builder(entity_count=scale)`. `rerun_baselines.py` copies these call shapes, not a guess; `strategic` and `idle` and `movement` use `entity_count`.

### C. Profile of each old file, read from its `profile` field (not from the name)
`combat_10_local` PERF_2GB_LOCAL; `combat_10_concurrent` PERF_2GB_CONC; `idle_100_local` PERF_512MB_LOCAL; `idle_100_concurrent` PERF_1GB_CONC; `movement_100_local` PERF_1GB_LOCAL; `movement_100_concurrent` PERF_2GB_CONC; `resource_100_local` PERF_1GB_LOCAL; `resource_100_concurrent` PERF_2GB_CONC; `strategic_100_local` PERF_2GB_LOCAL; `strategic_100_concurrent` PERF_2GB_CONC; the three corpus worlds PERF_512MB_LOCAL (mixed_200_*: PERF_1GB_LOCAL and PERF_2GB_CONC, pending). (Note the names do not predict the profile: `combat_10_local` is 2GB, not 512MB.)

### D. Where the expected RSS and wall come from (condition 4)
All from the old committed record of the same name: peak RSS = `mem_rss_mb.max` and wall = `wall_clock_s` (the sampled window only; the process also builds the state and warms up). Scenario files: `mem_rss_mb.max` 38.4 to 48.5 MB, `wall_clock_s` about 2.0 s (20 sampled ticks). Corpus: `simq_corpus_crowded_frontier` 696.3 MB / 8.25 s, `simq_corpus_frontier_extended` 1505.6 MB / 13.12 s, `simq_corpus_frontier_marches` 1405.1 MB / 11.77 s (1000 sampled ticks each). **Those exceeded their own profile**: `PERF_512MB_LOCAL` declares `ram_mb=512`, so 696 to 1506 MB is 1.4x to 2.9x of it. The profile's `ram_mb` is the modelled class used for the governor's memory guard, not an enforced process limit (memory guards exist only in LIVE; `performance_contract.md`), so the run was not killed; the old records are evidence of this, and the new ones will show whether the same holds. The measured max-RSS (from `mem_rss_mb.max` and the cgroup's `memory.peak`) and wall of each new run are stored beside its record.

## E. Measured results and the off-NORMAL evidence (2026-10-13; main 06aa3a20c, host `ubuntu`, i5-11400H 6 vCPU, loaded: 1-min load 0.6 to 5.3, swap 5.7 to 6.8 GB)
Each record: 3 fresh-process runs, median avg promoted, spread = max/min - 1, NOISY above 15 %. Raw files and summaries: `reports/perf/t08/` (first attempt) and `reports/perf/t08_retry/` (the one quiet-window retry of the 6 NOISY ones, load 0.6 to 1.2 at each start).

**Records that leave NORMAL under the canonical contract (not a baseline, contract 3.1; identical in all 3 runs, because the modelled cost does not depend on the host):**

| record | profile (canonical) | mode counts (ticks) | avg tick (median run) | top phases (avg ms) |
|---|---|---|---|---|
| `strategic_100_local` | PERF_2GB_LOCAL | CONSTRAINED 20 | 495.8 ms | cooperation 260.0, resolution_overhead 101.3, advancement 83.9, combat_engagement 28.3 |
| `strategic_100_concurrent` | PERF_2GB_CONC | SURVIVAL 20 | 398.9 ms | cooperation 197.9, resolution_overhead 95.3, advancement 63.9, combat_engagement 26.1 |
| `simq_corpus_frontier_extended` | PERF_512MB_LOCAL | NORMAL 40, CONSTRAINED 44, DEGRADED 14, SURVIVAL 902 | 165.9 ms | advancement 69.9, resolution_overhead 35.7, cooperation 32.0, combat_engagement 10.8 |
| `simq_corpus_frontier_marches` | PERF_512MB_LOCAL | NORMAL 10, CONSTRAINED 876, NORMAL 114 | 97.9 ms | advancement 37.3, resolution_overhead 22.3, cooperation 17.2, combat_engagement 6.1 |

`baseline_lifecycle promote` refused `strategic_100_local` and `simq_corpus_frontier_extended` with `mode_not_normal`; the other two were not offered. The old May files read 13.2 ms (`strategic_100_local`), 13.3 ms (`frontier_extended`) and 16.0 ms (`frontier_marches`), so the tick cost of these scenarios has grown by about 12x to 38x since (the May pipeline had 5 buckets; the tick now has 30 phases, with `cooperation` and `advancement` the largest). This is evidence for the owner decision on a larger-budget canonical profile (not made here). The old numbers are not a regression measurement: they predate DEV-017 and the 30-phase tick.

**Memory vs the profile's declared RAM.** `simq_corpus_frontier_extended` peaked at `memory_mb.rss_high_water` 1688.7 MB (cgroup run: 1703 MB process peak) and `frontier_marches` at 1554.7 MB (1568 MB), on `PERF_512MB_LOCAL` (declares `ram_mb=512`); `crowded_frontier` 797 MB. **Nothing flags it:** `BenchHarness` records `rss_high_water` but never compares it with the profile's `ram_mb`, `compare()` does not read memory, and the governor's memory guard exists only under LIVE (`performance_contract.md` section 3.1), not under the canonical contract these runs use. The old records already exceeded the profile the same way (696 to 1506 MB).

**Retry in the quiet window (one, as approved):** `combat_10_concurrent` 9.6 % and `resource_100_concurrent` 12.5 % became promotable and were promoted; `idle_100_local` 22.1 %, `movement_100_local` 28.8 %, `combat_10_local` 96.9 % and `simq_corpus_crowded_frontier` 32.8 % stayed above 15 % and are PENDING-NOISY in the ledger.

## F. The four PENDING-NOISY records: what the stored data shows (input for the follow-up ticket)
**Per-tick series were not kept.** The 26 measured runs were made with `samples_dir=None`, so a record holds only `latency_ms` {min, p50, avg, p95, max}, not the per-tick list; the claim "the first ticks after warm-up dominate" cannot be tested from these files. `rerun_baselines.py record --keep-samples` now keeps every sampled tick of each run under `<out>/<name>/samples/` (OD-6 pointer), for the follow-up. Per run (first window = load 2.2 to 2.7, retry = quiet window, load 0.6 to 1.3 at start); values in ms:

| record | window | run 1 min / p50 / avg / p95 / max | run 2 | run 3 | spread |
|---|---|---|---|---|---|
| idle_100_local | first | 49.4 / 63.1 / 62.4 / 71.9 / 74.0 | 49.3 / 60.4 / 61.0 / 70.4 / 72.2 | 31.1 / 44.2 / 46.1 / 60.7 / 67.1 | 35.3 % |
| idle_100_local | retry | 30.0 / 31.8 / 32.2 / 35.9 / 37.3 | 30.4 / 32.6 / 35.8 / 56.7 / 57.8 | 33.8 / 37.8 / 39.3 / 47.2 / 61.8 | 22.1 % |
| movement_100_local | first | 92.7 / 125.6 / 126.6 / 154.1 / 232.6 | 62.6 / 108.3 / 108.6 / 165.5 / 177.2 | 65.5 / 117.2 / 109.9 / 148.5 / 171.9 | 16.6 % |
| movement_100_local | retry | 89.1 / 133.6 / 134.9 / 161.2 / 166.8 | 101.3 / 125.8 / 126.8 / 146.0 / 155.1 | 65.0 / 112.4 / 104.8 / 151.4 / 156.3 | 28.8 % |
| combat_10_local | first | 31.9 / 40.3 / 47.3 / 73.4 / 97.3 | 49.3 / 65.2 / 67.8 / 80.4 / 93.1 | 51.4 / 64.8 / 64.5 / 72.5 / 81.7 | 43.3 % |
| combat_10_local | retry | 24.7 / 30.6 / 30.7 / 34.6 / 35.5 | 41.5 / 58.3 / 59.8 / 71.4 / 77.2 | 25.0 / 29.7 / 30.4 / 34.6 / 35.0 | 96.9 % |
| simq_corpus_crowded_frontier | first | 25.9 / 61.8 / 69.7 / 119.2 / 570.4 | 20.1 / 52.1 / 58.8 / 99.4 / 564.4 | 22.3 / 40.6 / 51.3 / 113.5 / 866.6 | 35.8 % |
| simq_corpus_crowded_frontier | retry | 22.4 / 80.4 / 91.5 / 178.4 / 411.3 | 25.9 / 70.3 / 83.9 / 158.3 / 451.2 | 20.9 / 71.5 / 68.9 / 108.3 / 226.1 | 32.8 % |

Reading, from these numbers only: (1) inside a run, avg and p50 agree for the three synthetic records (for example combat_10_local retry 30.7 vs 30.6, 59.8 vs 58.3, 30.4 vs 29.7), so the spread comes from **between processes**, not from a few slow ticks; (2) `combat_10_local` in the quiet window is **bimodal across processes**: two runs at about 30 ms and one at about 60 ms (a 2x step, p50 and the whole distribution shifted), which a longer sample would not average away; a per-process cause (CPU frequency or core placement on the VM, allocator or hash layout) is plausible and untested; (3) `crowded_frontier` has real tail ticks (max 226 to 867 ms against p50 41 to 80 ms), so there a few slow ticks do widen the average; (4) the quiet window cut the idle and combat variance but not the movement one. The follow-up should start from `--keep-samples` data (does a warm-up drop or a longer run narrow it, and is the 2x step per process), before another window.

## G. The two `mixed_200_*` records, after the spawn-collision fix (#544 merged, main 4b5d1bdfb; engine commit a002cc1dd, clean `src/`)
| record | profile (canonical) | mode counts | avg tick (median run) | spread | top phases (avg ms) |
|---|---|---|---|---|---|
| `mixed_200_local` | PERF_1GB_LOCAL | CONSTRAINED 20 in all 3 runs | 167.5 ms (old file: 18.8 ms) | 4.3 % | cooperation 63.1, combat_engagement 42.9, resolution_overhead 27.5, collection 13.3 |
| `mixed_200_concurrent` | PERF_2GB_CONC | CONSTRAINED 20 in all 3 runs | 182.3 ms (old file: 28.2 ms) | 13.8 % | cooperation 61.3, resolution_overhead 44.4, combat_engagement 41.7, collection 14.6 |

Both leave NORMAL, so they are not baselines under the canonical contract (same rule as `strategic_*`); not promoted, old files stay as legacy references. Peak RSS 78 to 79 MB, 5.4 to 6.9 s per run, 1-min load 1.15 to 1.23 at each start. Expected before the run (from the old files): RSS 47.6 and 48.5 MB (`mem_rss_mb.max`), 2.02 s (`wall_clock_s`, sampled window only). The workload is **140 entities** (`build_mixed_state(entity_count=200)` builds 40 % heroes + 30 % monsters = 140 plus 60 resource nodes), not 200, which is what the old name meant too.
