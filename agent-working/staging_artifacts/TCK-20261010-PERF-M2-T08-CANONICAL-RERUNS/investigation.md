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
