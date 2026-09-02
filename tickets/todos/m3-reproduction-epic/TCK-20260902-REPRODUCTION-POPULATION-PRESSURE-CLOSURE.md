---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE
phase: open
date: 2026-09-02
tags: [lifecycle, world]
---

# TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE

## Title
Close the population-pressure feedback loop — individual births nudge the aggregate cohort signal (idea 38)

## Status
OPEN

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
- [ ] A successful individual birth (from any of the three reproduction paths) increments the birth region's `population_cohorts["young"].count` by exactly +1, via a typed `WorldUpdate` through the authoritative apply path.
- [ ] No full resync/recount logic is introduced — the nudge is additive-only, verified by test (a birth changes the count by exactly 1, not to a recomputed total).
- [ ] `RegionalPressureModel.evaluate()`'s `demand_multiplier` measurably responds to births via the pressure test pattern in `tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py::test_repeated_deaths_increase_danger_pressure` (mirrored for births).
- [ ] A new integration-style test proves a region under population pressure receiving real births shows its aggregate signal move, following `tests/integration/scenarios/test_demographics.py::test_high_population_region_higher_resource_demand`'s pattern.
- [ ] The reproduction paths' repeatable-births capability is not considered "shipped" (per the epic's own acceptance constraint) until this ticket lands — Finalize for the epic should confirm this ticket landed no later than atomically with the last of the three path tickets.
- [ ] `docs/mechanics/05_world_evolution.md` documents the nudge mechanism explicitly as coarse/additive-only (not a resync); `docs/parity_ledger/world_dynamics.yaml` gains an entry (or updates `WORLD-DEMO-005`/`WORLD-DEMO-006`) citing it.

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

## Test Summary

## Files Changed

## Completion Summary
