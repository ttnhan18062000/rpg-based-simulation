---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE
phase: done
date: 2026-09-02
tags: [lifecycle, world]
---

# TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE

## Title
Close the population-pressure feedback loop — individual births nudge the aggregate cohort signal (idea 38)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Final child ticket (6 of 6) under the Reproduction epic (TCK-20260902-EPIC-RPG-M3-REPRODUCTION), covering idea 38 from `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md`. Today, `DemographicCycleService.process_demographics()` (`src/domains/demographics/cohort.py:324-419`) runs its own aggregate birth/death/migration logic every 200 ticks against `RegionState.population_cohorts`, feeding `RegionalPressureModel.evaluate()`'s `demand_multiplier = 1.0 + (density * 0.5)` (`src/domains/world_emergence/models.py:109`). Individual births produced by the three Reproduction-epic paths (natural-creature, magical/demonic, human/humanoid) do NOT increment this aggregate cohort count — a region flagged low-population by the pressure gate can stay flagged indefinitely regardless of real per-entity births. This ticket closes that gap with a deliberately coarse fix per the idea-38 atlas card: on a successful individual birth, nudge the birth region's `population_cohorts["young"].count` by +1 — never a full resync — keeping the aggregate cohort a background abstraction, not a real census. This ticket must land atomically with or immediately after the three birth-path tickets (TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH, TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH, TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE) — the epic's own acceptance constraint forbids exposing repeatable births before this loop can incorporate them.

