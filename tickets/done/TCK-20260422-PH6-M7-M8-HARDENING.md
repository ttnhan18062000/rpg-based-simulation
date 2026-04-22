# TCK-20260422-PH6-M7-M8-HARDENING

## Title
Phase 6 M7/M8 P0 Recovery Hardening and Ledger Truth Alignment

## Status
INPROGRESS

## Request Summary
Verify the Phase 6 M7 (Social Trust) and M8 (Opportunity Attacks) P0 recovery implementation. Align the Authoritative Replacement Ledger with the actual implementation status and harden the "decorative" implementation shortcuts to ensure legacy parity and architectural integrity.

## Scope
- Harden `SocialAppraisalSystem` to use legacy-parity trust recalibration rules.
- Harden `CombatReactionSystem` to use standard combat damage resolution for Opportunity Attacks.
- Update `AuthoritativeState` and `EntityState` to include typed `CombatComponent` for authoritative damage tracking, eliminating `properties`-based hacks.
- Update `docs/engine/legacy_replacement_ledger.md` status from UNSUPPORTED to SUPPORTED for the 9 affected P0 items.
- Synchronize parity tests to verify real-valued outcomes instead of simplified constants.

## Out of Scope
- Full combat system beyond melee OAs.
- Ranged combat mechanics.
- Phase 7 Substrate Closure (Task 1 onwards).

## Acceptance Criteria
- `SocialAppraisalSystem` recalibrates trust using harm/help ratios matching legacy formulas.
- `CombatReactionSystem` resolves OAs using standard attacker/defender power and mitigation logic.
- `legacy_replacement_ledger.md` rows LEG-RPG-049 to 056 and 099 are marked SUPPORTED.
- Parity tests `test_social_parity.py` and `test_oa_parity.py` pass with realistic values.
- No durable gameplay state is stored in `EntityState.properties`.

## Related Tickets
- [TCK-20260421-P6-M7-M8-P0-RECOVERY](file:///home/vboxuser/Work/rpg-based-simulation/tickets/done/TCK-20260421-P6-M7-M8-P0-RECOVERY.md)

## Related Docs
- [docs/engine/legacy_replacement_ledger.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/engine/legacy_replacement_ledger.md)
- [src_v2_principle.md](file:///home/vboxuser/Work/rpg-based-simulation/src_v2_principle.md)

## Related Stored Artifacts
- None

## Related Code Areas
- `src_v2/core/state.py`
- `src_v2/systems/social.py`
- `src_v2/engine/combat.py`
- `src_v2/engine/apply.py`
- `tests_v2/parity/test_social_parity.py`
- `tests_v2/parity/test_oa_parity.py`

## Assumptions / Open Questions
- Assumption: Legacy damage formulas for OA should match standard melee resolution.
- Assumption: Legacy trust recalibration should use the Archetype-weighted ratios from `SocialInterpretationService`.

## Implementation Notes
- None

## Test Summary
- TBD

## Files Changed
- TBD

## Completion Summary
- TBD
