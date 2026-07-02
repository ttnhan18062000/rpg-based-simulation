# Test Plan — TCK-20260619-E52B-MIGRATION

## Unit Tests (tests/unit/world/test_demographics.py)

### TestMigrationPressure

| Test | Scenario | Expected |
|---|---|---|
| `test_migration_pressure_triggers_on_scarcity_threshold` | 1 region, 1 cohort, scarcity > threshold, 1 adjacent region | WorldUpdate for source (reduced count) + WorldUpdate for target (increased count) + POPULATION_MIGRATION event |
| `test_no_migration_below_threshold` | scarcity < threshold | No migration updates (noop for migration) |
| `test_no_migration_no_adjacent` | scarcity > threshold, no adjacent regions | No migration (skip) |
| `test_migration_emigrant_count_30pct` | count=100, scarcity > threshold | emigrant_count == 30 |
| `test_migration_emigrant_count_min_1` | count=1, scarcity > threshold | emigrant_count == 1 (max(1,...)) |
| `test_migration_deterministic_target` | scarcity > threshold, 2 adjacent regions with different scarcity | target = lower-scarcity region |

## Integration Tests (tests/integration/scenarios/test_demographics.py)

### test_cohort_migrates_on_scarcity
- Build state with 2 adjacent regions: `r1` (depleted resources → high scarcity), `r2` (full resources → low scarcity)
- `r1` has young cohort with count=100, migration_threshold=0.7
- `r1` has 1 resource node with remaining_charges=0, max_charges=5 → scarcity=1.0
- `r2` has 1 resource node with remaining_charges=5, max_charges=5 → scarcity=0.0
- Call `process_demographics(state, tick=200)`
- Assert: `world_updates["r1"].population_cohorts_set["young"].count == 70` (100 - 30)
- Assert: `world_updates["r2"].population_cohorts_set["young"].count == 30`
- Assert: POPULATION_MIGRATION event emitted with region_id="r1"

## Regression
- Run full `tests/unit/world/test_demographics.py` to confirm E52A tests still pass
- Confirm `TestCohortZeroNet.test_region_without_cohorts_skipped` still passes (empty cohorts → no migration)
