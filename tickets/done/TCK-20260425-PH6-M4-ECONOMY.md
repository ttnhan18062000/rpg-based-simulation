# TCK-20260425-PH6-M4-ECONOMY

## Title

Implementation of Town Economy and Crafting Services

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement deterministic shopping and crafting services. Establish the recipe substrate and ensure authoritative exchange of items and gold.

## Scope

- Implement `RecipeRegistry` and core crafting recipes.
- Implement `ShopAction` for buying and selling items.
- Implement `BlacksmithAction` for item crafting.
- Add contract tests for economic transactions.

## Out of Scope

- Repair durability mechanics (deferred to later M).
- Complex auction houses.

## Acceptance Criteria

- [x] Shop correctly validates gold before allowing purchase.
- [x] Crafting consumes all required materials and gold.
- [x] Selling items returns half their base value in gold.
- [x] All transactions are authoritative and subject to inventory capacity.
- [x] All tests in \`tests/town/test_economy_contract.py\` pass.

## Related Tickets

- TCK-20260425-PH6-M3-HARVEST (Done)

## Related Docs

- resource_v2_e_phases.md

## Related Code Areas

- src/core/recipes.py [NEW]
- src/town/shop.py [NEW]
- src/town/blacksmith.py [NEW]
- src/core/inventory.py

## Implementation Notes

- Used \`InventoryUpdate\` for all economic transfers.
- Sell value is hardcoded to 50% of base value.
- Crafting requires ingredients and gold to be present in inventory.

## Test Summary

- \`tests/town/test_economy_contract.py\`:
  - \`test_shop_buy_and_sell\`: PASS
  - \`test_blacksmith_crafting\`: PASS

## Files Changed

- src/core/recipes.py [NEW]
- src/town/shop.py [NEW]
- src/town/blacksmith.py [NEW]

## Completion Summary

Phase 6 Milestone 4 is complete. The system now supports deterministic, authoritative economic interactions including shopping and crafting, backed by a formal recipe registry.
