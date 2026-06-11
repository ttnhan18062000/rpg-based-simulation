---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260518-COMPONENT-PATCH-MODEL
artifact_type: plan
tags: [component, patch, model]
---

# Implementation Plan: Component-Level Patch Model

## Phase 1: Define `ComponentPatch` Hierarchy
Create `src/engine/patches.py`:
- Define abstract base class `ComponentPatch` with `domain: str`, `is_noop()`, `merge(other)`, `apply(entity, changes)`.
- Implement concrete patch classes for all update domains:
  - `KindPatch`
  - `LifecyclePatch`
  - `BiologicalPatch`
  - `InteractionPatch`
  - `IdentityPatch`
  - `NavigationPatch`
  - `CombatPatch`
  - `StaminaPatch`
  - `InventoryPatch`
  - `EquipmentPatch`
  - `StrategicPatch`
  - `QuestPatch`
  - `SocialPatch`
  - `TaskPatch`
  - `AttributePatch`
  - `RewardPatch`
  - `WoundPatch`
- Implement `extract_patches(entity_id: int, update: EntityUpdate) -> List[ComponentPatch]` in a specific order that respects derived stat dependencies.

## Phase 2: Refactor `_apply_entity_update_to_dict`
In `src/engine/apply.py`:
- In `_apply_entity_update_to_dict`, call `extract_patches(entity.id, update)` and iterate through the patches, calling `patch.apply(entity, changes)`.
- Maintain the derived stats dirty tracking and recalculation at the end of the method if stat-impacting patches (`AttributePatch`, `EquipmentPatch`, `IdentityPatch`, `WoundPatch`, `RewardPatch`) were applied.

## Phase 3: Unit and Integration Testing
- Create `tests/unit/optimization/test_component_patches.py` to test no-op, merge, and application for each patch type.
- Create `tests/integration/optimization/test_component_patch_apply_parity.py` to test full simulation pipeline parity.
