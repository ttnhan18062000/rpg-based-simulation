# TCK-20260426-PH14-MULTI-OA

## Title
Implement Multi-Attacker Opportunity Attacks

## Status
DONE

## Request Summary
Recover the legacy capability for multiple hostiles to execute Opportunity Attacks (OA) against a single moving target in the same tick.

## Scope
- Refactor OA detection in LegalityService to return all engaged hostiles.
- Support multiple simultaneous intents in CombatUpdate.
- Implement multi-attacker damage resolution in CombatResolutionSystem and ApplyPath.

## Acceptance Criteria
- A target moving through multiple hostile zones takes damage from ALL attackers in one tick.
- OA resolution is deterministic and ordered by EntityID.
- 100% parity with legacy "Must-Have" OA logic.

## Related Tickets
- None

## Related Docs
- legacy_logic_coverage_report.md

## Implementation Notes
- CombatUpdate now carries a list of simultaneous intents.
- Damage is aggregated in the authoritative apply path to maintain atomic state transitions.

## Test Summary
- tests/parity/test_multi_oa_parity.py (PASSED)

## Files Changed
- src/engine/legality.py
- src/core/updates.py
- src/engine/combat.py
- src/engine/movement.py

## Completion Summary
Multi-attacker OA is now fully authoritative and deterministic. Verified with complex surround scenarios.
