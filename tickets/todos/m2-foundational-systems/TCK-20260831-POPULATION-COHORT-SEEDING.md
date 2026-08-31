---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260831-POPULATION-COHORT-SEEDING
phase: open
date: 2026-08-31
tags: [world]
---

# TCK-20260831-POPULATION-COHORT-SEEDING

## Title
Seed population_cohorts at world-compile time

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
This is the highest-leverage item in M2, cited by 5 later ideas (32, 38, 43, 65), and also the highest-uncertainty item in the whole 65-idea roadmap — the guard it activates has never fired against real data. WorldCompiler.compile() never passes population_cohorts= when constructing RegionState, so DemographicCycleService's real, unit-tested birth/death/migration logic — wired live into the tick pipeline every 200 ticks — has literally never run against compiler-produced data; every existing test hand-constructs RegionState bypassing the compiler.

## Scope
- Modify WorldCompiler.compile() (src/worldbuilding/compiler.py:245-254) to pass population_cohorts= when constructing RegionState, using direct constructor assignment (the same precedent already used for influence and owner_faction_id), not the tick-time WorldUpdate.population_cohorts_set merge path.
- Author and explicitly document a fixed young/adult/elder distribution ratio (no existing anchor in code or docs anywhere) to seed cohort counts from a region's declared population, against today's real age-bracket boundaries (`<3000`/`<7000`/`≥7000` ticks) — do not silently assume these tick values are permanent (see Temporal-axis caution below).
- If constructing PopulationCohort instances requires setting `birth_rate`/`mortality_rate` (rather than relying on their existing dataclass defaults untouched), explicitly state in Implementation Notes what real-world meaning (if any) is intended for the seeded values — do not let a compile-time seed value quietly imply a fantasy-calendar meaning nobody has decided (see Temporal-axis caution below). If defaults are left untouched, say so explicitly instead of leaving it implicit.
- Verify DemographicCycleService.process_demographics() proceeds past the `if not region.population_cohorts: continue` guard (src/domains/demographics/cohort.py:349) on compiler-produced state at tick=200.
- Preserve determinism: compiling the same WorldSpec+seed twice must produce byte-identical population_cohorts.
- Ensure a region with zero PopulationSpec entries still compiles without crashing and the guard correctly no-ops.

## Out of Scope
- entity age_ticks always defaulting to 0 because the compiler's builder chain never calls .lifecycle(age_ticks=...) — a separate atlas finding, not part of this ticket.
- Downstream consumers of population_cohorts (ideas 32, 38, 65) — this ticket only seeds the field.
- Actually migrating age representation to fantasy-year units, or redefining birth_rate/mortality_rate to a calendar-independent unit (e.g. births/year) — both are accepted-but-not-yet-implemented future decisions per `TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`, owned by a dedicated future calendar-migration ticket, not this one. This ticket only needs to avoid quietly baking in an assumption about either — documenting the gap is sufficient, resolving it is not required here.

## Acceptance Criteria
- [ ] After WorldCompiler.compile() on a WorldSpec with a PopulationSpec targeting a region, RegionState.population_cohorts is non-empty (young/adult/elder keys) with counts summing to the region's declared population per a documented, explicitly-authored fixed distribution ratio.
- [ ] Calling DemographicCycleService.process_demographics on a compiler-produced (not hand-built) AuthoritativeState at tick=200 proceeds past the guard and returns a real StateUpdate.
- [ ] Compiling the same WorldSpec+seed twice produces byte-identical population_cohorts (determinism preserved).
- [ ] A region with zero PopulationSpec entries still compiles without crashing and the guard correctly no-ops.
- [ ] Implementation Notes explicitly states whether seeded PopulationCohort instances leave `birth_rate`/`mortality_rate` at their existing per-200-tick-cycle defaults untouched, or set new values — either way, the real-world (calendar) meaning intended is stated explicitly, not left implicit, per the cadence-duration-conflation finding below.

## Related Tickets
- TCK-20260619-E52A-COHORT-MODEL
- TCK-20260619-E52B-MIGRATION
- TCK-20260619-E52C-AGE-ADVANCEMENT
- TCK-20260619-E52D-DENSITY-SIGNAL
- TCK-20260523-WORLD-COMPILER
- TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY

## Related Docs
- docs/brainstorm/rpg_expected_schemas.html
- docs/plans/rpg_design_roadmap/rpg_m2_foundational_systems_epic.md (Temporal-axis caution + cadence-coupled rate finding on idea 43, added 2026-08-31)
- docs/plans/rpg_design_roadmap/rpg_design_roadmap.md ("§9.3/§9.4 conflicts — code-verified" entry, added 2026-08-31)

## Related Stored Artifacts
None.

## Related Code Areas
- src/worldbuilding/compiler.py
- src/domains/demographics/cohort.py
- src/core/state.py
- src/engine/world_dynamics.py
- src/engine/apply_plan.py
- src/worldbuilding/schema.py
- src/core/builder.py
- tests/unit/world/test_demographics.py
- tests/unit/worldbuilding/test_world_compiler.py

## Assumptions / Open Questions
- The young/adult/elder distribution ratio is an open design decision with zero existing anchor — must be explicitly authored and documented, not treated as obvious.
- This is the first time DemographicCycleService's logic will ever run against real compiled-world data — corpus/integration-level testing should be required, not just unit tests.
- Real class name is PopulationCohort (docs/brainstorm/rpg_expected_schemas.html), not 'CohortState' as some docs call it.
- **Temporal-axis caution (`TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY`, decided):** the current tick-based age-bracket thresholds (`<3000`/`<7000`/`≥7000`) produce only a 4.17-day maximum lifespan under the now-settled 2,400-ticks/day calendar authority. Migrating age representation to fantasy-year units is an accepted-but-not-yet-implemented future decision. This ticket seeds population *counts* into the existing buckets, not the buckets themselves, so it is not blocked — but must not treat these specific tick values as permanent or build anything that would need non-trivial rework once that migration lands. Balancing/resolving the actual numbers is explicitly not required of this ticket; documenting the assumption is.
- **Cadence-coupled rate finding (code-verified 2026-08-31):** `PopulationCohort.birth_rate`/`mortality_rate` are defined and coded as "per 200-tick cycle" — the rate's real-world meaning is tied directly to `DemographicCycleService`'s evaluation cadence (`COHORT_INTERVAL=200`), not a calendar-independent duration unit (e.g. births/year). Since this ticket is the one that will next touch these exact fields, seed values chosen now inherit that ambiguity — state the intended real-world meaning explicitly when choosing seed numbers, or flag it as a known gap for the future calendar-authority migration ticket to resolve. Checked across all 16 M2 ideas: idea 43 (this ticket) is the *only* one with real exposure to the temporal-axis findings — no other M2 batch ticket needs this treatment.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
