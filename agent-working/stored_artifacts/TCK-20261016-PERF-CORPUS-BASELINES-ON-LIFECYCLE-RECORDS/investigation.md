---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS
date: 2026-10-18
tags: [performance, benchmarking]
---

# Investigation: TCK-20261016-PERF-CORPUS-BASELINES-ON-LIFECYCLE-RECORDS

Read-only. Context scan: `search_docs` (policy §4/§6, SIMQ-CORPUS-PERF-BASELINE-INTEGRATION), `graphify query`, then grep to narrow.

## Who reads or writes the legacy corpus files
- `tests/tools/test_corpus_perf_baseline.py`: `test_perf_baseline_scenario_id_matches_run_key_convention` reads `simq_corpus_{world}.json` for `frontier_extended`, `frontier_marches`, `crowded_frontier`; `test_corpus_baseline_json_schema_matches_existing_baselines` reads the same three **and `idle_100_local.json` as its shape reference**. So the T08 close (#613) deleting `idle_100_local.json` would break it.
- `tools/bench_corpus_world.py --commit`: the only writer of `simq_corpus_*.json` (`BASELINES_DIR / f"simq_corpus_{world}.json"`). No Makefile, workflow or other tool calls `--commit` (grep over *.py, Makefile, *.yml, *.yaml, *.toml). `bench_corpus_world()` itself (the function) is imported by the test and by nothing else; it stays.
- `tests/perf/test_perf_regression_baseline.py` uses `tripwire.load_baseline(name)` (prefers the promoted version) and names no corpus world. `rerun_baselines.py` knows `simq_corpus_{world}` names but writes candidates, not baselines.
- `LEGACY_TRIPWIRE_REFERENCES` has 9 names; `tests/unit/perf/test_baseline_lifecycle.py:162` pins the length.

## Promoted record shape (`simq_corpus_crowded_frontier.v0001.json`)
`schema_version` 1.2; `identity.scenario.id` = `simq_corpus_crowded_frontier`; `identity.content.world_id`; `result.latency_ms.avg`; `result.memory_mb.rss_after_trim_mb`/`rss_high_water`; `promotion` block (version 1, cause TCK-20261014-...). `tripwire.load_baseline` returns `(BenchmarkRecord, "")` for it.

## Conflicts / ownership
- `tests/tools/**` belongs to agent-working (`registries/session_roles.yaml:55`). Gate: GitHub issue #623. Draft locally; no commit of that file until perf-planner relays agreement.
- Ordering with T08 (#613): see both tickets' Assumptions.
- Docs touched are P1/P2 in `docs/performance/`; owner approves them in the PR.

## Decision: remove `--commit` (do not convert to a candidate writer)
`rerun_baselines.py record` already writes the candidate (3 or 5 fresh-process runs, quiet window, median) and `baseline_lifecycle.py promote` is the only path to a baseline. A `--commit` that wrote a second candidate kind would duplicate it and skip the quiet-window and spread rules. No caller exists. Removing it is the smaller change.
