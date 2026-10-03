# Plan — TCK-20260619-E52D-DENSITY-SIGNAL

## Steps

1. **cohort.py** — add `compute_population_density(region) -> float` pure function.
   Sums young+adult+elder counts, divides by `max(1, area_from_bounds)`.

2. **models.py** — in `RegionalPressureModel.evaluate()`:
   - Import `compute_population_density` from `src.domains.demographics.cohort`
   - Compute `demand_multiplier = 1.0 + (compute_population_density(reg_state) * 0.5)` per region
   - Apply to `res_intensity`: `res_intensity = min(1.0, res_intensity * demand_multiplier)`

3. **tests/unit/world/test_demographics.py** — add unit tests for `compute_population_density`.

4. **tests/integration/scenarios/test_demographics.py** — add `test_2000_tick_run_produces_cohort_demographic_change` (AC test).

5. **docs/world/demographics_contract.md** — new contract doc covering full E52A–E52D.

6. **docs/mechanics/05_world_evolution.md** — add demographic cycle section.

7. **docs/world/ecology_and_calamity_contract.md** — add density signal subsection.

8. **docs/parity_ledger/world_dynamics.yaml** — add WORLD-DEMO-005.

9. **make knowledge-index-update** after docs changes.

## Architecture Notes
- `compute_population_density` is a pure function (no side effects), consistent with existing E52 helpers.
- `demand_multiplier` only affects the resource pressure intensity — not danger or camp pressures.
- RegionState has no `area` field; derive from `bounds` tuple in the helper.
- The 2000-tick AC test does not run a real engine loop; it manually advances ticks via `DemographicCycleService.process_demographics()` and checks cohort state + density signal.
