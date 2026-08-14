---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION
artifact_type: plan
tags: [simulation-quality, world, corpus, performance]
---

# Plan — TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION

## Steps

1. `tools/bench_corpus_world.py` (new): CLI, `--world {name} --seed {n}`, reuses
   `calibrate_simq.py::_load_world_state` to build the real `AuthoritativeState`, runs
   `BenchHarness(PROD_SMALL).run_benchmark(scenario_id=f"simq_corpus_{world}", initial_state=state)`,
   writes the raw result dict to `tests/perf/baselines/simq_corpus_{world}.json` when `--commit`
   is passed (default: print only, don't silently overwrite a baseline) — same raw-dict shape as
   the existing committed baselines (`idle_100_local.json` etc.), NOT the unused `PerfBaseline`
   dataclass, per the corrected finding above.
2. Run for real against `frontier_extended`, `frontier_marches`, `crowded_frontier` — commit the 3
   resulting baselines.
3. `tests/perf/test_perf_regression_baseline.py`: add the 3 new `simq_corpus_*` scenario_ids to
   its own existing `@pytest.mark.parametrize` list, reusing the file's real, live comparison
   logic — not a new, parallel test file with its own comparison mechanism (that would be a 3rd
   parallel perf-comparison approach in one repo).
4. `docs/performance/perf_baseline_policy.md`: document the new `simq_corpus_*` baseline family,
   `tools/bench_corpus_world.py`, and the `PerfRegressionGate`-is-currently-unused finding (so a
   future reader doesn't repeat the same wrong assumption this ticket started with).
5. `corpus_registry.yaml`'s own generator (ticket 1) is NOT modified in this ticket — perf-baseline
   coverage as a registry field is a nice-to-have, not blocking; left as a natural small follow-up.

## Acceptance-criteria map

| AC | Step |
|---|---|
| investigation.md confirms input compatibility + corrected piggyback framing | Investigate (done) |
| calibrate_simq/evaluate_simq can optionally emit PerfResult, no default-behavior change | Step 1 (separate CLI, not a flag inside evaluate_simq.py itself — see Implementation Notes for why) |
| Largest few worlds have committed PerfBaseline entries | Step 2 |
| Scoped pytest check runs PerfRegressionGate against corpus baselines | Step 3 |
| Scoped pytest passes | Step 3 |
