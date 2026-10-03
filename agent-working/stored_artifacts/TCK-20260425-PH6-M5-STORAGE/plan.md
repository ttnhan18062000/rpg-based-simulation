---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH6-M5-STORAGE
artifact_type: plan
tags: [ph6, m5, storage]
---

# PH6 M5: Equipment, Chests, and Storage

Implement advanced gear management and persistent world storage.

## Proposed Changes

### [World State] [MODIFY] [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- Add `ChestState` model.
- Add `chests` and `home_storage` fields to `AuthoritativeState`.

### [Equipment Logic] [NEW] [equipment.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/equipment.py)
- Implement `EquipmentService.rank_item(item, class_kind)`.
- Implement `EquipmentService.auto_equip(entity) -> EquipmentUpdate`.

### [Storage Action] [NEW] [home_storage.py](file:///home/vboxuser/Work/rpg-based-simulation/src/town/home_storage.py)
- Implement `HomeStorageAction.deposit` and `HomeStorageAction.withdraw`.
- Ensure authoritative atomic transfer.

### [Verification Plan]

#### Automated Tests
- `tests/inventory/test_equipment_chests_storage.py`:
  - Verify auto-equip chooses higher `atk_bonus`.
  - Verify chests provide loot and enter cooldown.
  - Verify home storage preserves items and respects capacity.

#### Manual Verification
- Snapshot audit of global state to ensure home storage remains consistent across ticks.
