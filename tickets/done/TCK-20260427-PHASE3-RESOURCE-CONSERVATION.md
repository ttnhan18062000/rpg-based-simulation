# TCK-20260427-PHASE3-RESOURCE-CONSERVATION

## Title

Implement Authoritative Resource Conservation (Phase 3)

## Status

DONE

## Request Summary

Implement the missing RPG-core logic for resource, inventory, and interaction conservation as defined in Phase 3 of `resource_v2_e2_phases.md`. Ensure that items do not vanish and resource nodes/corpses are not depleted if the inventory cannot accept the rewards.

## Scope

- Implement `ResourceConservationService` (as `ResourceTransactionResolver`) to unify capacity checks.
- Refactor `HarvestSystem` to obey conservation laws.
- Refactor `LootSystem` to obey conservation laws.
- Implement conservation for ground pickup, crafting, and shop transactions (if applicable).
- Ensure all transfer operations are atomic and capacity-aware.

## Out of Scope

- Refactoring systems outside of resource/inventory (e.g., Combat, Movement) unless necessary for integration.
- UI changes for inventory management.

## Acceptance Criteria

- [x] `HarvestSystem` does not deplete charges if inventory is full.
- [x] `LootSystem` does not remove ground items if inventory is full.
- [x] `LootSystem` does not remove corpses if inventory is full.
- [x] All resource transfers are verified against `InventoryService.can_add_items`.
- [x] `ResourceConservationService` is used consistently across systems.
- [x] Tests verify that items are NOT lost when inventory limits are hit.

## Related Tickets

- None

## Related Docs

- [resource_v2_e2_phases.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_v2_e2_phases.md)
- [logic_checklist_exhaustive.md](file:///home/vboxuser/Work/rpg-based-simulation/logic_checklist_exhaustive.md)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/inventory.py`
- `src/core/conservation.py`
- `src/engine/interaction.py`
- `src/engine/pipeline.py`

## Assumptions / Open Questions

- Resolved: Resource transactions are all-or-nothing per intent.

## Implementation Notes

- Implemented `ResourceTransactionResolver.resolve` to handle atomic multi-step transfers.
- Hardened `InteractionSystem` and `AuthoritativeApplyPipeline` to check capacity against the "pending" inventory state (tick-wide state + queued updates).
- Moved Quest rewards to the refinement phase for capacity awareness.

## Test Summary

- `tests/rpg/test_resource_conservation_v2.py`: Proves that node depletion is blocked when inventory is full.
- Full RPG suite (100% green).

## Files Changed

- `src/core/inventory.py`
- `src/core/conservation.py`
- `src/core/updates.py`
- `src/engine/interaction.py`
- `src/engine/pipeline.py`
- `src/engine/quests.py`
- `src/engine/apply.py`

## Completion Summary

- Successfully implemented Phase 3 Resource Conservation. 
- The V2 engine now strictly obeys the law: "No source depletion without successful reward acquisition."
- Proven via native V2 violation tests.
