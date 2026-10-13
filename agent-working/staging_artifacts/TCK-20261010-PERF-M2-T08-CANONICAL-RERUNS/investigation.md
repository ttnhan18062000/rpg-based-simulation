---
status: active
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
