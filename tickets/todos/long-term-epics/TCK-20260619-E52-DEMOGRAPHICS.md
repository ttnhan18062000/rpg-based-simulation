---
status: open
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260619-E52-DEMOGRAPHICS
phase: open
date: 2026-06-19
tags: [demographics, population-cohorts, birth-death, migration, age-structure, epic, phase-5]
---

# TCK-20260619-E52-DEMOGRAPHICS

## Title
Epic 5.2 · Demographic / Cohort Population Model

## Status
OPEN

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
- `nomadic_herd` and `settled_quarter` population modules (authored in Epic 1.3) acquire demographic models here
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

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` § A
- `docs/plans/long_term_development_roadmap.md` § Epic 5.2
- `docs/mechanics/01_entity_anatomy.md` § Biological Pressures (entity age advancement affects biological stats — elder entities have higher mortality; verify aging mechanics against attribute definitions here)
- `docs/mechanics/06_worldbuilding_foundation.md` (population distribution rules — `nomadic_herd` and `settled_quarter` modules from Epic 1.3 acquire demographic models here; must conform to topology rules)
- `docs/mechanics/05_world_evolution.md` (add demographic cycle documentation; migration pressure ties into tick-to-day time and regional evolution)
- `docs/world/ecology_and_calamity_contract.md` (update with PopulationCohort as demand signal to RegionalPressureModel)
- `docs/parity_ledger/world_dynamics.yaml` (population/ecology entries — add cohort model as `verified`)
- New doc: `docs/world/demographics_contract.md` (PopulationCohort model, birth/death cycle, migration pressure rules, age bracket thresholds, density signal contract)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260613-DOC-WORLD-RUNTIME-SIMULATION/`

## Related Code Areas
- `src/core/state.py` (RegionState at L204 — add PopulationCohort; EntityState at L568 — add age_ticks)
- `src/systems/world_systems/` (SpawnService — integrate with birth/death cycle)
- `src/systems/world_systems/resource_ecology.py` (ResourceEcologyService — read scarcity for migration pressure)

## Assumptions / Open Questions
- What is a reasonable birth/death cycle interval? Avoid per-tick rate (too expensive); suggest every 200 ticks (same cadence as ecology)
- How are "adjacent regions" defined? Check regional topology in `docs/mechanics/06_worldbuilding_foundation.md`

## Implementation Notes
Cohort model is additive — entities can coexist with an abstract demographic cohort in the same region. The cohort drives spawn events that create new `EntityState` instances. Elder-tier entities should have stat multipliers wired through `AttributeComponent`, not special-cased logic.

After implementation: create `docs/world/demographics_contract.md`. Update `docs/mechanics/05_world_evolution.md` with demographic cycle documentation. Update `docs/world/ecology_and_calamity_contract.md` with PopulationCohort density signal. Update `docs/parity_ledger/world_dynamics.yaml`. Run `make knowledge-index-update` after docs/ changes.

## Test Summary
- New file `tests/unit/world/test_demographics.py`:
  - `test_cohort_birth_generates_spawn_event()` — configure birth_rate > 0, run N cohort ticks, assert spawn event emitted
  - `test_cohort_death_reduces_count()` — configure mortality_rate > 0, run N cohort ticks, assert cohort count decreases
  - `test_cohort_does_not_exceed_regional_cap()` — assert cohort count bounded by region capacity
- New file `tests/integration/scenarios/test_demographics.py`:
  - `test_cohort_migrates_on_scarcity()` — deplete regional resources (via Epic 2.1 mechanics); assert emigration event and cohort count decreases in source region
  - `test_entity_age_advances_to_elder_across_episodes()` — entity starts as YOUNG in ep1; assert AGE=ELDER after sufficient episodes

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
