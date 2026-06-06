# TCK-20260503-TERRAIN-WEIGHT-AUTHORITY

## Title
Enforcing Authoritative Movement Costs (Terrain Weighting)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Integrate terrain-based movement costs into the authoritative legality matrix to prevent entities from ignoring difficult terrain.

## Scope
- Integrate `get_tile_cost` logic into the authoritative movement refinement.
- Enforce `Readiness` penalties based on terrain type (e.g., MOUNTAIN = 2x cost).
- Ensure the engine rejects movement intents if the entity lacks the Readiness required for the specific terrain cost.

## Out of Scope
- Modifying A* pathfinding weights (this is a separate "Optimization" task).
- Adding new terrain types.

## Acceptance Criteria
- [ ] Entities moving through MOUNTAIN tiles must expend significantly more Readiness than on PLAIN tiles.
- [ ] The Kernel must reject movement intents if the entity lacks the Readiness required for the specific terrain cost.

## Related Tickets
- TCK-20260503-PHANTOM-LEADER-HARDENING

## Related Code Areas
- src/engine/legality.py
- src/engine/movement.py
- src/core/state.py

## Assumptions / Open Questions
- Assume terrain data is accessible via `state.terrain_tiles`.
- What is the exact mapping of terrain to cost? (e.g. PLAIN=1.0, FOREST=1.5, MOUNTAIN=2.0).

## Implementation Notes
- Use `AuthoritativeApplyPipeline._resolve_occupancy_conflicts` or a dedicated movement legality method in `pipeline.py`.

## Test Summary
- TBD

## Files Changed
- TBD

## Completion Summary
- TBD
