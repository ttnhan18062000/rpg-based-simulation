# TCK-20260610-REWARD-RELATION-CLASSIFY

## Title
Replace Faction.MONSTER_HORDE shortcut in reward classification with relation projection service

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`CombatRewardClassificationService.classify_defeated_target()` still uses a `Faction.MONSTER_HORDE` enum shortcut. Reward classification should use the same relation semantics path as attack legality.

## Scope
- Replace MONSTER_HORDE shortcut with `FactionSemanticsService.is_hostile_compat()` as primary classification step
- Add `source="relation_projection"` to the returned RewardClassification
- Update tests to assert `source == "relation_projection"` for hostile-faction entities
- Update parity ledger COMB-280

## Out of Scope
- Changing `FactionSemanticsService` itself
- Changing combat legality rules
- Removing `EntityRole` fallback

## Acceptance Criteria
- [x] `classify_defeated_target()` calls FactionSemanticsService / relation projection service as first step
- [x] Direct `Faction.MONSTER_HORDE` shortcut removed from primary classification path
- [x] Legacy `MONSTER_HORDE` entities still earn rewards through compatibility fallback path
- [x] Tests assert `source == "relation_projection"` for hostile-faction entities
- [x] Parity ledger updated

## Related Stored Artifacts
- `stored_artifacts/TCK-20260610-REWARD-RELATION-CLASSIFY/`

## Implementation Notes
- `is_hostile_compat("monster_horde", "hero_guild")` falls back to legacy bucket logic → True (mutual hostility).
- Behavior change: MONSTER_HORDE attacker defeating HERO_GUILD defender now gives HOSTILE_CREATURE (source="relation_projection") instead of HERO_KILL. HERO_KILL is still reachable when attacker faction is NEUTRAL.
- COMB-280 parity ledger updated with new v2_evidence and divergence_note.

## Test Summary
`pytest tests/unit/combat/test_combat_rewards.py -v` — 11/11 passed.

## Files Changed
- `src/engine/combat_rewards.py`
- `tests/unit/combat/test_combat_rewards.py`
- `docs/parity_ledger/combat_movement.yaml`

## Completion Summary
MONSTER_HORDE shortcut replaced with FactionSemanticsService.is_hostile_compat(). Source field set to "relation_projection" for all hostile-faction outcomes.
