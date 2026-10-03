---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS
date: 2026-09-06
---

# Plan: TCK-20260906-STRESS-TIER-LONG-RUN-CORPUS-TESTS

## Scope Guard
- New file only: `tests/simulation_quality/test_region_transformation_pipeline_corpus.py`.
- No production code change (`behavior_changed=false`).
- No corpus world/registry/profile change.
- Idea 57: no test file, deferral documented in this ticket's own Implementation Notes only (the
  gap is already cross-referenced elsewhere in the M9 epic's own docs from earlier scoping work).

## Steps
1. Write `test_region_transformation_pipeline_corpus.py`:
   - `test_forest_region_transforms_to_burnt_forest_through_real_pipeline_after_a_combat_death`:
     hand-seed `AuthoritativeState` with one `RegionState(kind="FOREST", trauma_score=49.0)` and one
     living entity positioned inside it. Construct a `StateUpdate` marking that entity's combat death
     (`CombatUpdate(outcome_kind="KILL", hp_delta=-20, alive_set=False)`), matching
     `test_regional_sovereignty.py`'s own real precedent. Run through
     `AuthoritativeApplyPipeline.refine()` then `ApplyPath.apply_generation()`. Assert
     `next_state.regions[...].kind == "BURNT_FOREST"`.
   - Same test (or a second one) asserts `region_transformed` appears in
     `EventExtractor.extract(prior_state, next_state, refined_update)`'s output with
     `payload["new_kind"] == "BURNT_FOREST"`. If `EventExtractor.extract()` alone does not surface it
     under default flags (push-shaper phase 2 may be the live default path instead), call whichever
     real live path actually fires by default — confirm empirically, do not guess.
   - `test_no_transformation_below_the_real_threshold_through_the_same_real_pipeline` (regression
     tolerance floor): same setup at `trauma_score=30.0` (well under 50), confirm the region's kind
     is unchanged and no `region_transformed` event fires — a real negative-path assertion, not a
     tautology.
   - Module-level docstring documents: (a) the idea-48 CITY/RUIN->FOREST/terrain correction with
     citations, (b) why the SOCIAL/GUILD-drop caveat from the original ticket text does not apply to
     this single-tick deterministic design, (c) idea 57's deferral and where its gap is tracked.
2. Run the new test file; confirm both pass.
3. Document-Update: none needed (no docs/ touched).
4. Architecture-Verify: confirm no `src/` file touched (trivially satisfied — test-only ticket).
5. Test: run `tests/simulation_quality/`, `tests/unit/world/test_transformations.py`,
   `tests/integration/world/test_regional_sovereignty.py` together — confirm no regression.
6. Parity: no entry needed, `behavior_changed=false`, no `src/` path in `files_changed`.
7. Verify: done-checker per standard tier.
8. Finalize: move ticket to `tickets/done/`, migrate staging artifacts, append working_log.csv
   (surgical single-row), regenerate REGISTRY.yaml only if a docs/ file changed (it won't).

## Acceptance-Criteria Map
- AC1 (idea 48 test authored+passing, SOCIAL/GUILD caveat documented) -> step 1 (docstring) + step 2.
- AC2 (idea 57 deferred with written reason) -> this plan's own Idea-57 scope line + ticket's own
  Implementation Notes at Finalize.
