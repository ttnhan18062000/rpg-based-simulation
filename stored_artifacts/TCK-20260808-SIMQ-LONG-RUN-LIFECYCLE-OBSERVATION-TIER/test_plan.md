---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER
artifact_type: test_plan
phase: investigate
date: 2026-08-08
tags: [simulation-quality, calibration]
---

# Test Plan — TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER

## New tests — `tests/tools/test_simq_long_run_observation.py`

1. `test_default_world_subset_matches_calibration_precedent` — the CLI's default `--worlds` list
   equals the 6-world set already established by `TCK-20260808-ENTITY-LIFECYCLE-SCORE-
   CALIBRATION`'s own density sample, not re-invented.
2. `test_observe_one_world_produces_both_signals` — a real, short (e.g. 50-tick, to keep the test
   fast) run of `sandbox_world` through the tool's own orchestration function produces a dict with
   both a `simq_report` key (real pillar grades) and a `lifecycle_score` key (real entity
   metrics), and cleans up its own `data/runs/` directory afterward.
3. `test_output_written_to_docs_long_run_observations_dir` — the function writes its output to
   `docs/simulation_quality/long_run_observations/`, not `data/`.
4. `test_engine_driven_only_once_per_world` — monkeypatch/spy on the Kernel-driving function to
   assert it's called exactly once per world (not twice — the whole design point of reusing one
   run_dir for both signals).

## Regression guard

`pytest tests/tools/test_simq_long_run_observation.py tests/tools/test_entity_lifecycle_score.py
tests/tools/test_corpus_registry.py -q`
