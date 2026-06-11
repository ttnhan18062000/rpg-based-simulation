---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260506-INVENTORY-TEST-STABILIZATION
artifact_type: plan
tags: [inventory, test, stabilization]
---

# Implementation Plan - Inventory Test Stabilization

Migrate `tests/inventory/` to `V2EntityBuilder` to resolve `TypeError` regressions.

## Proposed Changes

### Tests Migration

#### [MODIFY] [test_equipment_chests_storage.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/inventory/test_equipment_chests_storage.py)
#### [MODIFY] [test_equipment_ranking.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/inventory/test_equipment_ranking.py)
#### [MODIFY] [test_harvest_channeling.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/inventory/test_harvest_channeling.py)
#### [MODIFY] [test_inventory_hardening.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/inventory/test_inventory_hardening.py)
#### [MODIFY] [test_item_inventory_contract.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/inventory/test_item_inventory_contract.py)
#### [MODIFY] [test_loot_channeling.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/inventory/test_loot_channeling.py)

## Verification Plan

### Automated Tests
- `pytest tests/inventory -vv --tb=short`
