# TCK-20260503-TERRAIN-WEIGHT-AUTHORITY

## Title
Enforcing Authoritative Movement Costs (Terrain Weighting)

## Status
OPEN

## Request Summary
Integrate terrain-based movement costs into the authoritative legality matrix to prevent entities from ignoring difficult terrain.

## Scope
- Integrate `get_tile_cost` from `Community 11` into `LegalityServiceV2.verify_occupancy` or a new `MovementLegality` phase.
- Enforce `Readiness` penalties based on terrain type (e.g., MOUNTAIN = 2x cost).

## Acceptance Criteria
- [ ] Entities moving through MOUNTAIN tiles must expend significantly more Readiness than on PLAIN tiles.
- [ ] The Kernel must reject movement intents if the entity lacks the Readiness required for the specific terrain cost.

## Related Code Areas
- src/engine/legality.py
- src/engine/movement.py
- src/core/state.py (Terrain definitions)
