---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260930-IMPACT-REPORT-ECONOMY-CORE-OWNERSHIP-AND-DECLARED-MARKERS
phase: done
date: 2026-09-30
tags: [testing]
---

# TCK-20260930-IMPACT-REPORT-ECONOMY-CORE-OWNERSHIP-AND-DECLARED-MARKERS

## Title
Impact report: map src/core/conservation.py and inventory.py to economy as well as substrate, and read a changed test's declared markers

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Child of `TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION`. Found by the core-RPG pilot (`docs/testing/core_rpg_test_pilot_2026-09-30.md`) and fixed in the same batch. The impact report mapped `src/core/conservation.py` to substrate only, with no `mechanic_scenario` level, although conservation is the ch03 economic law; and for a changed test file it named no domain or level.

## Scope
1. `core_rpg_report.DOMAIN_IMPORT_PREFIXES["economy"]` gains `src.core.conservation*` and `src.core.inventory*`. Conservation implements ch03 §1 (Atomic Conservation). Inventory implements ch03 §2 (slot and weight limits, `INVENTORY_FULL`; parity TOWN-011/012 in `town_resource.yaml`). Both stay substrate too, so a change names both owners and recommends the scenario level. Other `src/core/` modules are unchanged.
2. `impact_report._owners_of` returns every owner (gameplay domain first, then substrate).
3. For a changed test file, its declared `domain`/`level` markers are added as `declared-marker` domains and levels beside every other rule; they never override or duplicate one.
4. The ownership map (`architecture_design_notes.md` §3.1) Economy row is updated in the same change.
5. Tests: a 6th sample case (conservation), inventory, plain-substrate unchanged, declared markers added, never overriding.

## Out of Scope
- Other `src/core/` modules (state, updates, ...). - Changing the classification design (declared markers stay listed, never override a file's class).

## Acceptance Criteria
1. A change to `src/core/conservation.py` or `src/core/inventory.py` yields the `economy` and `substrate` domains and the `mechanic_scenario` level.
2. A change to a plain substrate module is unchanged.
3. A changed test's declared markers appear as `declared-marker` reasons, never replacing another rule's reason.
4. `test_marker_vocabulary` stays green.

## Related Tickets
- `TCK-20260929-EPIC-TEST-STRUCTURE-SELECTION` (parent)
- `TCK-20260930-CORE-RPG-PILOT-NODE-CHARGE-ACCOUNTING` (evidence)

## Related Docs
- `docs/plans/test_architecture/reference/architecture_design_notes.md`: §3.1 Economy row names the two dual-owned files.

## Related Stored Artifacts
None.

## Related Code Areas
`tools/test_architecture/impact_report.py`, `tools/test_architecture/core_rpg_report.py`, `tests/unit/tools/test_impact_report.py`.

## Assumptions / Open Questions
None.

## Implementation Notes
Design decision kept as documented in the pilot report: the core-RPG report's file classification stays heuristic; declared markers are listed beside it and never override it. The new economy prefixes do add a gameplay-import signal for tests importing the two modules.

## Test Summary
4 new tests in `tests/unit/tools/test_impact_report.py`.
`pytest tests/unit/tools/test_impact_report.py tests/unit/tools/test_core_rpg_report.py tests/unit/tools/test_marker_vocabulary.py tests/unit/tools/test_marker_check.py`: pass.

## Files Changed
- `tools/test_architecture/impact_report.py`, `tools/test_architecture/core_rpg_report.py`
- `docs/plans/test_architecture/reference/architecture_design_notes.md`
- `tests/unit/tools/test_impact_report.py`

## Completion Summary
Conservation and inventory now map to economy and substrate; declared markers reach the impact report.
