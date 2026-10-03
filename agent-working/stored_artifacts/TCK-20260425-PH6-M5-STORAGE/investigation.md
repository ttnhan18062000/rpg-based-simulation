---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260425-PH6-M5-STORAGE
artifact_type: investigation
tags: [ph6, m5, storage]
---

# Investigation — PH6 M5: Equipment, Chests, and Storage

## Goal
Implement advanced inventory management: automated gear selection, world-object chests, and persistent home storage.

## Requirements
- **Equipment Ranking**: Logic to compare two items (e.g., `iron_sword` vs `wood_sword`) and decide which is better for a specific class.
- **Treasure Chests**: Authoritative world objects with loot tables and respawn timers.
- **Home Storage**: A new domain in `AuthoritativeState` for storing items outside of entity inventories.

## Proposed Architecture

### 1. Equipment Service (`core/equipment.py`)
- `EquipmentService.is_better(item_a, item_b, class_context)`:
  - Compares properties like `atk_bonus`, `def_bonus`.
- `EquipmentService.auto_equip(entity, state)`:
  - Scans inventory for better gear and generates `EquipmentUpdate`.

### 2. Chest Model (`state.py`)
- `ChestState`: `id: int`, `position: tuple[float, float]`, `loot_table_id: str`, `remaining_loot: List[ItemStack]`, `respawn_tick: int`.
- Integration into `ApplyPath`.

### 3. Home Storage Service (`town/home_storage.py`)
- `HomeStorageAction.deposit/withdraw(entity, item_id, qty, state)`:
  - Atomic transfer between `entity.inventory` and `state.home_storage[entity.id]`.

### 4. Authoritative State Update
- Add `home_storage: Dict[int, InventoryComponent]` to `AuthoritativeState`.
- Add `chests: Dict[int, ChestState]` to `AuthoritativeState`.

## Questions
- Do chests respawn?
  Roadmap says "chests have availability and respawn tick".
- How is gear power calculated?
  Weighted sum of relevant properties (e.g., for Warrior: `atk_bonus` * 1.0 + `def_bonus` * 0.5).
