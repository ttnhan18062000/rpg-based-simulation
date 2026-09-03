---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE
phase: done
date: 2026-09-02
tags: [lifecycle, strategy]
---

# TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE

## Title
Coming of Age — weighted archetype-choice roll at CHILD to ADULT transition, with a required convergence-guard metamorphic test

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Covers idea 34 (Coming of Age) from `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md`. Both M1 prerequisites are DONE: `TCK-20260824-LIFE-STAGE-TRANSITIONS` (idea 20) gives the CHILD→ADULT transition trigger inside `LifecycleSystem.resolve_lifecycle()` (`src/systems/lifecycle_systems/lifecycle.py`), and `TCK-20260824-OCCUPATION-CHANGE-TRIGGER` (idea 21) gives the first live `role_set` producer (`src/ai/goals/occupation_change_scorer.py`). The remaining unbuilt piece is a genuinely new weighted archetype-choice mechanism (personality + parental occupation + regional-need weighting) with zero existing numeric precedent — the closest analog, `PersonalityService.get_goal_modifiers()` (`src/ai/personality.py`), governs goal-utility, not occupation selection. CRITICAL RISK: today's only real occupation-selection precedent, `OccupationChangeGoalScorer` (`src/ai/goals/occupation_change_scorer.py`), is fully deterministic and zero-variance by construction (fixed-priority first-fit: `_CANDIDATE_ROLES = (SHOPKEEPER, WORKER, GUARD)`, first role passing an open-slot check plus a flat `attribute >= 5` threshold wins, no weighting or randomness). If this ticket naively reuses that pattern, it will reproduce the exact convergence bug the design proposal itself names — a metamorphic test proving that increasing the regional-need weight increases (not collapses) outcome variance is a required acceptance gate, not optional coverage. Has a hard dependency on the Reproduction epic's birth-record schema (TCK-20260902-EPIC-RPG-M3-REPRODUCTION / TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA) for one acceptance criterion (the no-birth-record hard exclusion) — that criterion is BLOCKED until the epic's schema child ticket lands; do not silently skip it, mark it explicitly deferred.

## Scope
- When an entity's `identity.life_stage` transitions CHILD→ADULT inside `LifecycleSystem.resolve_lifecycle()` (the same call site/tick-phase as the existing `life_stage_set` trigger, per the atlas's cross-reference note that idea 34 must fire in the same phase window as idea 20's transition), fire a Coming of Age archetype-choice roll exactly once for that entity.
- The roll produces exactly one `IdentityUpdate` (via the authoritative `IdentityPatch`/`role_set` path, not direct state mutation) assigning an occupation/archetype.
- Design a genuinely weighted (not fixed-priority, not deterministic) selection mechanism combining personality traits, parental occupation, and regional-need signals — the exact weighting formula (e.g. softmax over weighted scores vs. weighted-random draw) is a fresh Plan-phase design decision; do not copy `OccupationChangeGoalScorer`'s fixed-priority-first-fit pattern, since doing so would collapse variance to zero by construction.
- A required metamorphic test: holding personality and parental-occupation weight terms fixed, increasing the regional-need weight coefficient must strictly increase the variance/entropy of the resulting occupation distribution across a same-tick batch of same-region children reaching adulthood — never collapse it to a single occupation.
- A regression guard: a batch of N children in the same region under the same regional shortage, all transitioning CHILD→ADULT in the same tick, must not all resolve to the identical occupation role when regional-need weight is nonzero.
- The no-birth-record hard boolean exclusion (Coming of Age does not fire for an entity with no birth record) is explicitly BLOCKED pending the Reproduction epic's birth-record schema landing — implement the eligibility check as a stub/TODO with this dependency documented, or defer this specific AC to a fast-follow ticket once the schema exists; do not silently omit it from the ticket's tracking.

