# TCK-20260513-PERF-HARDENING-DIRTY-SPATIAL

## Title
Optimize RPG Engine Dirty Tracking and Spatial Lookups

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement O(1) dirty-entity tracking and spatial indexing to reduce computational overhead in the V2 RPG Engine.

## Scope
- Implement `DirtySet` for change categorization.
- Optimize high-load subsystems (Town, Strategic, Group, Shop).
- Implement `SpatialQueryService` for proximity lookups.
- Refactor `LegalityServiceV2` to use spatial indexing.

## Out of Scope
- API snapshot optimization (Milestone 5).
- Biological system staggering.

## Acceptance Criteria
- [x] $O(1)$ lookup for buildings and occupancy.
- [x] $O(Dirty)$ iteration for core passive systems.
- [x] Performance benchmarks pass for 5000+ entities.
- [x] Determinism maintained.

## Related Tickets
- TCK-20260513-PERF-HARDENING

## Related Docs
- [optimization_implementation.md](file:///home/vboxuser/Work/rpg-based-simulation/optimization_implementation.md)
- [logic_checklist_exhaustive.md](file:///home/vboxuser/Work/rpg-based-simulation/logic_checklist_exhaustive.md)

## Related Stored Artifacts
None

## Related Code Areas
- `src/core/dirty.py`
- `src/engine/spatial_query.py`
- `src/engine/legality.py`
- `src/engine/town_resolution.py`

## Implementation Notes
- Used per-tick caching in `AuthoritativeState` for spatial lookups.
- Integrated `DirtySet` into the main refinement pipeline.

## Test Summary
- `tests/perf/test_perf_passive_scaling.py`: PASS (100, 1000, 5000 entities)

## Files Changed
- `src/core/dirty.py`
- `src/engine/pipeline.py`
- `src/engine/spatial_query.py`
- `src/engine/legality.py`
- `src/engine/town_resolution.py`
- `src/engine/shop.py`
- `src/engine/sabotage.py`
- `src/engine/pipeline_phases/interactions.py`
- `src/systems/world_systems/groups.py`
- `src/systems/strategic_systems/intelligence.py`
- `src/systems/strategic_systems/redirection.py`

## Completion Summary
Completed Milestones 3 and 4 of the performance roadmap. Reduced per-tick compute from $O(N)$ to $O(Dirty)$ for most systems and $O(1)$ for spatial lookups.
