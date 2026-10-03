---
content_type: doc
status: historical
layer: engine
authority: P2
audience: agent
tags: [world, governance]
---

# TCK-20260515-WORLD-GOVERNANCE

## Title
Milestone 12: Regional Sovereignty and Governance Logic

## Status
DONE

## Request Summary
Implement and certify the final gameplay systems for Regional Sovereignty and Governance as part of the V2 Engine completion.

## Scope
- Implement Regional Sovereignty logic in `WorldDynamicsSystem`.
- Implement Faction Governance (Taxes, Vaults) in `TownResolutionSystem`.
- Add integration tests for regional conquest and governance.
- Ensure 100% compliance with V2 architectural laws.

## Out of Scope
- Major AI behavioral changes (tactical decision making).
- Visual/UI representation of governance.

## Acceptance Criteria
- Regions correctly flip ownership based on influence/conquest.
- Faction gold (Vaults) accumulates via regional taxes.
- Governance systems respect `ResourceGovernor` operational modes.
- Integration tests confirm 100% pass rate for sovereignty scenarios.

## Related Tickets
- TCK-20260515-PERF-HARDENING (Parent/Predecessor)

## Related Docs
- docs/mechanics/regional_sovereignty.md
- docs/engine/governance_logic.md
- docs/core/state.md
- docs/engine/authoritative_pipeline.md

## Related Stored Artifacts
- None

## Related Code Areas
- src/engine/world_dynamics.py
- src/engine/town_resolution.py
- src/systems/world_systems/
- src/core/state.py

## Implementation Notes
- Resolved state reconstruction omission in `ApplyPath.apply_generation` to correctly merge `update.resource_updates` into `prior_state.global_resources` and `update.building_updates` into `prior_state.buildings`.
- Implemented `InventoryService.apply_transfer` for atomic intent transfers.
- Added `corpses`, `ground_items`, and `_regions_global_bounds` spatial cache slots to `WorkerPacket`.
- Updated `test_regional_ownership_flip` to use `LifecycleSystem` for authoritative influence shifts.

## Test Summary
- Verified 100% pass rate for `pytest tests/integration/world/test_regional_sovereignty.py`.
- Verified 100% pass rate for `pytest tests/arena/`.

## Files Changed
- src/engine/apply.py
- src/core/inventory.py
- src/core/worker_protocol.py
- src/engine/executor.py
- src/engine/world_dynamics.py
- tests/arena/test_arena_regional_control.py
- tests/arena/test_arena_tactics.py
- tests/integration/world/test_regional_sovereignty.py
- docs/core/state.md
- docs/engine/authoritative_pipeline.md

## Completion Summary
Regional Sovereignty, Spatial Caching, Arena Quests, and Faction Governance are fully implemented, verified, and certified against the V2 Engine architecture. All arena and regional sovereignty integration tests pass flawlessly.
