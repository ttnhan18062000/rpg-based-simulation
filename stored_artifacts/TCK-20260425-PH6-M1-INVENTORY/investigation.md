# Investigation — PH6 M1: Inventory and Item Substrate

## Goal
Implement a typed, transactional item and inventory system that enforces slot and weight constraints authoritatively.

## Current State
- `InventoryComponent` exists in `state.py` but is a placeholder (L143).
- No unified item model or registry exists.
- `ResourceNodeState` and `BuildingState` exist but don't yet produce/consume real items.

## Proposed Architecture

### 1. Item Model (`items.py`)
Items should be immutable data records:
- `id`: str (template ID, e.g. 'iron_ore')
- `name`: str
- `kind`: Enum (CONSUMABLE, WEAPON, ARMOR, MATERIAL, CURRENCY)
- `weight`: float
- `stack_size`: int
- `value`: int (Gold)
- `properties`: Dict[str, Any] (e.g. `atk_bonus`, `heal_amount`)

### 2. Item Registry
A static registry mapping template IDs to `ItemDefinition` objects.

### 3. Inventory Component (`inventory.py` / `state.py`)
- `slots: List[ItemStack]`
- `max_slots: int`
- `max_weight: float`
- `gold: int`

### 4. Item Stack
- `item_id`: str
- `quantity`: int

### 5. Equipment Component
- `slots: Dict[EquipSlot, str | None]` (Head, Torso, Legs, MainHand, OffHand)

## Updating the Ledger
Inventory mutation must be transactional. 
We need `InventoryUpdate` in `updates.py`:
- `items_add: List[ItemStack]`
- `items_remove: List[ItemStack]`
- `gold_delta: int`
- `equipment_set: Dict[EquipSlot, str | None]`

## Questions
- Should "Gold" be a special currency field or just an item stack?
  Legacy used a special field for speed, but V2 should probably treat it as currency field in `InventoryComponent` for convenience in shop resolution.
- How to handle unique items?
  Unique items (e.g. 'Sword of Heroes') should have an instance ID. For now, we will focus on stackable template-based items.
