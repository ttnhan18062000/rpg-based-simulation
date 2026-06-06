# TCK-20260425-PH6-M3-HARVEST

## Title

Implementation of Harvesting and Resource Node Lifecycle

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement deterministic, channeled harvesting of resource nodes. Ensure authoritative node depletion, cooldowns, and item production without duplication.

## Scope

- Implement `HarvestAction` for initializing the harvesting channel.
- Implement `HarvestSystem` for progress tracking, yield production, and node depletion.
- Update `ApplyPath` for robust node state updates.
- Add contract tests for harvesting duration, yields, and depletion.

## Out of Scope

- Complex gathering tools (Task 6.4).
- Crafting logic (Task 6.6).

## Acceptance Criteria

- [x] Harvesting wood takes 10 ticks and produces 1 wood.
- [x] Harvesting iron takes 20 ticks and produces 1 iron ore.
- [x] Node charges decrement after each successful harvest.
- [x] Nodes enter cooldown state at 0 charges.
- [x] Proximity is enforced throughout the harvesting duration.
- [x] All tests in `tests/inventory/test_harvest_channeling.py` pass.

## Related Tickets

- TCK-20260425-PH6-M2-LOOT (Done)

## Related Docs

- resource_v2_e_phases.md

## Related Code Areas

- src/core/state.py
- src/engine/apply.py
- src/actions/harvest.py
- src/systems/harvest_system.py

## Implementation Notes

- Synced with `ResourceNodeState` fields: `remaining_charges`, `yields_item`, `required_ticks`.
- Used Manhattan distance (taxicab) for proximity check with a threshold of 1.5.

## Test Summary

- `tests/inventory/test_harvest_channeling.py`:
  - `test_harvest_channeling_and_yield`: PASS
  - `test_harvest_node_cooldown`: PASS

## Files Changed

- src/actions/harvest.py [NEW]
- src/systems/harvest_system.py [NEW]
- (State and Apply already supported node updates)

## Completion Summary

Phase 6 Milestone 3 is complete. The system now supports deterministic, multi-tick harvesting of resource nodes with authoritative depletion and yield generation.
