# Investigation: TCK-20260619-E52A-COHORT-MODEL

## Topic
PopulationCohort model + DemographicCycleService birth/death at 200-tick cadence.

## Key Findings

### Existing infrastructure
- `RegionState` (`src/core/state.py:L207`) is a `frozen=True, slots=True` dataclass. Adding a `population_cohorts: Dict[str, PopulationCohort]` field with `default_factory=dict` requires no other change to `__post_init__` or `to_readonly()`.
- `WorldUpdate` (`src/core/updates.py:L747`) is the standard delta object for `RegionState`. Adding `population_cohorts_set: Optional[Dict[str, PopulationCohort]] = None` allows the apply pipeline to overwrite cohort state.
- `apply_plan.py` lines 108-128 commit `WorldUpdate` fields to `RegionState` via `replace(reg, ...)`. We add `population_cohorts` to that replace call.
- `world_dynamics.py` already wires `ResourceEcologyService` at step 3.2 within the `should_run(state.tick, None, cadence.world_dynamics)` gate. We add `DemographicCycleService` as step 3.7 in the same block, returning a `StateUpdate` with `world_updates`.
- `StateUpdate.entities_add` is the correct channel for new entity spawns (births). `WorldUpdate.population_cohorts_set` is used for net-negative (death) adjustments to the cohort count.

### Design decision: no SpawnRequestUpdate type
The ticket spec mentions `SpawnRequestUpdate` as a new update type. Investigation shows existing spawn flow uses `StateUpdate.entities_add` with actual `EntityState` objects created by `EntityGenerator`. Creating a full entity per birth is expensive and unnecessary for a demographic abstraction model. Instead, `DemographicCycleService` returns a `StateUpdate` with:
- `world_updates`: contains a `WorldUpdate` per region with `population_cohorts_set` reflecting the updated cohort counts after birth/death (net applied).
- `world_events_add`: one `WorldEvent` per affected cohort-region pair for observability.

This matches the pattern used by `ResourceEcologyService` (returns `StateUpdate`) and avoids introducing a new update type not used elsewhere.

### `COHORT_INTERVAL = 200`
Matches `ResourceEcologyService.ECOLOGY_INTERVAL = 200`. Consistent cadence.

### `slots=True` constraint
`PopulationCohort` uses `frozen=True, slots=True` matching the project-wide pattern for durable domain models (all `*State` and `*Component` types use this pattern).

### apply_plan.py RegionState replace
Lines 124-127 list every field explicitly. Must add `population_cohorts=pop_cohorts` to the replace call.

### is_noop() in StateUpdate
No change needed — `world_updates` dict covers cohort changes since they go through `WorldUpdate`.
