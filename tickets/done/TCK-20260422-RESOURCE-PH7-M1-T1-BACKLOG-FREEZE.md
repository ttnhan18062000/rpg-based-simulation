---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260422-RESOURCE-PH7-M1-T1-BACKLOG-FREEZE
phase: done
date: 2026-04-22
tags: [resource, ph7, m1, t1, backlog, freeze]
---

# TCK-20260422-RESOURCE-PH7-M1-T1-BACKLOG-FREEZE

## Title

Freeze Phase 7 Replacement Ledger Row Set

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Execute Task 1 of Phase 7 Milestone 1: Freeze the exact Phase 7 replacement-ledger row set as the official substrate backlog. This involved triaging rows in the `legacy_replacement_ledger.md` to focus on "Substrate Closure" and publishing the final backlog.

## Scope

- [x] Identify and collect Phase 7-owned rows from `docs/engine/legacy_replacement_ledger.md`.
- [x] Verify that the row set is strictly limited to deterministic substrate closure.
- [x] Exclude semantic recovery rows assigned to later phases (8, 9).
- [x] Create `docs/engine/phase7_backlog.md` as the authoritative implementation backlog.
- [x] Update `docs/engine/phase_allocation_map.md` to reflect triaged counts.

## Out of Scope

- Defining closure conditions (Task 2).
- Identifying downstream blockers (Task 3).
- Implementing any substrate code.

## Acceptance Criteria

- [x] `docs/engine/phase7_backlog.md` exists and contains only substrate-owned rows.
- [x] Row ownership is explicit and aligned with the high-level Phase 7 plan.
- [x] The backlog is reviewable and stable.

## Related Tickets

- [TCK-20260421-P6-M1-T5-EXIT-PACKAGE](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260421-P6-M1-T5-EXIT-PACKAGE.md)

## Related Docs

- [resource_phase7_high_level.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_phase7_high_level.md)
- [resource_phase7_milestone1.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_phase7_milestone1.md)

## Related Stored Artifacts

- None

## Related Code Areas

- `docs/engine/`

## Assumptions / Open Questions

- Assumes `docs/engine/replacement_ledger.md` is the authoritative source for Phase 6 output.

## Implementation Notes

- None yet.

## Test Summary

- None.

## Files Changed

- [MODIFY] [legacy_replacement_ledger.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/legacy_replacement_ledger.md)
- [MODIFY] [phase_allocation_map.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/phase_allocation_map.md)
- [NEW] [phase7_backlog.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/phase7_backlog.md)
- [MODIFY] [TCK-20260422-RESOURCE-PH7-M1-T1-BACKLOG-FREEZE.md](file:///home/vboxuser/Work/rpg-based-simulation/tickets/inprogress/TCK-20260422-RESOURCE-PH7-M1-T1-BACKLOG-FREEZE.md)

## Completion Summary

Successfully froze the Phase 7 replacement-ledger row set.
- Triaged 185 rows in `legacy_replacement_ledger.md`.
- Moved 4 semantic recovery rows (Quests, Sabotage, Rumors, Memory) to Phase 8/9.
- Retained 3 substrate-specific gaps (Hazards, Calamities, Evolution) in Phase 7.
- Marked 8 existing substrate rows for final "Hardening" in Phase 7 to ensure authoritative closure.
- Published the official `docs/engine/phase7_backlog.md`.
- Updated `docs/engine/phase_allocation_map.md` with verified counts.
