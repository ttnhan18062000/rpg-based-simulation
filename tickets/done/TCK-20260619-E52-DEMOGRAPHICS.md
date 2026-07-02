---
status: done
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260619-E52-DEMOGRAPHICS
phase: done
date: 2026-06-19
tags: [demographics, population-cohorts, birth-death, migration, age-structure, epic, phase-5]
---

# TCK-20260619-E52-DEMOGRAPHICS

## Title
Epic 5.2 · Demographic / Cohort Population Model

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
`SpawnService` and `ResourceEcologyService` are density/spawn-rate driven. No age-structured birth/death/migration cohorts. Current model cannot show population aging or generational change. Needed for any long-horizon (century+) simulation.

Score: 6/10 · Effort: M · Source: `docs/plans/engine_future_epics_roadmap.md` § A

## Scope
- **Prerequisites:** TCK-20260619-E21-RESOURCE-ECOLOGY (migration pressure driven by scarcity); TCK-20260619-E32-CAMPAIGN-RUNTIME (multi-episode span)
- `PopulationCohort` durable model per region: cohorts by age_bracket (young/adult/elder), birth_rate, mortality_rate, migration_threshold
- Birth/death cycle: each N ticks, apply rates; produce spawn events for new young entities when cohort exceeds threshold
- Migration pressure: when regional resource scarcity exceeds threshold (from Epic 2.1), migration_pressure rises; cohorts above threshold emigrate to adjacent regions
- Age advancement: entities carry `age_ticks`; at threshold intervals, advance age bracket; elders have higher mortality, lower combat effectiveness, higher knowledge/reputation weight
- Population density signals: wire cohort density into `RegionalPressureModel` as demand signal
- Child tickets: (a) PopulationCohort model + birth/death cycle, (b) migration pressure + cohort movement, (c) entity age advancement, (d) density signals to RegionalPressureModel

## Out of Scope
- Genetic trait inheritance
- Cultural transmission between generations (Phase 6)
- Player population management

## Acceptance Criteria
- In a 2000-tick run, at least one region's cohort composition changes measurably (emigration from scarcity or immigration from abundance)
- An elder entity exists that started as young in episode 1

## Related Tickets
- TCK-20260619-E21-RESOURCE-ECOLOGY (prerequisite: scarcity signals for migration)
- TCK-20260619-E32-CAMPAIGN-RUNTIME (prerequisite: multi-episode entity age tracking)
- TCK-20260619-E51-CHRONICLE (unlocked: demographic shifts feed into chronicle milestones)
- TCK-20260619-E52A-COHORT-MODEL (child)
- TCK-20260619-E52B-MIGRATION (child)
- TCK-20260619-E52C-AGE-ADVANCEMENT (child)
- TCK-20260619-E52D-DENSITY-SIGNAL (child)

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` § A
- `docs/plans/long_term_development_roadmap.md` § Epic 5.2
- `docs/mechanics/01_entity_anatomy.md` § Biological Pressures
- `docs/mechanics/06_worldbuilding_foundation.md` (population distribution rules)
- `docs/mechanics/05_world_evolution.md` (demographic cycle documentation)
- `docs/world/ecology_and_calamity_contract.md` (PopulationCohort as demand signal)
- `docs/parity_ledger/world_dynamics.yaml` (cohort model entries)
- New doc: `docs/world/demographics_contract.md` (PopulationCohort model, birth/death cycle, migration pressure rules, age bracket thresholds, density signal contract)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260619-E52-DEMOGRAPHICS/`
- `stored_artifacts/TCK-20260613-DOC-WORLD-RUNTIME-SIMULATION/`

## Related Code Areas
- `src/core/state.py:L143` (`age_ticks` — already exists; L204 RegionState — add population_cohorts)
- `src/systems/world_systems/` (SpawnService — integrate with birth/death cycle)
- `src/systems/world_systems/resource_ecology.py` (ResourceEcologyService — read scarcity)

## Assumptions / Open Questions
- Birth/death cycle interval: 200 ticks (same cadence as ecology) — confirmed in investigation.md
- `age_ticks` already exists at `src/core/state.py:L143` — E52A does NOT add it; only PopulationCohort model is new
- Adjacent regions: check `docs/mechanics/06_worldbuilding_foundation.md` topology rules in E52B before implementing adjacency lookup

## Implementation Notes
Cohort model is additive — entities can coexist with an abstract demographic cohort in the same region. The cohort drives spawn events that create new `EntityState` instances. Elder-tier entities should have stat multipliers wired through `AttributeComponent`, not special-cased logic.

After implementation: create `docs/world/demographics_contract.md`. Update `docs/mechanics/05_world_evolution.md` with demographic cycle documentation. Update `docs/world/ecology_and_calamity_contract.md` with PopulationCohort density signal. Update `docs/parity_ledger/world_dynamics.yaml`. Run `make knowledge-index-update` after docs/ changes.

## Test Summary
- New file `tests/unit/world/test_demographics.py`:
  - `test_cohort_birth_generates_spawn_event()`
  - `test_cohort_death_reduces_count()`
  - `test_age_bracket_returns_correct_bracket()`
  - `test_elder_modifier_reduces_combat_effectiveness()`
  - `test_migration_pressure_triggers_on_scarcity_threshold()`
- New file `tests/integration/scenarios/test_demographics.py`:
  - `test_cohort_migrates_on_scarcity()`
  - `test_2000_tick_run_produces_cohort_demographic_change()`

## Files Changed
- `tickets/todos/TCK-20260619-E52A-COHORT-MODEL.md`
- `tickets/todos/TCK-20260619-E52B-MIGRATION.md`
- `tickets/todos/TCK-20260619-E52C-AGE-ADVANCEMENT.md`
- `tickets/todos/TCK-20260619-E52D-DENSITY-SIGNAL.md`
- `staging_artifacts/TCK-20260619-E52-DEMOGRAPHICS/investigation.md`
- `staging_artifacts/TCK-20260619-E52-DEMOGRAPHICS/plan.md`
- `staging_artifacts/TCK-20260619-E52-DEMOGRAPHICS/test_plan.md`

## Completion Summary
EPIC_SCOPED. Staged 4 child tickets (E52A–E52D) covering PopulationCohort model, migration pressure, age bracket advancement, and density signal wiring. Key insight: `age_ticks` already exists at `src/core/state.py:L143`; only the bracket logic and cohort model are new. Staging artifacts written.
