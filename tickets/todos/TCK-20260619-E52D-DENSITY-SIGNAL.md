---
status: open
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260619-E52D-DENSITY-SIGNAL
phase: open
date: 2026-06-20
tags: [demographics, density-signal, regional-pressure, phase-5]
---

# TCK-20260619-E52D-DENSITY-SIGNAL

## Title
Epic 5.2D · Population Density Signal to RegionalPressureModel

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Closes the feedback loop: `PopulationCohort.count` feeds into `RegionalPressureModel` as a population density demand signal, making high-population regions generate more economic pressure.

**Requires:** TCK-20260619-E52C-AGE-ADVANCEMENT

## Scope

Find `RegionalPressureModel` in codebase (likely `src/systems/world_systems/` or `src/engine/`). Add `population_density` as a demand signal:

```python
population_density = (
    region.population_cohorts.get("young", PopulationCohort("young")).count +
    region.population_cohorts.get("adult", PopulationCohort("adult")).count +
    region.population_cohorts.get("elder", PopulationCohort("elder")).count
) / max(1, region.area)
```

Wire as a multiplier on resource demand: `demand_multiplier = 1.0 + (population_density * 0.5)`.

After E52D: create `docs/world/demographics_contract.md`. Update `docs/mechanics/05_world_evolution.md` with demographic cycle. Update `docs/world/ecology_and_calamity_contract.md` with density signal. Update `docs/parity_ledger/world_dynamics.yaml`. Run `make knowledge-index-update`.

## Acceptance Criteria
- High-population region generates measurably higher resource demand than low-population region in 200-tick test
- `test_2000_tick_run_produces_cohort_demographic_change` passes

## Related Tickets
- TCK-20260619-E52-DEMOGRAPHICS (parent epic)
- TCK-20260619-E52C-AGE-ADVANCEMENT (required)

## Related Docs
- `docs/world/demographics_contract.md` (new — create after implementation)
- `docs/world/ecology_and_calamity_contract.md` (update density signal section)

## Related Code Areas
- RegionalPressureModel (find location before implementing)
- `src/domains/demographics/cohort.py` (population_density helper)

## Test Summary
```bash
pytest tests/integration/scenarios/test_demographics.py::test_2000_tick_run_produces_cohort_demographic_change -x -v -m slow
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
