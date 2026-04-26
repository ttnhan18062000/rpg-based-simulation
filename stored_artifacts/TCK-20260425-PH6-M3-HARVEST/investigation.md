# Investigation — PH6 M3: Harvesting and Resource Nodes

## Goal
Implement a deterministic harvesting system where extracting resources from nodes takes time, requires proximity, and produces yields through the authoritative mutation path.

## Requirements
- **Harvesting as a Channel**: Similar to looting, harvesting needs `InteractionComponent` progress.
- **Authoritative Nodes**: `ResourceNodeState` must track `charges` and `cooldown_remaining`.
- **Deterministic Yields**: Yields must be determined authoritatively (using a seed if random, but for M3 we can use fixed yields or simple logic).
- **Depletion**: Nodes must become inactive when charges reach zero and enter a cooldown period.

## Proposed Architecture

### 1. Resource Node Model (`state.py`)
- `ResourceNodeState` (already exists):
  - `id: int`, `kind: str`, `position: tuple[float, float]`, `charges: int`, `max_charges: int`, `respawn_cooldown: int`, `cooldown_remaining: int`.

### 2. Harvest Action (`actions/harvest.py`)
- Validates proximity (< 1.5 tiles).
- Initializes `InteractionComponent` with `target_id` and `required_ticks`.

### 3. Harvest System (`systems/harvest_system.py`)
- Increments progress each tick.
- On completion:
  - Generates `InventoryUpdate` (add items like `iron_ore` or `wood`).
  - Generates `ResourceNodeUpdate` (decrement charges).
  - Resets interaction.

### 4. Apply Path Integration
- Already has `ResourceNodeUpdate` support.

## Questions
- What are the default harvest times?
  Varies by resource? (e.g. wood 10 ticks, iron 20 ticks).
- What determines the yield?
  Fixed for now based on node kind (e.g. Iron Node -> 1 Iron Ore).
