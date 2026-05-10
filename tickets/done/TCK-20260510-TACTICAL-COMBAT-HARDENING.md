# TCK-20260510-TACTICAL-COMBAT-HARDENING

## Title
Hardening Tactical Combat Bonuses (Bracketing/Flanking)

## Status
DONE

## Request Summary
Integrate tactical bonuses (flanking, high ground, cover) into the `resolve_multi_attack` pipeline and refactor `CombatResolutionSystem` to use a centralized tactical helper.

## Scope
- Extract tactical multiplier logic from `resolve_attack` into `_get_tactical_multipliers`.
- Implement tactical bonuses in `resolve_multi_attack`.
- Update `test_bracketing_bonus_requires_active_attackers` with strict damage assertions.
- Add `test_bracketing_bonus_ignores_inactive_entities` to verify active attacker requirement.

## Out of Scope
- AOE tactical bonuses (kept separate for now).
- Skill-based tactical overrides.

## Acceptance Criteria
- `resolve_multi_attack` correctly applies flanking and other bonuses to each attacker.
- Flanking trace markers are present in `CombatUpdate.trace`.
- Inactive entities do not contribute to flanking geometry.
- All engine and tactical tests pass.

## Related Tickets
- TCK-20260507-STABILIZE-TESTS

## Related Docs
- docs/architecture.md

## Related Stored Artifacts
- stored_artifacts/c6306454-56e4-4a14-b03f-7fc75ea22c2d/plan.md
- stored_artifacts/c6306454-56e4-4a14-b03f-7fc75ea22c2d/walkthrough.md

## Related Code Areas
- src/engine/combat.py
- tests/tactical/test_bracketing_bonus.py

## Assumptions / Open Questions
- None.

## Implementation Notes
- Centralizing tactical logic prevents drift between single and multi-attack resolution.
- Multi-attack trace keys use `{attacker_id}_{bonus_name}` format for clarity.

## Test Summary
- `tests/tactical/test_bracketing_bonus.py`: PASSED (2 tests)
- `tests/engine/`: PASSED (281 tests, excluding long runs)

## Files Changed
- [MODIFY] src/engine/combat.py
- [MODIFY] tests/tactical/test_bracketing_bonus.py

## Completion Summary
- Successfully unified tactical modifier application across all combat resolution paths.
- Hardened the flanking requirement to strictly enforce active status for participants.
- Cleaned up `CombatResolutionSystem` by removing duplicated logic.
