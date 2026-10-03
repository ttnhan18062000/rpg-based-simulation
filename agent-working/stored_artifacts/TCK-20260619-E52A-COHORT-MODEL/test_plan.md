# Test Plan: TCK-20260619-E52A-COHORT-MODEL

## Test File
`tests/unit/world/test_demographics.py`

## Run Command
```bash
pytest tests/unit/world/test_demographics.py -x -v
```

## Test Cases

### test_cohort_birth_generates_spawn_event
- Setup: RegionState with `population_cohorts = {"young": PopulationCohort(bracket="young", count=100, birth_rate=0.02, mortality_rate=0.01)}`
- Input: tick=200
- Expected: StateUpdate world_updates["region1"].population_cohorts_set["young"].count == 101

### test_cohort_death_reduces_count  
- Setup: RegionState with `population_cohorts = {"elder": PopulationCohort(bracket="elder", count=100, birth_rate=0.00, mortality_rate=0.05)}`
- Input: tick=200
- Expected: StateUpdate world_updates["region1"].population_cohorts_set["elder"].count == 95

### test_no_update_between_intervals
- Input: tick=199
- Expected: StateUpdate is noop (no world_updates)

### test_zero_net_skips_cohort_update
- Setup: PopulationCohort(count=100, birth_rate=0.01, mortality_rate=0.01) → net=0
- Expected: region not in world_updates

### test_region_without_cohorts_skipped
- Setup: RegionState with empty population_cohorts dict
- Input: tick=200
- Expected: StateUpdate is noop

## Regression Check
Run after implementation:
```bash
pytest tests/unit/world/ -x -v -m "not slow"
```
Specifically verify RegionState construction tests still pass (new field has `default_factory=dict`).
