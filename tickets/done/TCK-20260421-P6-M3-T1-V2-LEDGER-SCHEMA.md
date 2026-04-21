# TCK-20260421-P6-M3-T1-V2-LEDGER-SCHEMA

## Title

Define the canonical src_v2 row schema aligned to the legacy inventory

## Status

DONE

## Request Summary

Milestone 3 Task 1: Define the schema for the src_v2 side of the replacement ledger. This ensures that every V2 implementation can be directly compared against the legacy inventory defined in Milestone 2.

## Scope

- Align the V2 inventory unit with the Legacy unit as defined in [replacement_ledger_schema.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/replacement_ledger_schema.md).
- Define columns for V2 Source, V2 Test, Proof Artifact, Support Status (Supported/Partial/Internal), and Ambiguity Note.
- Ensure the schema captures the distinction between "Implemented" and "Officially Supported".

## Out of Scope

- Populating the V2 inventory (Tasks 2-5).

## Acceptance Criteria

- `replacement_ledger_schema.md` is updated to include the V2-side requirements.
- The V2 row structure is perfectly comparable to the legacy structure.

## Related Tickets

- [TCK-20260421-P6-M2-T1-LEDGER-SCHEMA](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260421-P6-M2-T1-LEDGER-SCHEMA.md)

## Related Docs

- [resource_phase6_milestone3.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_phase6_milestone3.md)
- [replacement_ledger_schema.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/replacement_ledger_schema.md)

## Related Stored Artifacts

- None

## Related Code Areas

- `docs/engine/`

## Assumptions / Open Questions

- None

## Implementation Notes

- Expanded schema to 15 columns to capture comprehensive audit trail metadata (Target Phase, Proof Path, etc).

## Test Summary

- Schema validation verified via consolidated ledger merge.

## Files Changed

- [MODIFY] `docs/engine/replacement_ledger_schema.md`

## Completion Summary

- Finalized the 15-column canonical schema.
- Synchronized the ledger with the new schema during the Milestone 5 merge.
- Verified that all inventory items now support high-fidelity proof-path tracking.
