---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260421-P6-M7-M8-P0-RECOVERY
phase: done
date: 2026-04-21
tags: [p6, m7, m8, recovery]
---

# TCK-20260421-P6-M7-M8-P0-RECOVERY

## Title

Implement Phase 6 P0 Logic Recovery (Social Trust & Opportunity Attacks)

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Hardening Phase 6: Recover the P0 "Must-Have" gaps identified in the Master Ledger implementation. This includes Social Trust history and Opportunity Attack mechanics to ensure the engine baseline is not "decorative" in critical gameplay contracts.

## Scope

- Implement `SocialComponent` and `SocialAppraisalSystem`.
- Link strategic outcomes to trust recalibration.
- Implement engagement detection in `LegalityService`.
- Implement Opportunity Attack triggers in `MovementSystem`.
- Implement `CombatReactionSystem` for OA resolution.

## Out of Scope

- Full combat system (P1/P2 items).
- Ranged combat mechanics (Phase 7).

## Acceptance Criteria

- `test_social_parity.py` passes (3/3).
- `test_oa_parity.py` passes (2/2).
- Trust recalibration matches legacy recalibration rules.
- OAs trigger authoritatively on disengagement.

## Related Tickets

- [TCK-20260421-P6-M5-M6-CONSOLIDATION](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260421-P6-M5-M6-CONSOLIDATION.md)

## Related Docs

- [resource_phase6_milestone5.md](file:///home/vboxuser/Work/rpg-based-simulation/resource_phase6_milestone5.md)
- [docs/engine/legacy_replacement_ledger.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/legacy_replacement_ledger.md)

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/state.py`
- `src/core/updates.py`
- `src/engine/movement.py`
- `src/engine/legality.py`
- `src/systems/social.py`
- `src/engine/combat.py`

## Assumptions / Open Questions

- None

## Implementation Notes

- P0 recovery completed within Phase 6 to satisfy the entry gate requirements for Phase 7.
- Damage and trust values calibrated to legacy parity.

## Test Summary

- `tests/parity/test_social_parity.py`: PASSED
- `tests/parity/test_oa_parity.py`: PASSED

## Files Changed

- [MODIFY] `src/core/state.py`
- [MODIFY] `src/core/updates.py`
- [MODIFY] `src/engine/movement.py`
- [MODIFY] `src/engine/legality.py`
- [MODIFY] `src/engine/apply.py`
- [NEW] `src/systems/social.py`
- [NEW] `src/engine/combat.py`
- [NEW] `tests/parity/test_social_parity.py`
- [NEW] `tests/parity/test_oa_parity.py`

## Completion Summary

- Social Trust persistence and recalibration implemented and verified.
- Opportunity Attack mechanics (engagement/trigger/resolution) implemented and verified.
- Engine baseline is now hardened for P0 tactical and social contracts.
