---
status: open
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260619-E52A-COHORT-MODEL
phase: open
date: 2026-06-20
tags: [demographics, population-cohort, birth-death, region-state, phase-5]
---

# TCK-20260619-E52A-COHORT-MODEL

## Title
Epic 5.2A · PopulationCohort Model + Birth/Death Cycle

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
No population cohort model exists. This ticket introduces `PopulationCohort` as a per-region durable model and `DemographicCycleService` implementing birth/death at 200-tick cadence.

**Blocks:** All other E52 child tickets

## Scope

New file `src/domains/demographics/cohort.py`:

```python
@dataclass(frozen=True, slots=True)
class PopulationCohort:
    bracket: str            # "young" | "adult" | "elder"
    count: int = 0
    birth_rate: float = 0.02         # births per 200-tick cycle as fraction
    mortality_rate: float = 0.01
    migration_threshold: float = 0.7  # scarcity above this → emigrate

class DemographicCycleService:
    COHORT_INTERVAL = 200  # ticks

    @staticmethod
    def tick(state: AuthoritativeState, tick: int) -> list[StateUpdate]:
        """Apply birth/death to all regions' cohorts every COHORT_INTERVAL ticks."""
        if tick % DemographicCycleService.COHORT_INTERVAL != 0:
            return []
        updates = []
        for region_id, region in state.regions.items():
            for bracket, cohort in region.population_cohorts.items():
                births = cohort.count * cohort.birth_rate
                deaths = cohort.count * cohort.mortality_rate
                net = int(births - deaths)
                if net > 0:
                    updates.append(SpawnRequestUpdate(region_id=region_id, count=net, bracket=bracket))
                if net < 0:
                    updates.append(CohortUpdate(region_id=region_id, bracket=bracket, delta=net))
        return updates
```

Add to `RegionState` (`src/core/state.py:L204`):
```python
population_cohorts: Dict[str, PopulationCohort] = field(default_factory=dict)
```

Wire `DemographicCycleService.tick()` into world dynamics phase (same tier as `ResourceEcologyService`).

## Acceptance Criteria
- `test_cohort_birth_generates_spawn_event` passes
- `test_cohort_death_reduces_count` passes
- All existing RegionState tests pass (new field has default)

## Related Tickets
- TCK-20260619-E52-DEMOGRAPHICS (parent epic)
- TCK-20260619-E52B-MIGRATION (blocked on this)

## Related Code Areas
- `src/domains/demographics/cohort.py` (new)
- `src/core/state.py:L204` (RegionState — add population_cohorts)
- `src/systems/world_systems/` (wire DemographicCycleService)

## Test Summary
```bash
pytest tests/unit/world/test_demographics.py -x -v
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
