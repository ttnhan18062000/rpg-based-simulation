---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260425-PH6-M3-HARVEST
artifact_type: plan
tags: [ph6, m3, harvest]
---

# PH6 M3: Harvesting and Resource Nodes

Implement deterministic channeled harvesting and resource node lifecycle.

## Proposed Changes

### [Harvest Action] [NEW] [harvest.py](file:///home/vboxuser/Work/rpg-based-simulation/src/actions/harvest.py)
- Implement `HarvestAction.start(entity, target_id, state)`:
  - Validates proximity (< 1.5 tiles).
  - Validates node has charges.
  - Sets `InteractionComponent(target_id=target_id, progress=0, required_ticks=X)` where X depends on node kind.

### [Harvest System] [NEW] [harvest_system.py](file:///home/vboxuser/Work/rpg-based-simulation/src/systems/harvest_system.py)
- Implement `HarvestSystem.update(state)`:
  - Identifies entities with harvesting progress.
  - On progress == required_ticks:
    - Finds target node.
    - Emits `InventoryUpdate` (add yield).
    - Emits `ResourceNodeUpdate` (decrement charges).
    - Resets interaction.
  - Handles node respawn cooldowns (decrement `cooldown_remaining` each tick).

### [Resource Node Lifecycle] [MODIFY] [apply.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/apply.py)
- Ensure `ResourceNodeUpdate` handles `cooldown_remaining` and `charges` correctly. (Already mostly there, but verify).

## Verification Plan

### Automated Tests
- `tests/inventory/test_harvest_channeling.py`:
  - Verify harvesting wood takes 10 ticks.
  - Verify harvesting iron takes 20 ticks.
  - Verify node charges decrement.
  - Verify node enters cooldown when empty.
  - Verify harvesting is interrupted if entity moves.

### Manual Verification
- Visual audit of state advancement logs to ensure no yield duplication.