## Scope
- On a successful individual birth from any of the three reproduction paths, nudge the birth region's `population_cohorts["young"].count` by +1 via the same authoritative merge path already used by `DemographicCycleService` and migration (`WorldUpdate` → `engine/apply_plan.py`) — never a direct mutation of frozen `RegionState`.
- The nudge is coarse and additive only — explicitly do not implement a full resync/recount of `population_cohorts` against actual named entities; this is an intentional, documented decoupling between the named-entity layer and the aggregate cohort layer (per the atlas card's revision-25 decision).
- Confirm which existing feature flag (if any) idea 32's reproduction paths are gated behind, and wire this nudge logic inside the same flag rather than introducing a separate one.
- Verify end-to-end: a region under population pressure (scarcity above `migration_threshold`) that receives real individual births via the Reproduction epic's paths shows its aggregate `population_cohorts` count increase and its pressure signal respond accordingly.

## Out of Scope
- Any change to `DemographicCycleService`'s own 200-tick aggregate birth/death/migration cycle — this ticket only adds an additive nudge on top of it, not a replacement.
- A full resync/recount mechanism between named entities and aggregate cohorts — explicitly rejected by the idea-38 card's own design.
- The three reproduction trigger paths themselves — those must already be landed (this ticket is the final one in the epic's build order).

## Acceptance Criteria
- [x] A successful individual birth (from any of the three reproduction paths) increments the birth region's `population_cohorts["young"].count` by exactly +1, via a typed `WorldUpdate` through the authoritative apply path.
- [x] No full resync/recount logic is introduced — the nudge is additive-only, verified by test (a birth changes the count by exactly 1, not to a recomputed total).
- [x] `RegionalPressureModel.evaluate()`'s `demand_multiplier` measurably responds to births via the pressure test pattern in `tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py::test_repeated_deaths_increase_danger_pressure` (mirrored for births).
- [x] A new integration-style test proves a region under population pressure receiving real births shows its aggregate signal move, following `tests/integration/scenarios/test_demographics.py::test_high_population_region_higher_resource_demand`'s pattern.
- [x] The reproduction paths' repeatable-births capability is not considered "shipped" (per the epic's own acceptance constraint) until this ticket lands — Finalize for the epic should confirm this ticket landed no later than atomically with the last of the three path tickets.
- [x] `docs/mechanics/05_world_evolution.md` documents the nudge mechanism explicitly as coarse/additive-only (not a resync); `docs/parity_ledger/world_dynamics.yaml` gains an entry (or updates `WORLD-DEMO-005`/`WORLD-DEMO-006`) citing it.

## Related Tickets
- TCK-20260902-EPIC-RPG-M3-REPRODUCTION (parent epic)
- TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH (hard dependency — must land first)
- TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH (hard dependency — must land first)
- TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE (hard dependency — must land first)
- TCK-20260831-POPULATION-COHORT-SEEDING (idea 43, DONE — the aggregate signal this loop closes)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md
- docs/brainstorm/rpg_feature_atlas.html (idea 38 card — coarse-nudge, not-a-resync decision, revision 25)
- docs/mechanics/05_world_evolution.md
- docs/parity_ledger/world_dynamics.yaml (WORLD-DEMO-005, WORLD-DEMO-006)

## Related Stored Artifacts
None.

## Related Code Areas
- src/domains/demographics/cohort.py
- src/domains/world_emergence/models.py
- src/worldbuilding/compiler.py
- src/core/state.py

## Assumptions / Open Questions
- This ticket is the final one in the Reproduction epic's build order — it must not land before at least the three birth-path tickets are done, since it has nothing real to hook into otherwise.
- Whether magical/demonic-path births participate in this nudge at all is inherited from the open question flagged in TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH.

## Implementation Notes

Implemented all 12 plan steps as specified, with one citation-only correction (see
Deviations in `staging_artifacts/.../plan.md`): Step 3's precedent citation was corrected
from `src/domains/demographics/cohort.py`'s migration "new bracket in target" branch (which
actually copies the source cohort's own rates via `replace()`, not dataclass defaults) to
`src/worldbuilding/compiler.py`'s `_seed_population_cohorts()`, whose own docstring
confirms dataclass-default behavior. This did not change any implemented behavior — the
plan's specified `PopulationCohort(bracket="young", count=delta)` with dataclass defaults
was already correct; only the code comment's citation changed.

1. `WorldUpdate.population_young_births_delta: int = 0` added to `src/core/updates.py`,
   summed additively in `merge()` alongside the existing delta fields.
2. Fixed the pre-existing bug in `WorldDynamicsSystem.resolve_dynamics()`
   (`src/engine/world_dynamics.py`) that silently dropped `camp_state_update.world_updates`/
   `calamity_update.world_updates` — both are now folded into `update.world_updates` via the
   same per-region merge-or-set idiom already used for `ThreatService`, applied after the
   `update.replace(...)` call that handles those two services' other fields.
3. `src/engine/apply_plan.py` layers `population_young_births_delta` onto the `young`
   bracket strictly after `population_cohorts_set` is resolved, so a same-tick
   `DemographicCycleService` rebuild becomes the base and the nudge adds on top without
   clobbering it. Materializes a fresh `PopulationCohort(bracket="young", count=delta)`
   with dataclass defaults when the bracket is absent.
4. `src/world/camp.py` block 4 (natural-creature path): accumulates the nudge in a local
   `world_updates` dict across camps in the same `process_camps()` call, merging (not
   overwriting) when two camps in the same region both birth on the same tick. Skipped when
   `region is None`.
5. `src/world/reproduction_humanoid.py`: nudge added to `pair_update`'s `world_updates`;
   accumulates for free through the function's existing `result.merge(pair_update)` loop.
   Skipped when `region is None`.
6. `src/world/calamity.py`: no behavior change to the magical/demonic branch. Added a
   comment above it citing `WORLD-121`'s already-shipped rationale for the confirmed
   exclusion, plus a hard regression-guard test.
7. Retargeted the three existing `does_not_write_population_cohorts` guard tests (renamed,
   not deleted) to assert the new additive `+1` behavior, per Step 7. The humanoid guard
   test was split into two: one for the "no region resolved" skip case (kept, renamed) and
   one new test for the actual nudge.
8. Added `test_repeated_births_increase_population_density_signal` to
   `test_phase8_regional_pressure_model.py`, using a 1x1-unit region fixture (not the
   `count=2000`/`100x100` integration-test scale) so a single +1 nudge produces a
   measurable `demand_multiplier`/resource-intensity delta.
9. Added `test_population_pressure_region_responds_to_real_births` to
   `test_demographics.py`, driving the humanoid path end-to-end through
   `WorldDynamicsSystem.resolve_dynamics()` + `ApplyPath.apply_generation()` (real
   authoritative apply path), also using a 1x1-unit region for the same reason. Had to
   filter the resulting new entities by `lifecycle.parent_a_entity_id == 1` rather than "any
   id not in (1, 2)", since `cadence.world_dynamics=1` also fires `SpawnService`'s ordinary
   monster replenishment in the same call.
10. Added `test_world_dynamics_folds_camp_and_calamity_world_updates_into_final_update`
    (`test_world_dynamics.py`) as the Step-2 regression guard, and
    `test_reproduction_paths_never_mutate_region_directly`
    (`test_natural_creature_reproduction.py`) as a source-inspection architecture guard
    across all three `process_*` methods.
11. Updated `docs/mechanics/05_world_evolution.md`: corrected the three now-false "never
    writes population_cohorts" sentences (natural-creature, magical/demonic, humanoid
    subsections under §6), and added a new "Individual-Birth Population-Pressure Nudge"
    subsection under §5 documenting the mechanism, participating paths, and the confirmed
    magical/demonic exclusion.
