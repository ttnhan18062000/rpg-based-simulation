---
status: historical
layer: simulation
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260817-STANDARD-SIMQ-STALE-ANCHOR-RECALIBRATION-BATCH
tags: [simulation-quality, calibration, testing, bug]
---

# Test Plan — TCK-20260817-STANDARD-SIMQ-STALE-ANCHOR-RECALIBRATION-BATCH

## Scope
Verify the 4 recalibrated anchors pass individually and that no other test in the file
regressed.

## Commands and results

Pre-fix (all 4 failing with stale anchors — captured during investigation):
```
pytest tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed42_200t_social_grade_stability -m slow --resource-budget large -q
pytest tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability -m slow --resource-budget large -q
pytest tests/unit/worldassembly/test_corpus_diversity.py::test_frontier_living_world_seed42_200t_social_grade_stability -m slow --resource-budget large -q
pytest tests/unit/worldassembly/test_corpus_diversity.py::test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability -m slow --resource-budget large -q
```
All 4: 1 failed each (score-tolerance AssertionError, see investigation.md for exact messages).

Post-fix, batch run (4 tests in one `pytest` invocation, sequential within the same process):
```
=== test_urban_political_seed42_200t_social_grade_stability ===       1 passed in 15.95s
=== test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability === FAILED (1 failed in 18.15s)
=== test_frontier_living_world_seed42_200t_social_grade_stability ===  1 passed in 28.73s
=== test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability === 1 passed in 105.54s
```
Test 2's single failure investigated immediately: re-ran it alone (fully isolated, no concurrent
pytest processes) 3 times total — all 3 passed (`1 passed in 30.22s`, `1 passed in 31.08s`,
`1 passed in 30.85s`). The one failure occurred while it ran back-to-back with the other 3 heavy
engine-simulation tests in the same batch (self-inflicted concurrent load) — this matches the
exact documented `TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE` mechanism (CI's real
`slow` job deliberately runs this suite as isolated per-test subprocesses for exactly this
reason, via `make simq-corpus-diversity-slow-isolated`). Not treated as evidence the abs_floor is
too tight — 3/3 clean isolated passes is the correct verification standard here, matching how
the suite is actually invoked on CI.

## Regression check
No other test in `test_corpus_diversity.py` was touched by this ticket's edits (dict-literal
edits are scoped to exactly the 4 anchors' own `anchors = {...}` blocks). No `src/` file changed,
so no broader regression surface.

## Final status
All 4 tests pass individually and reliably under isolated execution, matching CI's real
invocation pattern.
