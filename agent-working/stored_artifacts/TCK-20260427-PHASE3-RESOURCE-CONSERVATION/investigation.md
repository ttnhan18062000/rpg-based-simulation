---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260427-PHASE3-RESOURCE-CONSERVATION
artifact_type: investigation
tags: [phase3, resource, conservation]
---

# Investigation: Phase 3 Resource Conservation Violations

## Current Behavior Analysis

### HarvestSystem
- `HarvestSystem.update` calculates progress and, upon completion, generates `InventoryUpdate` (to add items) and `ResourceNodeUpdate` (to decrement charges).
- It does **not** check if the entity's inventory has capacity for the item.
- Result: Node is depleted, but if inventory is full, `InventoryService.apply_update` (called in `ApplyPath`) silently drops the item.
- **Violation**: Resource charge consumed without reward.

### LootSystem
- `LootSystem.update` processes ground items and corpses.
- Upon completion, it generates `InventoryUpdate` and adds the target to `ground_items_remove` or `corpses_remove`.
- It does **not** check capacity.
- Result: Ground item/corpse disappears from the world, but if inventory is full, items are dropped.
- **Violation**: Item loss / vanishing.

## Legacy Comparison
- `tests_legacy/rpg/test_resource_conservation.py` confirms that legacy behavior required checking capacity to prevent node depletion.
- `src_legacy/systems/harvest_system.py` (assumed, will check next) likely performed this check.

## Proposed Solution: `ResourceConservationService`
- Need a central service that can:
    1. Check if a set of updates (Inventory + Node/Ground/Corpse) is valid as a whole.
    2. Provide a helper for systems to check capacity before emitting updates.

## Technical Constraint: `StateUpdate` Atomicity
- The current `ApplyPath` applies updates per-domain (entities, then nodes, etc.).
- While it's "atomic" in the sense that it produces a new state, it's not "transactional" across domains if one part of a system's intent (add item) fails but another (deplete node) succeeds.
- Systems should only emit intents that are valid.
