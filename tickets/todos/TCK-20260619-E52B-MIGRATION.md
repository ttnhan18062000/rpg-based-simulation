---
status: open
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260619-E52B-MIGRATION
phase: open
date: 2026-06-20
tags: [demographics, migration, scarcity, cohort-movement, phase-5]
---

# TCK-20260619-E52B-MIGRATION

## Title
Epic 5.2B · Migration Pressure + Cohort Movement

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
When regional scarcity exceeds `cohort.migration_threshold`, 30% of that cohort emigrates to the lowest-scarcity adjacent region.

**Requires:** TCK-20260619-E52A-COHORT-MODEL

## Scope

In `DemographicCycleService.tick()`, after birth/death:

```python
def _check_migration(region_id: str, region: RegionState, state: AuthoritativeState) -> list[StateUpdate]:
    scarcity = compute_regional_scarcity(region, state)  # from ResourceEcologyService
    updates = []
    for bracket, cohort in region.population_cohorts.items():
        if scarcity > cohort.migration_threshold:
            adjacent = find_adjacent_regions(region_id, state)
            if not adjacent:
                continue
            target = min(adjacent, key=lambda r: compute_regional_scarcity(r, state))
            emigrant_count = max(1, int(cohort.count * 0.30))
            updates.append(CohortTransferUpdate(
                source_region=region_id, target_region=target.id,
                bracket=bracket, count=emigrant_count
            ))
    return updates
```

**Adjacent regions**: read from `docs/mechanics/06_worldbuilding_foundation.md` topology rules before implementing the adjacency lookup. Likely based on bounds overlap or explicit adjacency list in world spec.

**Scarcity**: aggregate `remaining_charges / max_charges` across all resource nodes in the region. Zero resources = scarcity 1.0.

Emit `cohort_migration` SimulationEvent when emigration fires.

## Acceptance Criteria
- `test_migration_pressure_triggers_on_scarcity_threshold` passes
- `test_cohort_migrates_on_scarcity` integration test passes

## Related Tickets
- TCK-20260619-E52-DEMOGRAPHICS (parent epic)
- TCK-20260619-E52A-COHORT-MODEL (required)
- TCK-20260619-E52C-AGE-ADVANCEMENT (blocked on this)

## Related Code Areas
- `src/domains/demographics/cohort.py` (extend DemographicCycleService)
- `src/systems/world_systems/resource_ecology.py` (ResourceEcologyService — read scarcity)

## Test Summary
```bash
pytest tests/unit/world/test_demographics.py::test_migration_pressure_triggers_on_scarcity_threshold -x -v
pytest tests/integration/scenarios/test_demographics.py::test_cohort_migrates_on_scarcity -x -v -m slow
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
