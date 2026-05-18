# TCK-20260421-P6-M2-T2-RPG-CORE-POPULATION

## Title

Enumerate the RPG-core semantic replacement surface into the canonical legacy inventory

## Status

DONE

## Request Summary

Milestone 2 Task 2 of Phase 6: Populate the Authoritative Replacement Ledger with all RPG-core behaviors defined in the existing 4 legacy checklists.

## Scope

- Extract all atomic items from `legacy_checklist_part1.md` through `legacy_checklist_part4.md`.
- Populate `docs/engine/legacy_replacement_ledger.md`.
- Ensure IDs follow `LEG-RPG-xxx` format.
- Preserve subsystem grouping in the logic.

## Out of Scope

- System-compatibility surface (Task 3).
- Fine-grained normalization (Task 4).

## Acceptance Criteria

- `legacy_replacement_ledger.md` contains every item from the 4 RPG-core checklists.
- Items are tagged correctly with Area: `RPG-CORE`.
- Initial status matches the markers in the source checklists.

## Related Tickets

- [TCK-20260421-P6-M2-T1-LEDGER-SCHEMA](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260421-P6-M2-T1-LEDGER-SCHEMA.md)

## Related Docs

- `legacy_checklist_part*.md`
- `docs/engine/legacy_replacement_ledger.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `docs/engine/`

## Assumptions / Open Questions

- None

## Implementation Notes

- Inventory expanded from ~120 to 185 items (including 16 items from checklists 1-4 that were not properly tracked).
- Corrected double-headers and column alignment during Milestone 5 merge.

## Test Summary

- Full inventory integrity audit (185 rows found).

## Files Changed

- [MODIFY] `docs/engine/legacy_replacement_ledger.md`

## Completion Summary

- 100% inventory restoration complete (185 items).
- All items mapped to canonical 15-column schema.
- Area tags and IDs normalized.
