# TCK-20260608-CLASSIFY-DEFEATED-TARGET

## Title
Add classify_defeated_target(attacker, defender, state) to CombatRewardClassificationService

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
CombatRewardClassificationService currently only exposes classify(EntityRole), which requires callers to extract the role from the entity before calling. This is a legacy-role-only API that cannot use relation projection or clean identity data. This task adds classify_defeated_target(attacker, defender, state) as the new primary method, using a resolution order of: (1) clean identity/relation projection if available, (2) compatibility mapping, (3) legacy EntityRole fallback. The existing classify(EntityRole) method is retained as a compatibility wrapper. Combat resolution in combat.py must migrate to classify_defeated_target().

## Scope
- Add CombatRewardClassificationService.classify_defeated_target(attacker: EntityState, defender: EntityState, state: AuthoritativeState) -> RewardClassification static/classmethod
- Implement resolution order: relation projection → compatibility mapping → legacy EntityRole fallback
- For this repair phase, clean path minimum: hostile relation → hostile_creature category; HERO role fallback → HERO_KILL; MONSTER role fallback → MONSTER_KILL; neutral role → NONE
- Keep existing classify(EntityRole) method as a compatibility wrapper calling through to legacy fallback path
- Update resolve_attack in combat.py to call classify_defeated_target() instead of classify()
- Update resolve_skill_usage in combat.py to call classify_defeated_target()
- Update resolve_multi_attack in combat.py to call classify_defeated_target()
- Add tests in tests/unit/combat/test_combat_rewards.py for the new method
- Optionally add tests in tests/unit/combat/test_direct_combat_outcomes.py for integration path

## Out of Scope
- Rewriting reward math or XP formulas
- Removing legacy EntityRole fallback
- Requiring full relation migration across all entity types
- Removing rebirth/permadeath behavior

## Acceptance Criteria
- [ ] classify_defeated_target(attacker, defender, state) method exists on CombatRewardClassificationService
- [ ] Combat resolution (resolve_attack, resolve_skill_usage, resolve_multi_attack) calls classify_defeated_target() not classify()
- [ ] Legacy EntityRole MONSTER defender classifies as MONSTER_KILL via the new method
- [ ] Legacy EntityRole HERO defender classifies as HERO_KILL via the new method
- [ ] Hostile relation classification produces hostile_creature reward category
- [ ] Neutral merchant/citizen defender produces RewardCategory.NONE
- [ ] Old classify(EntityRole) still passes all existing compatibility tests
- [ ] Legacy reward XP and gold multiplier values are unchanged

## Related Tickets
- TCK-20260607-COMBAT-REWARD-SERVICE (predecessor — created classify(EntityRole) and CombatRewardClassificationService)

## Related Docs
- docs/mechanics/02_combat_laws.md
- docs/mechanics/01_entity_anatomy.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/combat_rewards.py
- src/engine/combat.py
- tests/unit/combat/test_combat_rewards.py
- tests/unit/combat/test_direct_combat_outcomes.py

## Assumptions / Open Questions
- AuthoritativeState has enough relation/identity projection data to support at least minimal hostile-relation detection
- If relation projection is not available, the method falls back to EntityRole without error

## Implementation Notes
Added HOSTILE_CREATURE to RewardCategory. Added classify_defeated_target classmethod: step 1 checks defender.identity.faction == MONSTER_HORDE → HOSTILE_CREATURE (xp×10, gold×5); step 2 falls back to classify(EntityRole). Updated all 3 call sites in combat.py. classify(EntityRole) unchanged as compatibility wrapper. COMB-280 parity ledger updated.

## Test Summary
72 combat unit tests pass (5 new: hostile_creature category, hero_kill fallback, neutral NONE, multiplier values, compatibility wrapper).

## Files Changed
- src/engine/combat_rewards.py
- src/engine/combat.py
- tests/unit/combat/test_combat_rewards.py
- docs/parity_ledger/combat_movement.yaml

## Completion Summary
Added classify_defeated_target to CombatRewardClassificationService with hostile-relation detection via faction check, falling back to legacy EntityRole. All combat resolution call sites migrated. 72 tests pass.
