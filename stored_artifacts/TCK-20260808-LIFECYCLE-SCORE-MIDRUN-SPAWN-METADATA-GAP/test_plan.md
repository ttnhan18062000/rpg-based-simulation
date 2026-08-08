---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP
artifact_type: test_plan
phase: investigate
date: 2026-08-08
tags: [simulation-quality, observability, world]
---

# Test Plan — TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP

## New/updated tests — `tests/tools/test_entity_lifecycle_score.py`

1. `test_run_for_analysis_returns_final_entities` — `_run_for_analysis()`'s new 3-tuple return
   includes a real, non-empty `final_entities` dict after a short real run.
2. `test_midrun_spawned_entity_gets_real_metadata` — real, short (e.g. 200-tick) `wilderness_survival`
   run (a world already confirmed in the real 2000-tick data to produce mid-run spawns): assert
   the `"None"` role group shrinks relative to a pre-fix baseline, or is empty if the run is short
   enough that no entity is both born and removed within it.
3. `test_run_dir_mode_still_works_without_final_entities` — `--run-dir` mode (scoring an existing
   run without a live Kernel) doesn't crash; documented pre-run-only fallback still functions.

## Regression guard

`pytest tests/tools/test_entity_lifecycle_score.py tests/tools/test_simq_long_run_observation.py -q`

## Real re-verification (not just unit tests)

Re-run `make simq-long-run-lifecycle-observation` (2000 ticks, 6 curated worlds) after the fix and
confirm the `"None"` role group shrinks materially across all 6 worlds — real evidence, not
assumed from the unit tests alone.
