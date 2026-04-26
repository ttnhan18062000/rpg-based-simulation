# TCK-20260425-PROG-ATTRIBUTE-POINTS

## Title
Implement Attribute Points and Manual Growth (PH8 M5)

## Status
DONE

## Request Summary
Implement the AP system for Heroes, allowing manual stat growth while keeping Monsters on an automatic scaling model (Hybrid Growth). Ensure authoritative recalculation and aptitude-based scaling.

## Scope
- Add AttributeComponent and unspent_ap tracking.
- Implement Hybrid Growth logic in LevelingService.
- Update ApplyPath for authoritative attribute transitions and recalculation.
- Implement AllocateAttributeAction with aptitude multipliers.
- Add verification tests.

## Out of Scope
- UI for attribute allocation.
- Complex secondary stats (Mana, Crit) beyond core RPG formulas.

## Acceptance Criteria
- [x] Heroes gain 5 AP on level up.
- [x] Monsters scale +10% stats automatically.
- [x] Spending AP increases attributes based on Aptitude (PROG-015).
- [x] Combat stats (HP, ATK, DEF, Evasion) recalculate deterministically (PROG-051).
- [x] Attributes are capped at 100 (PROG-046).
- [x] All 5 verification tests pass.

## Related Tickets
- None

## Related Docs
- docs/superpowers/specs/2026-04-25-attribute-points-design.md
- docs/parity_ledger

## Related Stored Artifacts
- None (will be moved after work)

## Related Code Areas
- src/core/state.py
- src/core/updates.py
- src/progression/leveling.py
- src/engine/apply.py
- src/actions/attributes.py

## Implementation Notes
- Used a strict initialization pattern in `ApplyPath._apply_entity_update` to avoid `UnboundLocalError` and ensure all components are available for cross-component recalculation (e.g., Attributes affecting Combat).

## Test Summary
- tests/progression/test_attribute_growth.py (5/5 passed)

## Files Changed
- src/core/state.py
- src/core/updates.py
- src/core/builder.py
- src/progression/leveling.py
- src/engine/apply.py
- src/actions/attributes.py
- tests/progression/test_attribute_growth.py

## Completion Summary
- Successfully implemented the full AP and manual growth pipeline. The system is now ready for Hero class specialization and deeper progression mechanics.
