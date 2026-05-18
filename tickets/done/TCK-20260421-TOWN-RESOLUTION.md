# TCK-20260421-TOWN-RESOLUTION

## Title
Implement Town Resource Resolution (Milestone 2)

## Status
DONE

## Request Summary
Implement authoritative Shop and Blacksmith systems in V2 Engine to achieve bit-identical parity with V1 oracle.

## Scope
- Implement gold in InventoryComponent
- Implement IdentityComponent for recipes and craft targets
- Implement TownResolutionSystem (Passive Healing)
- Implement ShopSystem (Pricing & Sell-on-Entry)
- Implement BlacksmithSystem (Crafting & Recipe Learning)
- Verify bit-identical parity against V1 oracle

## Acceptance Criteria
- [x] All town resource deltas match V1 oracle (results.json)
- [x] Shop pricing is authoritative
- [x] Blacksmith crafting enforces "Law of Materials" and "Law of Knowledge"
- [x] State hash includes new town components

## Related Tickets
- None

## Related Docs
- src_overview.md
- src_principle.md

## Related Code Areas
- src/engine/town_resolution.py
- src/engine/shop.py
- src/engine/blacksmith.py
- src/core/state.py

## Implementation Notes
- Standardized all item keys to lowercase for parity.
- Separated passive laws (Healing) from active services (Shop/Blacksmith).

## Test Summary
- tests/parity/test_town_resolution_parity.py: 6/6 passed.

## Files Changed
- src/core/state.py
- src/core/updates.py
- src/engine/apply.py
- src/engine/town_resolution.py
- src/engine/shop.py
- src/engine/blacksmith.py
- src/engine/kernel.py
- src/engine/checkpoint.py

## Completion Summary
Milestone 2 core implementation is complete. All systems are integrated into the authoritative resolution phase and verified via parity testing.
