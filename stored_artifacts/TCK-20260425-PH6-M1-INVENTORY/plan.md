---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH6-M1-INVENTORY
artifact_type: plan
tags: [ph6, m1, inventory]
---

# PH6 M1: Inventory and Item Substrate

Implement the foundation for item management and authoritative inventory mutation.

## Proposed Changes

### [Core State] [MODIFY] [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- Define `ItemKind` enum (MATERIAL, CONSUMABLE, WEAPON, ARMOR, CURRENCY).
- Define `EquipSlot` enum.
- Implement `ItemStack` dataclass.
- Update `InventoryComponent`:
  - `items: List[ItemStack]`
  - `gold: int`
  - `max_slots: int`
  - `max_weight: float`
- Add `EquipmentComponent`:
  - `slots: Dict[EquipSlot, str | None]`

### [Item Registry] [NEW] [items.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/items.py)
- Implement `ItemDefinition` dataclass.
- Implement `ItemRegistry` class with static definitions for:
  - `iron_ore`, `wood`, `bread`, `healing_potion`, `iron_sword`, `leather_armor`.

### [Inventory Logic] [NEW] [inventory.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/inventory.py)
- Implement `InventoryService`:
  - `calculate_weight(inventory, registry)`
  - `can_add_item(inventory, item_id, quantity, registry)`
  - `can_equip_item(entity, item_id, slot, registry)`

### [State Updates] [MODIFY] [updates.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py)
- Add `InventoryUpdate`:
  - `items_add: List[ItemStack]`
  - `items_remove: List[ItemStack]`
  - `gold_delta: int`
- Add `EquipmentUpdate`:
  - `slot_updates: Dict[EquipSlot, str | None]`
- Update `EntityUpdate` to include these.

### [Apply Path] [MODIFY] [apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- Implement authoritative inventory merging (stacking, overflow prevention).
- Apply `gold_delta`.
- Apply `EquipmentUpdate`.

## Verification Plan

### Automated Tests
- `tests/inventory/test_item_inventory_contract.py`:
  - Verify item stacking (adding 5 iron + 5 iron = 1 stack of 10).
  - Verify slot limit enforcement (adding beyond `max_slots` fails).
  - Verify weight limit enforcement.
  - Verify gold transactions.
  - Verify equipment legality (cannot equip 'bread' as main hand).

### Manual Verification
- Trace `ApplyPath` logs during a mock loot transaction to ensure bit-identical state transitions.
