---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS
date: 2026-09-06
---

# Test Plan: TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS

## New Tests
- `tests/simulation_quality/test_region_transformation_pipeline_corpus.py`
  - `test_forest_region_transforms_to_burnt_forest_through_real_pipeline_after_a_combat_death` —
    positive path: real trauma accumulation + real transformation + real event emission, all through
    production code (`AuthoritativeApplyPipeline.refine()`, `ApplyPath.apply_generation()`,
    `EventExtractor.extract()`/live shaper path).
  - `test_no_transformation_below_the_real_threshold_through_the_same_real_pipeline` — negative
    path: same pipeline, trauma stays under threshold, no transformation and no event fire. Would
    fail if the transformation logic regressed to fire too eagerly.

## Regression Scope
- `tests/unit/world/test_transformations.py` — existing pure-function coverage, must stay green
  (not modified).
- `tests/integration/world/test_regional_sovereignty.py` — the real precedent this ticket's own test
  structurally follows, must stay green (not modified).
- `tests/simulation_quality/` (broader) — confirm no incidental regression.

## Out of Scope
- Idea 57: no test authored (real, disclosed blocker — see investigation.md).
- Any long emergent multi-tick corpus/calibration run — confirmed unnecessary during Investigate.
