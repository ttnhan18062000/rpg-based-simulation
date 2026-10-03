# Investigation — TCK-20260619-E52D-DENSITY-SIGNAL

## Findings

### RegionalPressureModel location
`src/domains/world_emergence/models.py` — `RegionalPressureModel.evaluate(state, aggregates)` static method.
Called from `WorldEmergencePhase.execute()` in `src/domains/world_emergence/phase.py`.

### RegionState
`src/core/state.py` — `RegionState` dataclass. Has `population_cohorts: Dict[str, Any]`.
Has no `area` field; area must be derived from `bounds` tuple: `(xmax - xmin) * (ymax - ymin)`.

### Resource pressure section
The existing "resource" pressure in `RegionalPressureModel` computes intensity from harvest/depletion counts.
The density signal must augment resource demand by applying a `demand_multiplier` to the base resource pressure intensity.

### demand_multiplier formula (from ticket scope)
```python
total_pop = sum of young + adult + elder counts
area = (xmax - xmin) * (ymax - ymin)  # derived from bounds
population_density = total_pop / max(1, area)
demand_multiplier = 1.0 + (population_density * 0.5)
```
Applied to `res_intensity` for the "resource" pressure kind.

### Helper function placement
A `compute_population_density(region)` pure function will be added to `src/domains/demographics/cohort.py` for reuse and testability.

### Test gap
No 2000-tick integration test exists. Must add `test_2000_tick_run_produces_cohort_demographic_change` to `tests/integration/scenarios/test_demographics.py`.
AC: high-population region has higher resource demand (demand_multiplier > 1.0) than zero-population region.

### Docs to update after implementation
- Create `docs/world/demographics_contract.md`
- Update `docs/mechanics/05_world_evolution.md` (§demographic cycle section)
- Update `docs/world/ecology_and_calamity_contract.md` (§density signal)
- Add WORLD-DEMO-005 parity entry to `docs/parity_ledger/world_dynamics.yaml`
