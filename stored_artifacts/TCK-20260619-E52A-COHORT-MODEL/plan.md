# Plan: TCK-20260619-E52A-COHORT-MODEL

## Changes

### 1. New file: `src/domains/demographics/__init__.py`
Empty, marks package.

### 2. New file: `src/domains/demographics/cohort.py`
- `PopulationCohort` dataclass (`frozen=True, slots=True`): `bracket`, `count`, `birth_rate`, `mortality_rate`, `migration_threshold`
- `DemographicCycleService` static class:
  - `COHORT_INTERVAL = 200`
  - `process_demographics(state, tick) -> StateUpdate`: skips if tick % 200 != 0; iterates regions; computes net birth/death; returns StateUpdate with world_updates per region (population_cohorts_set with new counts) and world_events_add for observability.

### 3. Modify `src/core/updates.py`
- Add `population_cohorts_set: Optional[Dict[str, Any]] = None` to `WorldUpdate` dataclass.
- Update `WorldUpdate.merge()` to handle `population_cohorts_set` (last-write wins).

### 4. Modify `src/core/state.py`
- Add `population_cohorts: Dict[str, Any] = field(default_factory=dict)` to `RegionState`.
- Add `"population_cohorts": dict(sorted(self.population_cohorts.items()))` to `RegionState.to_canonical_dict()`.

### 5. Modify `src/engine/apply_plan.py`
- In the region replace block (lines 124-127): read `pop_cohorts = r_upd.population_cohorts_set if r_upd.population_cohorts_set is not None else reg.population_cohorts`; add `population_cohorts=pop_cohorts` to `replace(reg, ...)`.

### 6. Modify `src/engine/world_dynamics.py`
- In step 3 block (after step 3.6 raid): add step 3.7 calling `DemographicCycleService.process_demographics(state, state.tick)` and merge into the update.

### 7. New test file: `tests/unit/world/test_demographics.py`
- `test_cohort_birth_generates_spawn_event`: region with young cohort count=100, birth_rate=0.02, mortality_rate=0.01 at tick=200 → net=+1 → world_update has population_cohorts_set with count=101.
- `test_cohort_death_reduces_count`: region with elder cohort count=100, birth_rate=0.00, mortality_rate=0.05 at tick=200 → net=-5 → world_update has population_cohorts_set with count=95.
- `test_no_update_between_intervals`: tick=199 → returns empty StateUpdate.
- `test_zero_net_skips_update`: birth_rate == mortality_rate → no world_update emitted for that cohort.

## Wiring Summary
DemographicCycleService is called inside the `should_run(state.tick, None, cadence.world_dynamics)` gate in `world_dynamics.py`, consistent with how `ResourceEcologyService` and `CalamityService` are called.
