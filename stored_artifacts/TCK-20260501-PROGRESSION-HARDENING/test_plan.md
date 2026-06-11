---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260501-PROGRESSION-HARDENING
artifact_type: test_plan
tags: [progression, hardening]
---

# Test Plan: Phase E4.5 Progression Hardening

## Unit Tests
- `src/progression/leveling.py`:
    - `test_xp_overflow`: Verify leveling up when XP exceeds threshold.
    - `test_xp_reward_separation`: Verify XP is granted even if `ItemTransaction` fails.
- `src/core/equipment_service.py`:
    - `test_durability_degradation`: Verify combat hits reduce durability.
    - `test_repair_transaction`: Verify gold is consumed and durability restored.

## Integration Tests
- `src/systems/crafting.py`:
    - `test_crafting_materials_consumption`: Verify all materials are removed on success.
    - `test_crafting_recipe_gate`: Verify rejection for unknown recipes.

## Lifecycle Tests
- `tests/engine/test_progression_lifecycle.py`:
    - **Scenario 1**: Combat Victory -> XP Gain -> Level Up -> Skill Unlock -> Attribute Allocation.
    - **Scenario 2**: Equipment Wear -> Efficiency Drop -> Repair Trip -> Resource Drain.
    - **Scenario 3**: Gathering -> Crafting Attempt -> Material Depletion -> New Item in Inventory.
