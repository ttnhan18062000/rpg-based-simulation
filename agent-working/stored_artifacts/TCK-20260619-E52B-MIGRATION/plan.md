# Plan — TCK-20260619-E52B-MIGRATION

## Objective
Implement migration pressure: when regional scarcity exceeds a cohort's migration_threshold, 30% of that cohort emigrates to the lowest-scarcity adjacent region.

## Files to Change

1. `src/domains/world_emergence/schema.py`
   - Add `POPULATION_MIGRATION = "POPULATION_MIGRATION"` to `WorldEventCategory`

2. `src/domains/demographics/cohort.py`
   - Add `compute_regional_scarcity(region_id, state)` — pure function
   - Add `find_adjacent_regions(region_id, state)` — pure function, deterministic (sorted by id)
   - Add `_check_migration(region_id, region, state, tick)` — returns (list[WorldUpdate dict], list[WorldEvent])
   - Extend `DemographicCycleService.process_demographics()` to call `_check_migration` and merge results

3. `tests/unit/world/test_demographics.py`
   - Add `TestMigrationPressure` class with `test_migration_pressure_triggers_on_scarcity_threshold` and related edge case tests

4. `tests/integration/scenarios/test_demographics.py` (new file)
   - `test_cohort_migrates_on_scarcity` — end-to-end: two adjacent regions, one scarce; verify cohort moves

## Key Decisions

- **Scarcity formula**: `1.0 - mean(remaining_charges/max_charges)` for all nodes whose position falls within region bounds. Zero nodes = 1.0.
- **Adjacency**: bounds share an edge (one axis aligns exactly, other overlaps). Pure function from state.regions.
- **Determinism**: `sorted(state.regions.items())` before iteration; target selected with `min(..., key=lambda r: (scarcity, r.id))`.
- **WorldUpdate encoding**: use existing `population_cohorts_set` — source region gets full updated cohort dict with reduced count; target region gets full updated cohort dict with increased count.
- **No new StateUpdate types**: reuse `WorldUpdate.population_cohorts_set` for both source and target updates. Emit `WorldEvent(POPULATION_MIGRATION)` per migration.

## Out of Scope
- Persistent CohortTransferUpdate record type (ticket spec shows pseudocode, not a required new type)
- Cross-tick cohort tracking
- Destination region validation beyond adjacency
