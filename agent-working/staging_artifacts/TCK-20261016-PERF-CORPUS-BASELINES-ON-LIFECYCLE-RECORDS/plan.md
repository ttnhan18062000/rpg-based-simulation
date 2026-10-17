---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS
date: 2026-10-18
tags: [performance, benchmarking]
---

# Plan: TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS

Not implemented. Sent to perf-planner for review before code. No measured run; no `src/` change.

## Changes
1. `tools/bench_corpus_world.py`: remove `--commit`, `BASELINES_DIR` and the write; docstring says it prints the harness dict and that baselines come only from `rerun_baselines.py record` then `baseline_lifecycle.py promote`. `bench_corpus_world()` unchanged.
2. `git rm tests/perf/baselines/simq_corpus_crowded_frontier.json`; drop it from `LEGACY_TRIPWIRE_REFERENCES` (9 -> 8); update the length pin and its comment in `tests/unit/perf/test_baseline_lifecycle.py`.
3. `tests/tools/test_corpus_perf_baseline.py` (**gated, #623: draft only, commit after agent-working agrees**):
   - Promoted worlds (a world with a `<name>.vNNNN.json`): `tripwire.load_baseline("simq_corpus_<world>")` returns a record; assert `identity.scenario.id`, `schema_version`, `result.latency_ms["avg"] > 0`, and `memory_mb['rss_high_water'] > 0` (plus `rss_after_trim_mb <= rss_high_water` when present).
   - Raw-dict worlds (`frontier_extended`, `frontier_marches`): assert a fixed key set `{"scenario_id","profile","avg_tick_compute_ms","tick_ms","mem_rss_mb"}` in the test itself; no `idle_100_local.json` read.
   - The test chooses promoted vs raw-dict per world by `baseline_lifecycle.version_files`, so a later promotion of a world moves it to the record branch with no test edit.
4. New pin test in `tests/unit/perf/` (ours): (a) `bench_corpus_world.main` with `--commit` exits 2 (argparse rejects it); (b) no module under `tools/` or `src/` writes a `simq_corpus_*.json` baseline: a scan for `simq_corpus_` together with `write_text`/`open(..., "w")` outside `baseline_lifecycle.py` finds nothing. Uses `tools.agent_working_paths` where a path is needed (paths guard).
5. Docs (P1, owner approves in the PR): `perf_baseline_policy.md` §4 (lines ~112, 121) and §6 (lines ~155-170: the `--commit` procedure becomes `record` + `promote`); ledger row line 65 and plan table line 142; `benchmark_identity_schema.md` F1/F4 (the `--commit` writer is gone); `performance_clause_inventory.md` BP-17 and D-8. Then `make knowledge-index-update`.

## Acceptance map
AC1: new test passes with the legacy file gone. AC2: pin test (4). AC3: `baseline_lifecycle.py check` rc=0 and the pin = 8. AC4: docs edited; owner approval in the PR.

## Order of commits
(1) tickets, staging; (2) `--commit` removal + pin test + docs for the removal (policy §4/§6, ledger step 1, schema F1/F4, inventory BP-17/D-8); (3) only after #623 clears: the `tests/tools` edit + `git rm` of `simq_corpus_crowded_frontier.json` + list 9 -> 8 + length pin + the docs lines that say the file is retired (policy §4 line 121, ledger line 65, schema F3). Every commit stays green (review change 1). Tell perf-planner before each commit.
