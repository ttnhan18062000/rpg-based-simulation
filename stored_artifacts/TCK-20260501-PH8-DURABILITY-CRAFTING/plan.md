---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260501-PH8-DURABILITY-CRAFTING
artifact_type: plan
tags: [ph8, durability, crafting]
---

# Plan - Phase 8 Durability and Crafting

## Objective
Implement durability and repair mechanics to complete the RPG equipment loop.

## Proposed Changes

### [MODIFY] [state.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/state.py)
- Update `EquipmentComponent` to include `durability: Dict[EquipSlot, float]`.
- Initialize durability when equipment is added (e.g. in `EvolutionSystem` or `EquipmentService`).

### [MODIFY] [updates.py](file:///home/vboxuser/Work/rpg-based-simulation/src/core/updates.py)
- Update `EquipmentUpdate` to include `durability_delta` and `durability_set`.

### [MODIFY] [combat.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/combat.py)
- Reduce durability of equipped items during combat resolution.
- Weapon durability decays on attack; Armor durability decays on being hit.

### [MODIFY] [blacksmith.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/blacksmith.py)
- Implement `REPAIR` action which restores durability for a gold cost.
- Logic should check if entity has enough gold.

### [MODIFY] [pipeline.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/pipeline.py)
- Ensure `EquipmentUpdate` is correctly applied.
- Integrate `REPAIR` action into the `TownResolutionSystem` or `BlacksmithSystem` enforce loop.

## Verification Plan
- Create `tests/rpg/test_durability_repair.py`.
- Test case: Equipment loses durability after combat.
- Test case: Broken equipment provides no stat bonus.
- Test case: Blacksmith repair restores durability.
- Test case: Repair fails if not enough gold.
