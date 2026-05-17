# Investigation: OccupancySnapshot

## Current State

In `src/engine/legality.py` and `src/engine/spatial_query.py`, occupancy lookups and entity priority checks (`LegalityServiceV2.get_entity_priority`) are performed repeatedly during movement resolution, pathfinding, and combat validation. Although `SpatialQueryService.get_occupancy_map` caches a dictionary on `state`, priority calculations and tile checks are not fully consolidated into a single immutable snapshot per tick.

## Optimization Strategy

Implement `OccupancySnapshot` as a frozen dataclass encapsulating `tick`, `occupancy_by_tile` (mapping `(x, y)` to `entity_id`), and `priority_by_entity` (mapping `entity_id` to priority score). This provides a perfectly stable, immutable read model for the entire tick, ensuring deterministic consistency and O(1) lookups for spatial queries.
