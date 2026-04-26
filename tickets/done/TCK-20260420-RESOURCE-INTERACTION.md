# TCK-20260420-RESOURCE-INTERACTION

## Title
Second Supported RPG Slice: Deterministic Resource Interaction Core

## Status
DONE

## Request Summary
Implement the fourth milestone of Resource Phase 4, establishing deterministic loot/harvest channeling and inventory pressure as the second officially supported gameplay slice in the V2 engine.

## Scope
- Interaction State Model (loot_progress)
- Inventory State Model (slots, weight, items)
- Resource Node Representation
- Deterministic Channeling Law (multi-tick progress)
- Inventory Pressure Law (slot/weight limits)
- Local and Concurrent Interaction Resolution
- Parity verification with old src interaction logic

## Out of Scope
- Combat interaction
- Complex item effects (buffs/debuffs)
- Equipment-specific attribute modifiers (beyond weight)
- Dynamic inventory sorting

## Acceptance Criteria
- [x] Entities can perform multi-tick "INTERACT" work items.
- [x] Interaction progress is saved in AuthoritativeState.
- [x] Inventory limits (slots/weight) are enforced authoritatively.
- [x] Looting/Harvesting preserves old src semantic parity.
- [x] Resource nodes deplete and respawn deterministically.
- [x] All changes are covered by parity and certification tests.

## Related Tickets
- TCK-20260420-PERF-FOUNDATION (Milestone 3)

## Related Docs
- resource_phase4_implementation_milestone_4.md

## Related Code Areas
- src/core/state.py
- src/core/updates.py
- src/engine/domain_logic.py
- src/engine/interaction.py [NEW]

## Test Summary
- `pytest tests/unit/test_interaction_system.py` (PASS)
- `pytest tests/certification/test_final_gate.py` (INTEG_RESOURCE_LOOP)

## Files Changed
- `src/engine/domain_logic.py`
- `src/certification/scenarios.py`

## Completion Summary
- Successfully consolidated the second officially supported gameplay surface (Movement + Harvesting).
- Implemented multi-tick interaction channeling logic with authoritative state persistence.
- Verified bit-identical parity for harvesting yields and inventory pressure under concurrent execution.