## Out of Scope
- Any change to `OccupationChangeGoalScorer`'s existing deterministic regional-need/target_count logic — this ticket may read its `BASE_OCCUPATION_DENSITY`/target_count constants (`src/world/occupation_config.py`) for regional-need signal input, but must not modify that scorer's own selection behavior.
- The Reproduction epic itself (idea 32) — a separate epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION); this ticket only consumes its birth-record schema once available.
- Long-run corpus-tier population-pressure convergence (idea 38's separate claim) — the metamorphic AC here is scoped to a bounded single-tick synthetic batch, not the long-run corpus property.

## Acceptance Criteria
- [x] When `identity.life_stage` transitions CHILD→ADULT inside `LifecycleSystem.resolve_lifecycle()`, a Coming of Age roll fires exactly once and commits exactly one `IdentityUpdate` through the authoritative `IdentityPatch`/`role_set` path, and only for `entity.identity.role == EntityRole.CITIZEN` (the intended citizen population, added per architecture-review Decision 5).
- [x] A metamorphic test asserts: holding personality and parental-occupation weight terms fixed, increasing the regional-need weight coefficient strictly increases the variance/entropy of the resulting occupation distribution across a same-tick batch of same-region children reaching adulthood.
- [x] A batch of N children in the same region under the same regional shortage, transitioning CHILD→ADULT in the same tick, do not all resolve to the identical occupation role when regional-need weight is nonzero (direct regression guard).
- [x] The no-birth-record hard exclusion is implemented (not merely tracked as BLOCKED): the Reproduction epic dependency landed (all six child tickets DONE under `tickets/done/m3-reproduction-epic/`) before this ticket reached Implement, so `is_excluded_no_birth_record()` uses the investigation's proven-safe compound check (`birth_tick==0 AND parent_a_entity_id is None AND parent_b_entity_id is None`) rather than deferring — a valid path explicitly offered by this AC's own original wording ("...implement the eligibility check...**or** defer").
- [x] New unit tests added following `tests/unit/strategic/test_occupation_change_scorer.py` and `tests/unit/strategic/test_life_stage_transitions.py`'s conventions; the metamorphic/convergence test is a genuinely new test class (`TestComingOfAgeMetamorphicConvergenceGuard`, none existed before for weighted/stochastic archetype selection).
- [x] `docs/mechanics/04_strategic_cognition.md` §9 documents the weighting mechanism and the convergence-risk guard; `docs/parity_ledger/strategic_cognition.yaml` entry `STRAT-267` references it.

## Related Tickets
- TCK-20260824-LIFE-STAGE-TRANSITIONS (DONE — idea 20, the life-stage write path this concern co-locates with)
- TCK-20260824-OCCUPATION-CHANGE-TRIGGER (DONE — idea 21, the first live `role_set` producer this extends)
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION / TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA (hard dependency for the no-birth-record exclusion AC — BLOCKED until this lands)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md (build-order item 4 of 5, explicit metamorphic-check acceptance gate)
- docs/brainstorm/rpg_feature_atlas.html (idea 34 card)
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/lifecycle_systems/lifecycle.py
- src/ai/life_stage.py
- src/ai/goals/occupation_change_scorer.py
- src/world/occupation_config.py
- src/ai/personality.py
- src/core/state.py
- src/core/updates.py

## Assumptions / Open Questions
- The weighting-mechanism design (softmax vs. weighted-random draw, etc.) has no existing precedent and is a fresh Plan-phase decision.
- Whether to call `OccupationChangeGoalScorer`'s regional-count logic directly or duplicate/extend `BASE_OCCUPATION_DENSITY` is an open design question — duplicating risks drift between the two systems.
- The no-birth-record exclusion AC is untestable until the Reproduction epic's schema lands; Plan should decide whether to stub it now or split it into a fast-follow ticket once that schema exists.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE/plan.md`'s
6 steps (including the revised Step 4 role gate / Decision 5, and the new test 10), with no
structural deviations. Details:

1. **New module `src/ai/coming_of_age.py`** — free functions (not a `ComingOfAgeService` wrapper
   class): `compute_role_weights()` (pure, coefficient-parameterized: `personality_coeff`,
   `parental_coeff`, `regional_coeff` keyword overrides), `_personality_weight()`,
   `_parental_weight()`, `_regional_need_weight()`, `is_excluded_no_birth_record()`, and
   `choose_archetype()`. Chose plain functions over a thin staticmethod wrapper class (the plan
   explicitly left this to implementer's judgment) since the module has no shared instance state
   to justify the extra indirection — matches the "no unnecessary abstractions" rule more directly
   than mirroring `LifeStageService`'s class-wrapper style would have.
2. **AC4 (no-birth-record exclusion) — UNBLOCKED and implemented in this pass.** The ticket's own
   Request Summary/AC4 text describes this as BLOCKED pending the Reproduction epic. That epic
   (`TCK-20260902-EPIC-RPG-M3-REPRODUCTION`) is now DONE (all six child tickets under
   `tickets/done/m3-reproduction-epic/`), confirmed during investigation, so `is_excluded_no_birth_record()`
   uses the investigation's proven-safe compound check
   (`birth_tick==0 AND parent_a_entity_id is None AND parent_b_entity_id is None`), not the unsafe
   `birth_tick==0`-only shortcut (unsafe because `HumanoidReproductionService.process_reproduction()`
   has no explicit `tick>0` guard, so a real tick-0 Humanoid birth can have non-`None` parent ids).
   This is implementing AC4 as originally written, not exceeding scope: the AC's own text offers
   "implement the eligibility check... **or** defer" as the two valid paths once the dependency
   lands.
3. **`choose_archetype()`** constructs `DeterministicRNG(state.seed)` locally (the established
   pattern for `resolve_lifecycle()`-adjacent code, since no RNG instance is threaded through the
   refinement pipeline) and calls `weighted_choice(Domain.STRATEGIC, state.tick, entity.id,
   list(_CANDIDATE_ROLES), weights)` — never Python's unseeded `random` module, never a
   fixed-priority first-fit.
4. **`src/systems/lifecycle_systems/lifecycle.py` wiring** — added a sibling `if` block
   immediately after the ELDER branch, before `refined_entity_updates[e_id] = ent_upd`. **Role
   gate (Decision 5, load-bearing):** the branch condition is
   `target_stage == LifeStage.ADULT and entity.identity.life_stage == LifeStage.CHILD and
   entity.identity.role == EntityRole.CITIZEN` — the third clause is required and was added per
   architecture review (2026-09-02 revision): without it, a MONSTER-role CHILD from
   `spawn_natural_creature_offspring()` (parentless but with a real nonzero `birth_tick`, so
   `is_excluded_no_birth_record()` alone does NOT exclude it) would have its `role_set` incorrectly
   overwritten to a citizen occupation, producing an incoherent `MONSTER_HORDE`-faction entity.
   Added `from src.core.enums import EntityRole` and
   `from src.ai.coming_of_age import choose_archetype, is_excluded_no_birth_record` imports; no
   other lines in `resolve_lifecycle()` were touched.
5. **New test file `tests/unit/strategic/test_coming_of_age_archetype_choice.py`** — pure-function
   metamorphic test (`TestComingOfAgeMetamorphicConvergenceGuard.
   test_coming_of_age_metamorphic_regional_need_weight_increases_variance`, AC2), same-tick
   no-collapse batch test (`...test_coming_of_age_same_tick_batch_does_not_collapse_to_identical_occupation`,
   AC3), parent-resolution edge-case tests (missing/inactive parent, parentless-neutral), and the
   seeded-RNG determinism + no-unseeded-random architecture guard. Added tests 1, 2, 3, 6, and 10
   (including the new role-gate regression test
   `test_coming_of_age_monster_role_child_role_untouched_on_transition`) to
   `tests/unit/progression/test_lifecycle.py` beside the existing CHILD→ADULT fixture coverage.
6. **Docs** — new `docs/mechanics/04_strategic_cognition.md` §9 (Gate/Direction/Durable
   record/Out-of-scope/Source format matching §8's template) and a new
   `docs/parity_ledger/strategic_cognition.yaml` entry `STRAT-267` (`status: verified`,
   `priority: P1`), written via `tools/parity_ledger_writer.py`'s schema-validating `write_entry()`
   (next available ID after `STRAT-266`, confirmed at implementation time). `tools/parity_index.py
   build` was run afterward as a second, visible index-rebuild step per the writer module's own
   documented convention. `graphify update .` and `make knowledge-index-update` were run after all
   `src/`/`tests/`/`docs/` edits.

No deviations from `plan.md` were required — see `staging_artifacts/.../plan.md` (no new
"Deviations" section was added since none of the plan's Anti-Drift Notes, Scope Guards, or Step
specifics needed to change during implementation).

## Test Summary

Scoped regression run (per `test_plan.md`'s "Scoped Pytest Commands", via
`/home/u24desktop/Working/venv/bin/python3 -m pytest`, since the repo's tracked `.venv` lacks
`pydantic`):

- `tests/unit/progression/test_lifecycle.py tests/unit/strategic/test_life_stage_transitions.py tests/unit/strategic/test_occupation_change_scorer.py tests/unit/strategic/test_coming_of_age_archetype_choice.py` — 53 passed.
- `tests/integration/strategic/test_occupation_change_reachability.py tests/integration/optimization/test_component_patch_apply_parity.py tests/integration/optimization/test_apply_plan_parity.py` — 11 passed.
- `tests/unit/world/test_demographics.py -k "LifecycleSystemElderWiring"` — 2 passed.

All 10 planned new tests (1-10) implemented and passing, plus the pre-existing anti-drift/regression
suite for `OccupationChangeGoalScorer`, `LifeStageService`, apply-path parity, and the ELDER-branch
sibling precedent confirmed unaffected.

## Files Changed

- `src/ai/coming_of_age.py` (new)
- `src/systems/lifecycle_systems/lifecycle.py`
- `tests/unit/strategic/test_coming_of_age_archetype_choice.py` (new)
- `tests/unit/progression/test_lifecycle.py`
- `docs/mechanics/04_strategic_cognition.md`
- `docs/parity_ledger/strategic_cognition.yaml`
- `tests/architecture/test_role_set_identity_patch_only_guard.py` (updated during Parity — this ticket's `replace(ent_upd.identity, role_set=...)` mutation in `lifecycle.py` was a real second, twice-architecture-reviewed-and-approved producer of `role_set` that the guard's regex/allowlist didn't recognize; broadened both to correctly detect and sanction it rather than leave the guard blind to it)
- `staging_artifacts/TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE/investigation.md` (new — created during this run's Investigate phase)
- `staging_artifacts/TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE/plan.md` (new — created during this run's Plan phase, including the post-review Decision 5 revision; reviewed for further deviations during Implement, none required)
- `staging_artifacts/TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE/test_plan.md` (new — created during this run's Plan/test-scoping phase)
- `tickets/inprogress/TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE.md` (this file)

(`graphify-out/` and the knowledge-search index were also regenerated via `graphify update .` and
`make knowledge-index-update`, but both are gitignored and not part of the tracked changeset.)

## Completion Summary

Implemented the Coming of Age archetype-choice roll (idea 34): a new `src/ai/coming_of_age.py`
module computes a genuinely weighted (personality + parental-occupation + regional-need)
distribution over `{SHOPKEEPER, WORKER, GUARD}` and draws from it via the project's seeded
`DeterministicRNG.weighted_choice()`, wired into `LifecycleSystem.resolve_lifecycle()` as a
sibling branch to the existing ELDER transition, firing exactly once at the CITIZEN CHILD→ADULT
transition. The no-birth-record exclusion (AC4) was implemented now rather than deferred, since
the Reproduction epic dependency landed before this ticket reached Implement. A critical role gate
(`entity.identity.role == EntityRole.CITIZEN`), added during architecture review, prevents the
mechanism from incorrectly overwriting `role_set` on MONSTER-role Natural-Creature offspring. All
required tests (metamorphic convergence guard, no-collapse batch regression, parent-resolution
edge cases, seeded-RNG determinism, and the new role-gate regression test) pass, and the Mechanics
Bible (`04_strategic_cognition.md` §9) and parity ledger (`STRAT-267`) were updated.
