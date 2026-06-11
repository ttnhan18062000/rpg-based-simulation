---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260427-RESOURCE-CONSERVATION-HARDENING
phase: done
date: 2026-04-27
tags: [resource, conservation, hardening]
---

# TCK-20260427-RESOURCE-CONSERVATION-HARDENING

## Title

Hardening Resource Conservation Law (Phase 3.1)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement and verify the "Resource, Inventory, and Interaction Conservation" law (Phase 3 of `resource_v2_e2_phases.md`). This involves ensuring that items are never lost or duplicated during harvest, loot, pickup, and crafting, and that capacity limits are strictly enforced BEFORE world depletion.

## Scope

- Audit `HarvestSystem` and `LootSystem` for capacity check enforcement.
- Implement missing capacity checks in `HarvestSystem` and `LootSystem` using `InventoryService`.
- Ensure atomic transfer: if inventory cannot accept item, source (node, corpse, ground item) must not be depleted/removed.
- Update `logic_checklist_exhaustive.md` to reflect true status of TOWN-011 and TOWN-012 if they were false-green.
- Add regression tests to prove conservation.

## Out of Scope

- Shop transaction law (TOWN-016) - will be handled in a separate ticket.
- Crafting consume/produce law (TOWN-017) - will be handled in a separate ticket.

## Acceptance Criteria

- [x] `HarvestSystem` checks capacity before depleting node. (VIA INTENT)
- [x] `LootSystem` checks capacity before removing corpse/ground item. (VIA INTENT)
- [x] Items are NOT removed from the world if inventory is full.
- [x] Tests prove no item loss when inventory is full.
- [x] `logic_checklist_exhaustive.md` reflects the implemented changes.

## Related Tickets

- None

## Related Docs

- [resource_v2_e2_phases.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_v2_e2_phases.md)
- [logic_checklist_exhaustive.md](file:///home/vboxuser/Work/rpg-based-simulation/logic_checklist_exhaustive.md)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/systems/harvest_system.py`
- `src/systems/loot_system.py`
- `src/core/conservation.py`
- `src/engine/interaction.py`
- `src/core/updates.py`

## Assumptions / Open Questions

- Does `InventoryService.can_add_item` correctly account for both slots and weight? (Yes, verified in code).
- Should we use a unified `ResourceConservationService` as suggested in `resource_v2_e2_phases.md`? (Implemented as `ResourceTransactionResolver`).

## Implementation Notes

- Introduced `ResourceTransferIntent` to unify proposed transfers.
- Created `ResourceTransactionResolver` as the authoritative arbiter of transfers.
- Refactored `HarvestSystem` and `LootSystem` to emit intents.
- Hardened `InteractionSystem.enforce` to ensure all-or-nothing resolution.

## Test Summary

- [x] `tests/systems/test_resource_conservation_regression.py` (4 tests passed)
- Proven: Harvest node with full inventory -> Node charge preserved.
- Proven: Loot corpse with full inventory -> Corpse preserved.
- Proven: Pickup ground item with full inventory -> Ground item preserved.
- Proven: Explicit intent resolution for valid transfers.

## Files Changed

- `src/core/updates.py`
- `src/core/conservation.py`
- `src/engine/interaction.py`
- `src/systems/harvest_system.py`
- `src/systems/loot_system.py`
- `tests/systems/test_resource_conservation_regression.py`

## Completion Summary

Successfully hardened the Resource Conservation Law by introducing an intent-based transaction architecture. This eliminates the "split-brain" authority issue where systems could deplete world resources even if the actor's inventory was full. The solution is fully backed by regression tests and aligns with the V2 engine's refinement pipeline.
