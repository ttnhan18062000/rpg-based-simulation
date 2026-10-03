---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260506-INVENTORY-TEST-STABILIZATION
artifact_type: test_plan
tags: [inventory, test, stabilization]
---

# Test Plan - Inventory Test Stabilization

## Strategy

1. Run all tests in `tests/inventory/` to confirm baseline failures.
2. For each test file:
    - Replace `EntityState(...)` with `V2EntityBuilder(id).kind(kind).at(pos)...build()`.
    - Run the specific test file to verify the fix.
3. Final pass: Run all tests in `tests/inventory/`.

## Tests

- [x] `test_equipment_chests_storage.py`
- [x] `test_equipment_ranking.py`
- [x] `test_harvest_channeling.py`
- [x] `test_inventory_hardening.py`
- [x] `test_item_inventory_contract.py`
- [x] `test_loot_channeling.py`
