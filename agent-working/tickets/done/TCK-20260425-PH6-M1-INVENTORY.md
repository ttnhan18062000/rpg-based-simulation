---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260425-PH6-M1-INVENTORY
phase: done
date: 2026-04-25
tags: [ph6, m1, inventory]
---

# TCK-20260425-PH6-M1-INVENTORY

## Title

Implementation of Inventory Model and Item Contracts

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Establish the foundation for item management. This includes the item registry, inventory constraints (slots/weight), and authoritative mutation paths for items and gold.

## Scope

- Implement `ItemRegistry` and core item definitions.
- Implement `InventoryComponent` and `EquipmentComponent`.
- Create `InventoryUpdate` and `EquipmentUpdate` structures.
- Update `ApplyPath` to handle authoritative inventory transitions.
- Add contract tests for inventory limits and stacking.

## Out of Scope

- Channeled looting (Task 6.2).
- Shopkeeper trading logic (Task 6.5).

## Acceptance Criteria

- [x] Item stacking works correctly (quantities merge).
- [x] Adding items beyond `max_slots` is rejected by the system.
- [x] Weight is calculated accurately from `ItemRegistry`.
- [x] Gold transactions are authoritative and persistent.
- [x] Weapons can be equipped to valid slots.
- [x] All tests in `tests/inventory/test_item_inventory_contract.py` pass.

## Related Tickets

- TCK-20260425-PH5-M2-PERSONALITY (Done)

## Related Docs

- resource_v2_e_phases.md

## Related Code Areas

- src/core/state.py
- src/core/updates.py
- src/engine/apply.py
- src/core/inventory.py
- src/core/items.py

## Implementation Notes

- Inventory mutation is handled by `InventoryService.apply_update` within `ApplyPath`.
- Removed redundant legacy `InventoryUpdate` definition from `updates.py`.

## Test Summary

- `tests/inventory/test_item_inventory_contract.py`:
  - `test_inventory_stacking`: PASS
  - `test_inventory_capacity_limits`: PASS
  - `test_equipment_and_gold_updates`: PASS

## Files Changed

- src/core/state.py
- src/core/updates.py
- src/engine/apply.py
- src/core/inventory.py [NEW]
- src/core/items.py [NEW]

## Completion Summary

Phase 6 Milestone 1 is complete. The system now has a robust, transactional substrate for item management, ensuring that all inventory changes are authoritative and subject to physical constraints (weight/slots).
