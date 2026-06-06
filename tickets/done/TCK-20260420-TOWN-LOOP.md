# TCK-20260420-TOWN-LOOP

## Title
Town-Driven Resource Resolution (Material Handback)

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement the 'Town Loop' where entities on Town tiles convert their harvested materials into Gold or secondary resources. This recovers the original RPG-core resolution cycle.

## Scope
- Implement `TownResolutionSystem` to detect entities on town tiles.
- Define `ITEM_PRICES` (e.g., WOOD=10 GOLD, ORE=25 GOLD).
- Update `AuthoritativeState` to include `town_tiles`.
- Integrate into `Kernel._phase_resolution`.

## Acceptance Criteria
- [ ] Entities on a town tile have their materials removed.
- [ ] Equivalent `GOLD` is added to the entity's inventory or global state (Parity with src).
- [ ] No gold awarded if the entity is not on a town tile.

## Files Changed
- `src/core/state.py` (Add town_tiles)
- `src/engine/town_resolution.py` [NEW]
- `src/engine/kernel.py` (Wiring)
