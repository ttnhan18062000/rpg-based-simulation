# Investigation — PH6 M2: Channeled Loot and Corpse Recovery

## Goal
Implement a deterministic looting system where retrieving items from the world takes time, requires proximity, and ensures no item duplication through authoritative state transitions.

## Requirements
- **Looting as a Channel**: Looting shouldn't be instant. It needs `InteractionComponent` progress.
- **Authoritative World Objects**: Ground items and corpses must have unique IDs and be tracked in `AuthoritativeState`.
- **No Duplication**: The item must be removed from the world in the SAME tick it is added to the inventory.
- **Interruption**: Moving or taking damage should cancel the loot progress.

## Proposed Architecture

### 1. Ground Item / Corpse Model (`state.py`)
- `GroundItemState`: `id: int`, `item_id: str`, `quantity: int`, `position: tuple[float, float]`.
- `CorpseState` (already exists in some form?): Needs to track items.

### 2. Loot Action (`actions/loot.py`)
- Validates proximity.
- Initializes `InteractionComponent` with `target_id` and `required_ticks`.

### 3. Loot System (`systems/loot_system.py`)
- Increments progress each tick.
- On completion:
  - Generates `InventoryUpdate` (add item).
  - Generates `WorldUpdate` (remove ground item).

### 4. Apply Path Integration
- Ensure `WorldUpdate` handles ground item removal bit-identically.

## Questions
- Should corpses be separate entities or just a type of world object?
  In V2, we prefer treating them as `WorldObject` (like resource nodes) for simple interaction.
- What is the standard looting time?
  Default 10 ticks (0.5s at 20Hz).
