---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION
artifact_type: test_plan
tags: [simulation-quality, world, corpus, performance]
---

# Test Plan — TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION

## New tests (`tests/tools/test_corpus_perf_baseline.py`)

1. `test_bench_corpus_world_loads_real_state` — `_load_world_state` reused correctly returns a
   real `AuthoritativeState` for a known corpus world (not a mock).
2. `test_perf_baseline_scenario_id_matches_run_key_convention` — committed baseline `scenario_id`
   values use the real corpus world name (`simq_corpus_{world}`), distinguishable from the
   existing synthetic `combat_10`/`idle_100`-style IDs.
3. `test_corpus_baseline_json_schema_matches_existing_baselines` — the new committed baseline
   JSONs have the same real field set as existing baselines (`avg_tick_compute_ms`,
   `tick_ms`/`mem_rss_mb` sub-dicts, etc.) — confirms this ticket followed the actually-live raw
   dict shape, not the unused `PerfBaseline` dataclass shape (different field names).

## Regression coverage (`tests/perf/test_perf_regression_baseline.py`)

The 3 new `simq_corpus_*` scenarios get added to this file's own existing `parametrize` list,
reusing its real, already-exercised comparison logic — no new comparison mechanism.

## Real-kernel verification

Run `tools/bench_corpus_world.py --world frontier_extended` once for real, confirm a genuine
`PerfResult` is produced and looks sane (non-zero tick cost, non-zero memory) before committing it
as a baseline.

## Scoped pytest command

`.venv/bin/python3 -m pytest tests/tools/test_corpus_perf_baseline.py -q`
