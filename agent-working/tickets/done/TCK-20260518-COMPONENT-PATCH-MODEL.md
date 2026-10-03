---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260518-COMPONENT-PATCH-MODEL
phase: done
date: 2026-05-18
tags: [component, patch, model]
---

# TCK-20260518-COMPONENT-PATCH-MODEL

## Title

Milestone 15: Component-Level Patch Model

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Transition state update mechanics from monolithic EntityUpdate objects toward component-specific patches (`ComponentPatch`).

## Scope

- Create `src/engine/patches.py` defining the `ComponentPatch` hierarchy (`NavigationPatch`, `CombatPatch`, `InventoryPatch`, `StrategicPatch`, `BiologicalPatch`, `LifecyclePatch`, `IdentityPatch`, `EquipmentPatch`, `StaminaPatch`, `WoundPatch`, `SocialPatch`, `TaskPatch`, `InteractionPatch`, `AttributePatch`).
- Implement no-op detection and merge logic for each patch type.
- Implement patch application logic (`apply`) that cleanly transforms components.
- Integrate `ComponentPatch` into `ApplyPath._apply_entity_update_to_dict` as an internal ApplyPath optimization.
- Ensure order-sensitive patch application (e.g. attributes/equipment/identity before combat derived stats recalculation).
- Implement unit tests and integration parity tests.

## Out of Scope

- Changes to authoritative game rules or simulation mechanics.
- External API changes (proposals can still produce `EntityUpdate` or updates can be converted internally).

## Acceptance Criteria

- [x] Each patch type can detect no-op.
- [x] Each patch type can merge compatible patches.
- [x] Patch application equals old EntityUpdate application.
- [x] Order-sensitive patches are protected.

## Related Tickets

- TCK-20260518-APPLY-PATH-REDESIGN

## Related Docs

- perf_plan_v2.md
- docs/engine/authoritative_apply_contract.md

## Related Stored Artifacts

- stored_artifacts/TCK-20260518-COMPONENT-PATCH-MODEL/

## Related Code Areas

- `src/engine/patches.py`
- `src/engine/apply.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- Implemented `ComponentPatch` abstract base class and 17 concrete component patch classes.
- Inside `extract_patches(entity_id, update)`, monolithic `EntityUpdate` objects are cleanly decomposed into non-noop component patches.
- Fixed dependency order enforced: `KindPatch`, `IdentityPatch`, `EquipmentPatch`, `WoundPatch`, etc., are evaluated before combat derived stats.
- `_apply_entity_update_to_dict` in `ApplyPath` refactored to execute `patch.apply(entity, changes)` sequentially, eliminating massive nested conditional blocks while maintaining dirty tracking and derived stats recalculation.

## Test Summary

- `tests/unit/optimization/test_component_patches.py` (Passed)
- `tests/integration/optimization/test_component_patch_apply_parity.py` (Passed)
- All 67 optimization unit tests and 9 integration tests passed successfully.
- REST parity test suite passed cleanly.

## Files Changed

- `src/engine/patches.py` (NEW)
- `src/engine/apply.py` (MODIFY)
- `docs/engine/authoritative_apply_contract.md` (MODIFY)
- `tests/unit/optimization/test_component_patches.py` (NEW)
- `tests/integration/optimization/test_component_patch_apply_parity.py` (NEW)

## Completion Summary

- Milestone 15 completed successfully. State update application now operates via highly modular, encapsulated component-level patches with 100% semantic parity and robust dependency ordering.
