---
status: done
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260619-E52D-DENSITY-SIGNAL
phase: done
date: 2026-06-20
tags: [demographics, density-signal, regional-pressure, phase-5]
---

# TCK-20260619-E52D-DENSITY-SIGNAL

## Title
Epic 5.2D · Population Density Signal to RegionalPressureModel

## Status
DONE

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
- `src/domains/demographics/cohort.py` — added `compute_population_density()` pure function
- `src/domains/world_emergence/models.py` — imported `compute_population_density`; applied `demand_multiplier` to resource pressure intensity in `RegionalPressureModel.evaluate()`
- `tests/unit/world/test_demographics.py` — added 6 unit tests (`TestComputePopulationDensity`)
- `tests/integration/scenarios/test_demographics.py` — added 2 integration tests (`test_2000_tick_run_produces_cohort_demographic_change`, `test_high_population_region_higher_resource_demand`)
- `docs/world/demographics_contract.md` — new contract doc covering E52A–E52D
- `docs/mechanics/05_world_evolution.md` — added §5 Demographic Cohort Cycle
- `docs/world/ecology_and_calamity_contract.md` — added §Population Density Demand Signal
- `docs/parity_ledger/world_dynamics.yaml` — added WORLD-DEMO-005

## Completion Summary
`compute_population_density(region)` pure function added to `cohort.py`: sums all cohort counts, divides by `max(1, area_from_bounds)`. `RegionalPressureModel` imports and applies `demand_multiplier = 1.0 + (density * 0.5)` to resource pressure intensity, recorded in `source_aggregates` for traceability. 6 new unit tests + 2 integration AC tests pass (61 total demographics tests). WORLD-DEMO-005 parity entry added. Full demographics contract doc created covering E52A–E52D. Both AC tests pass: `test_2000_tick_run_produces_cohort_demographic_change` and `test_high_population_region_higher_resource_demand`.
