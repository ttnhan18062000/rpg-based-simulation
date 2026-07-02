# Test Plan — TCK-20260619-E52D-DENSITY-SIGNAL

## Unit tests (tests/unit/world/test_demographics.py)

| ID | Test | Assertion |
|---|---|---|
| TC-D5-01 | `test_compute_population_density_zero_cohorts` | Returns 0.0 for region with no cohorts |
| TC-D5-02 | `test_compute_population_density_single_bracket` | count=100, area=100×100=10000 → density=0.01 |
| TC-D5-03 | `test_compute_population_density_all_brackets` | Sums young+adult+elder correctly |
| TC-D5-04 | `test_compute_population_density_degenerate_area` | bounds=(0,0,0,0) → area=0 → max(1,0)=1 → no div-by-zero |

## Integration test (tests/integration/scenarios/test_demographics.py)

| ID | Test | Assertion |
|---|---|---|
| TC-D5-05 | `test_2000_tick_run_produces_cohort_demographic_change` | High-pop region demand_multiplier > 1.0 > zero-pop region; 200-tick cycle changes cohort counts |
| TC-D5-06 | `test_high_population_region_higher_resource_demand` | demand_multiplier for high-pop region > demand_multiplier for zero-pop region |

## Run command
```bash
pytest tests/unit/world/test_demographics.py -x -v
pytest tests/integration/scenarios/test_demographics.py -x -v -m slow
```
