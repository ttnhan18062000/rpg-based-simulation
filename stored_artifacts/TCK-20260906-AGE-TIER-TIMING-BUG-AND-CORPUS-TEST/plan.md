---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST
date: 2026-09-06
---

# Plan: TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST

## Steps

1. **Tooling guard, not a huge default bump** — `tools/simq_long_run_observation.py`: add a
   post-parse check that warns (stderr, non-fatal) whenever `--ticks` cannot reach
   `ADULT_ELDER_BOUNDARY_TICKS` (17,280,000), naming both real thresholds and the actual gap, so a
   future silent no-observation run is caught rather than repeated. Leave the `--ticks` default at
   `5000` (a full-scale default bump is impractical — see investigation.md) but make the shortfall
   explicit every time the tool runs with an inadequate value (which is every current call site,
   including its own default). File: `tools/simq_long_run_observation.py`.
2. **New Unit-tier SimQ corpus test** — `tests/simulation_quality/test_age_tier_transitions_corpus.py`
   (new file). A small, hand-seeded, synthetic-content `AuthoritativeState` (Unit tier explicitly
   allows synthetic content per `corpus_tier_taxonomy.md`) with 2 entities: one placed at
   `age_ticks = YOUNG_ADULT_BOUNDARY_TICKS - 1` (child, about to transition) and one at
   `age_ticks = ADULT_ELDER_BOUNDARY_TICKS - 1` (adult, about to transition to elder), both
   `EntityRole.CITIZEN`. Run a real `Kernel.tick_once()` and assert: (a) entity 1's
   `identity.life_stage` flips CHILD->ADULT and its `identity.role` changes via a real `role_set`
   from the Coming-of-Age roll (idea 34's real mechanism, not a fabricated `archetype_locked`
   field); (b) entity 2's `identity.life_stage` flips ADULT->ELDER and its attributes change per
   `compute_elder_attribute_update()`'s real deltas.
3. **Doc update** — mark the roadmap doc's own open finding as addressed by this ticket, citing the
   corrected framing from investigation.md.
4. **Ticket text** — this ticket's own body should record the `archetype_locked` correction, the
   duplicate-ownership check, and the already-resolved `LifeStage`/`get_age_bracket()` question in
   its own Implementation Notes/Completion Summary, not silently.

## Files to change
- `tools/simq_long_run_observation.py` (guard added)
- `tests/simulation_quality/test_age_tier_transitions_corpus.py` (new)
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (note addressed)
- `tickets/todos/m9-corpus-test-coverage/TCK-20260906-AGE-TIER-TIMING-BUG-AND-CORPUS-TEST.md` ->
  `tickets/done/`

## Scope Guards
- Do not touch `src/domains/demographics/cohort.py`, `src/ai/life_stage.py`, or
  `src/ai/coming_of_age.py` — all 3 mechanisms are already correct; this ticket is tooling + tests
  only.
- Do not raise the tool's default anywhere near the real elder threshold.
- Do not invent a new `archetype_locked` field on any state class.

## Dependency Map
Step 1 and Step 2 are independent of each other; Step 3/4 depend on both being done so the doc
update accurately reflects the real change.

## Acceptance Criteria Map
- AC1 (tooling guard) -> Step 1
- AC2 (real corpus test observing both transitions) -> Step 2
- AC3 (LifeStage/get_age_bracket resolution) -> already resolved, cited in investigation.md
  Correction 4 and this ticket's own Implementation Notes — no code step needed.

## Unresolved Questions
None.
