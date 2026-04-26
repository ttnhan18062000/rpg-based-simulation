# TCK-20260426-PH16-AOE-LEGALITY

## Title
Implement Authoritative AoE Legality and Splash

## Status
DONE

## Request Summary
Recover the authoritative Area-of-Effect (AoE) logic where impact center legality is separate from splash consequences.

## Scope
- Add verify_aoe_legality to LegalityServiceV2.
- Implement resolve_aoe_attack in CombatResolutionSystem.
- Add splash damage resolution to ApplyPath.

## Acceptance Criteria
- AoE targeting validates LOS to impact center.
- Splash damage is applied correctly to nearby entities.
- Primary target receives damage proportional to impact.

## Related Tickets
- None

## Related Docs
- legacy_logic_coverage_report.md

## Implementation Notes
- Splash damage is pre-calculated in ApplyPath before the main entity loop to ensure deterministic results.
- 50% splash damage multiplier implemented as per legacy default.

## Test Summary
- tests/combat/test_aoe_splash.py (PASSED)

## Files Changed
- src/core/updates.py
- src/engine/legality.py
- src/engine/combat.py
- src/engine/apply.py

## Completion Summary
Full recovery of AoE combat mechanics. The V2 engine now correctly distinguishes between primary impact and secondary splash consequences.
