# TCK-20260421-P6-M2-T1-LEDGER-SCHEMA

## Title

Define the canonical row schema for legacy replacement items

## Status

DONE

## Request Summary

Milestone 2 Task 1 of Phase 6: Define the formal schema for the Authoritative Replacement Ledger. This schema will be used to inventory every legacy behavior and track its replacement status, divergence, and proof path.

## Scope

- [x] Create `docs/engine/replacement_ledger_schema.md`.
- [x] Define column requirements: Area, Atomic Item, Legacy Source, Legacy Test, Status, Divergence Note, Proof Path, Owner, Phase Target.
- [x] Define a stable ID format (`LEG-RPG-xxx`).
- [x] Provide granularity guidance.

## Out of Scope

- Populating the ledger with actual data (Tasks 2-3).

## Acceptance Criteria

- [x] `replacement_ledger_schema.md` exists and defines a stable row unit.
- [x] Schema is compatible with both RPG-core and System-Compatibility surfaces.
- [x] Schema provides placeholders for all Phase 6-7 column requirements.

## Related Tickets

- None (Start of Milestone 2)

## Related Docs

- [resource_phase6_milestone2.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_phase6_milestone2.md)
- [src_principle.md](file:///home/vboxuser/Work/rpg-based-simulation/src_principle.md)

## Related Stored Artifacts

- None

## Related Code Areas

- `docs/engine/`

## Assumptions / Open Questions

- None

## Implementation Notes

- Schema includes Status options: `SUPPORTED`, `DIVERGENT`, `UNSUPPORTED`, `RETIRED`.
- Granularity is set at the **Contract/Rule level** to ensure auditability.

## Test Summary

- Verified link integrity via `pytest tests/docs/test_doc_integrity.py`.

## Files Changed

- [NEW] `docs/engine/replacement_ledger_schema.md`
- [NEW] `docs/engine/legacy_replacement_ledger.md`

## Completion Summary

- Successfully established the fundamental data structure for Phase 6 legacy inventory. The replacement ledger is now initialized with a stable schema and granularity guidance, ready for population.
