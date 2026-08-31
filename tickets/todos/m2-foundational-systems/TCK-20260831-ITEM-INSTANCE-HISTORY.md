---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260831-ITEM-INSTANCE-HISTORY
phase: open
date: 2026-08-31
tags: [resource]
---

# TCK-20260831-ITEM-INSTANCE-HISTORY

## Title
Possessions With Personal History (ItemInstance ownership tracking)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Possessions With Personal History — the highest design-uncertainty ticket in this batch, with no precedent anywhere in the codebase. ItemStack is item_id+quantity only, and InventoryService.apply_update actively merges same-item_id stacks by mutating quantity, meaning any per-instance data bolted onto ItemStack today would be silently destroyed on the next merge. No test file anywhere references instance_id/ItemInstance/per-item ownership history.

## Scope
- Add a new ItemInstance durable record (instance_id, item_id, owner_history: List[str], acquired_tick, acquired_method: enum{LOOT,CRAFTED,GIFT,INHERITED}) with a defined typed state location, NOT stored in ItemStack.properties or any untyped dict.
- Route only items explicitly flagged significant at creation through ItemInstance tracking; all other items continue through the unmodified ItemStack merge path, and existing test_inventory_stacking() must pass unmodified.
- Transferring a significant item appends the new owner to owner_history via a typed StateUpdate through the authoritative apply pipeline only.
- Re-verify TOWN-128 parity entry (item identity/kind preserved through pickup/stacking/selling/crafting/dropping) as unaffected, or add a new adjacent entry distinguishing item_id-identity from instance_id-uniqueness.
- Flag significance_flag's trigger criteria as an explicit open design decision requiring sign-off before implementation — do not invent criteria ad hoc.

## Out of Scope
- src/domains/progression/possession.py's PossessionUnderstandingService — a same-named but unrelated concept (subjective reward meaning for progression conversion); do not conflate with this ticket's physical per-instance identity.
- Any change to the existing ItemStack merge-by-item_id behavior for non-significant items — must remain unmodified.

## Acceptance Criteria
- [ ] A new ItemInstance durable record (instance_id, item_id, owner_history, acquired_tick, acquired_method) exists with a defined typed state location, NOT stored in ItemStack.properties or any untyped dict.
- [ ] Only items explicitly flagged significant at creation receive an ItemInstance — all other items continue through the unmodified ItemStack merge path, and existing test_inventory_stacking() passes unmodified.
- [ ] Transferring a significant item appends the new owner to owner_history via a typed StateUpdate through the authoritative apply pipeline only.
- [ ] TOWN-128 parity entry is re-verified as unaffected or a new adjacent entry is added distinguishing item_id-identity from instance_id-uniqueness.
- [ ] Ticket explicitly flags significance_flag's trigger criteria as an open design decision requiring sign-off before implementation, not invented ad hoc.

## Related Tickets
None.

## Related Docs
- docs/parity_ledger/town_resource.yaml
- docs/brainstorm/rpg_expected_schemas.html

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/models/inventory.py
- src/core/inventory.py
- src/core/update_models/inventory.py
- src/core/state.py

## Assumptions / Open Questions
- significance_flag's trigger criteria is explicitly marked an open question in the schema doc — cannot be scoped without a design decision first, must not be invented ad hoc.
- Flagged as the batch's largest/riskiest ticket — recommend design review before implementation starts.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