12. Updated `docs/parity_ledger/world_dynamics.yaml` via `tools/parity_ledger_writer.py`
    (never a raw edit): corrected `WORLD-120`/`WORLD-122`'s text/v2_evidence/test_path;
    appended a confirmation addendum to `WORLD-121`; added new entry `WORLD-123` (computed
    via `next_available_id()`, priority P1) documenting the nudge mechanism itself, with
    `test_path` citing the Step 8/9/10 tests. `tests/tools/test_parity_updater_static.py`'s
    hardcoded `next_available_id`-against-real-shard baseline was updated from `WORLD-123`
    to `WORLD-124` (documented drift pattern, same as the humanoid ticket's own precedent).
    `tools/parity_index.py build` was re-run afterward to keep the derived index fresh.

Full regression pass: `tests/unit/` (5003 passed, 3 skipped) and `tests/integration/`
(944 passed, 6 skipped) both green except one pre-existing, unrelated failure —
`tests/integration/world/test_long_run_stability.py::test_long_run_stability`
(`@pytest.mark.extra_slow`) hit a wall-clock resource-time-limit timeout. This test is not
gated by `-m "not slow"` (its own mark is `extra_slow`), does not exercise any
`ENABLE_REPRODUCTION_*` flag (all OFF by default in its fixture), and is documented in
`docs/testing/regression_policy.md` as "long-running; infrastructure-sensitive; failures are
investigated but don't block fast iteration" — consistent with the project's own known,
already-flagged wall-clock mid-tick-throttle determinism issue in `kernel.py`, not a
regression introduced by this ticket.

## Test Summary

New/retargeted tests, all passing:
- `tests/unit/world/test_natural_creature_reproduction.py`: retargeted
  `test_natural_creature_birth_nudges_young_cohort_by_one`; new
  `test_two_simultaneous_births_same_region_same_call_both_nudge`,
  `test_birth_nudge_does_not_recompute_other_brackets`,
  `test_birth_in_region_missing_young_cohort`,
  `test_reproduction_paths_never_mutate_region_directly`.
- `tests/unit/world/test_calamity_magical_demonic_reproduction.py`: retargeted
  `test_magical_demonic_birth_nudge_decision`.
- `tests/unit/world/test_reproduction_humanoid_cadence.py`: retargeted
  `test_no_population_cohorts_write_when_birth_region_unresolved`; new
  `test_humanoid_birth_nudges_young_cohort_by_one`.
- `tests/unit/world/test_world_dynamics.py`: new
  `test_world_dynamics_folds_camp_and_calamity_world_updates_into_final_update`.
- `tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py`: new
  `test_repeated_births_increase_population_density_signal`.
- `tests/integration/scenarios/test_demographics.py`: new
  `test_population_pressure_region_responds_to_real_births`.
- `tests/tools/test_parity_updater_static.py`: updated hardcoded baseline
  (`test_next_available_id_against_real_world_dynamics_shard`).

Commands run: targeted files (52 passed), `tests/integration/scenarios/test_demographics.py`
(7 passed), the Step-2 regression surface (`test_camp_lifecycle.py`, `test_calamity_raid.py`,
`test_calamity_pressure_propagator.py`, `test_creature_territory_lifecycle.py`,
`test_spawn_cadence.py`, `test_system_cadence.py`, `test_demographics.py` — 106 passed),
parity tooling tests (100 passed), full `tests/unit -m "not slow"` (5003 passed, 3 skipped),
full `tests/integration -m "not slow"` (944 passed, 6 skipped, 1 pre-existing unrelated
`extra_slow` timeout — see Implementation Notes).

## Files Changed

Code:
- `src/core/updates.py`
- `src/engine/world_dynamics.py`
- `src/engine/apply_plan.py`
- `src/world/camp.py`
- `src/world/reproduction_humanoid.py`
- `src/world/calamity.py`

Tests:
- `tests/unit/world/test_natural_creature_reproduction.py`
- `tests/unit/world/test_calamity_magical_demonic_reproduction.py`
- `tests/unit/world/test_reproduction_humanoid_cadence.py`
- `tests/unit/world/test_world_dynamics.py`
- `tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py`
- `tests/integration/scenarios/test_demographics.py`
- `tests/tools/test_parity_updater_static.py` (hardcoded baseline drift, documented pattern)

Docs / parity:
- `docs/mechanics/05_world_evolution.md`
- `docs/parity_ledger/world_dynamics.yaml`
- `docs/parity_ledger/faction.yaml` (Parity-phase fix: `FAC-009`'s `v2_evidence` line citation for
  `apply_plan.py`'s siege-mechanics clamp block drifted from `125-140` to `137-152` because this
  ticket's new population-nudge block was inserted immediately above it in the same region-apply
  loop; corrected the citation, no behavioral change to the underlying claim)

Ticket / staging artifacts (pre-existing from Investigate/Plan phases of this same pipeline
run, not authored by this Implement step, but part of this run's real changeset):
- `tickets/inprogress/TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE.md`
- `staging_artifacts/TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE/investigation.md`
- `staging_artifacts/TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE/plan.md`
  (Deviations section added by this Implement step)
- `staging_artifacts/TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE/test_plan.md`

## Completion Summary

Closed the individual-birth to aggregate-cohort population-pressure feedback loop (idea 38):
added a new additive `WorldUpdate.population_young_births_delta` field, wired a `+1` nudge
into the natural-creature and humanoid reproduction paths' own already-flag-gated branches,
applied it in `apply_plan.py` strictly after `population_cohorts_set` resolution (never a
resync), and confirmed the magical/demonic path's exclusion with a regression-guard test. Two
pre-existing bugs were fixed as prerequisite plumbing: `WorldDynamicsSystem.resolve_dynamics()`
was silently dropping `camp_state_update.world_updates`/`calamity_update.world_updates`, and
the missing-`young`-bracket case now materializes a fresh cohort with dataclass defaults
instead of silently dropping the signal. Mechanics Bible and parity ledger were both updated
in-session to reflect the new behavior, and all six acceptance criteria are satisfied with
passing tests, with no regressions found in the full unit/integration suites beyond one
pre-existing, unrelated, environment-flagged `extra_slow` timeout.
