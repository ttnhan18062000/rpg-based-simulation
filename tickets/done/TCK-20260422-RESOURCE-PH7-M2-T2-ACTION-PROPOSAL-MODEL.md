# TCK-20260422-RESOURCE-PH7-M2-T2-ACTION-PROPOSAL-MODEL

## Title

Complete Authoritative Action Proposal Model

## Status

INPROGRESS

## Request Summary

Execute Task 2 of Phase 7 Milestone 2: Complete the authoritative action proposal model for supported substrate scope. This involves making action intent explicit, structured, and stable by defining the `ActionProposal` model and its linkage to authoritative updates.

## Scope

- [ ] Create `src_v2/core/actions.py`.
- [ ] Define `ActionProposal` as a frozen dataclass with slots.
- [ ] Include fields: `actor_id`, `verb` (ActionType), `target`, `reason`, and `updates`.
- [ ] Define V2 `ActionType` enum in `src_v2/core/enums.py`.
- [ ] Ensure the model is deterministic and serialization-safe.
- [ ] Establish initial linkage between `ActionProposal` and `EntityUpdate`.

## Out of Scope

- Full implementation of conflict resolution (Milestone 3+).
- Normalization of legacy reason/target shapes (Task 4).

## Acceptance Criteria

- [ ] `src_v2/core/actions.py` exists with a strictly typed `ActionProposal` model.
- [ ] `ActionType` enum is defined in `src_v2/core/enums.py`.
- [ ] The proposal model does not contain hidden mutation payloads.

## Related Tickets

- [TCK-20260422-RESOURCE-PH7-M2-T1-ACTION-UPDATE-AUDIT](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260422-RESOURCE-PH7-M2-T1-ACTION-UPDATE-AUDIT.md)

## Related Docs

- [resource_phase7_milestone2.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_phase7_milestone2.md)
- [phase7_m2_gap_audit.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/phase7_m2_gap_audit.md)

## Related Stored Artifacts

- None

## Related Code Areas

- `src_v2/core/`
- `src_v2/actions/`

## Assumptions / Open Questions

- None yet.

## Implementation Notes

- None yet.

## Test Summary

- None.

## Files Changed

- [NEW] `tickets/inprogress/TCK-20260422-RESOURCE-PH7-M2-T2-ACTION-PROPOSAL-MODEL.md`

## Completion Summary

- None yet.
