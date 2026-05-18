# Implementation Plan: Phase 3 Resource Conservation

## Goal Description
Implement the "Resource Conservation" law across `HarvestSystem` and `LootSystem`. This ensures that resource nodes, ground items, and corpses are only consumed/removed if the entity can successfully receive the items into their inventory.

## Proposed Changes

### [Component Name] Resource Conservation Logic

#### [NEW] [ResourceConservationService](file:///home/vboxuser/Work/rpg-based-simulation/src/core/conservation.py)
- Create a service to centralize conservation checks.
- Method `check_capacity(entity_inventory, items_to_add) -> bool`.
- Method `atomic_transfer_possible(state, entity_id, items_to_add) -> bool`.

#### [MODIFY] [HarvestSystem](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/harvest_system.py)
- Import `InventoryService` (or `ResourceConservationService`).
- Add capacity check before emitting `ResourceNodeUpdate` and `InventoryUpdate`.
- If capacity is insufficient, reset interaction and skip node depletion.

#### [MODIFY] [LootSystem](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/loot_system.py)
- Add capacity check before emitting `InventoryUpdate` and adding targets to removal lists.
- If capacity is insufficient, reset interaction and skip target removal.

#### [MODIFY] [InventoryService](file:///home/vboxuser/Work/rpg-based-simulation/src/core/inventory.py)
- Ensure `can_add_item` and `can_add_items` are robust and used correctly by the systems.

## Verification Plan

### Automated Tests
- Port and run `tests/rpg/test_resource_conservation.py`.
- Run existing inventory and channeling tests.

### Manual Verification
- None (Automated tests should cover all logic).
