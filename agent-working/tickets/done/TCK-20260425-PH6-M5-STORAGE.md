---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260425-PH6-M5-STORAGE
phase: done
date: 2026-04-25
tags: [ph6, m5, storage]
---

# TCK-20260425-PH6-M5-STORAGE

## Title

Implementation of Advanced Equipment and World Storage

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement deterministic gear ranking, world treasure chests, and persistent home storage. Ensure authoritative state management for all storage domains.

## Scope

- Update \`AuthoritativeState\` with \`chests\` and \`home_storage\`.
- Implement gear ranking and auto-equip logic.
- Implement treasure chest interaction and respawn support in \`ApplyPath\`.
- Implement home storage deposit/withdraw actions.
- Add contract tests for all new storage domains.

## Out of Scope

- Guild storage (Task 6.7).
- Complex enchanting.

## Acceptance Criteria

- [x] Auto-equip correctly identifies and equips items with higher relevant stats.
- [x] Chests provide items and then become unavailable for a defined tick duration.
- [x] Home storage allows persistent item storage separate from entity inventory.
- [x] All transactions between inventories and storage are atomic and authoritative.
- [x] All tests in \`tests/inventory/test_equipment_chests_storage.py\` pass.

## Related Tickets

- TCK-20260425-PH6-M4-ECONOMY (Done)

## Related Docs

- resource_v2_e_phases.md

## Related Code Areas

- src/core/state.py
- src/core/equipment.py [NEW]
- src/town/home_storage.py [NEW]
- src/engine/apply.py

## Implementation Notes

- Added \`home_storage\` and \`chests\` to \`AuthoritativeState\`.
- \`EquipmentService.rank_item\` uses weighted \`atk_bonus\` and \`def_bonus\`.
- \`HomeStorageAction\` ensures atomicity by emitting a single \`StateUpdate\` with both entity and storage deltas.

## Test Summary

- \`tests/inventory/test_equipment_chests_storage.py\`:
  - \`test_auto_equip_ranking\`: PASS
  - \`test_home_storage_atomicity\`: PASS
  - \`test_chest_loot_and_apply\`: PASS

## Files Changed

- src/core/state.py
- src/core/updates.py
- src/engine/apply.py
- src/core/equipment.py [NEW]
- src/town/home_storage.py [NEW]

## Completion Summary

Phase 6 Milestone 5 is complete. The system now supports automated gear management and persistent world-object storage, fully integrated into the authoritative engine truth.
