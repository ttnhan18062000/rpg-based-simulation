# TCK-20260608-REWARD-TRACE-COVERAGE

## Title
Add REWARD_CATEGORY and REWARD_SOURCE to all reward-producing combat traces

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
resolve_attack and resolve_multi_attack currently include REWARD_SOURCE in their combat update traces, but resolve_skill_usage does not include a clear REWARD_SOURCE trace, and no path currently includes REWARD_CATEGORY. This task ensures that every reward-producing combat path — resolve_attack, resolve_skill_usage, and multi-attack — includes both REWARD_CATEGORY and REWARD_SOURCE in the CombatUpdate trace dict. Tests must assert the presence and value of both keys so the reward classification source is fully observable in telemetry.

## Scope
- Add REWARD_CATEGORY key to combat update trace in resolve_attack
- Add REWARD_CATEGORY key to combat update trace in resolve_skill_usage
- Add REWARD_SOURCE key to combat update trace in resolve_skill_usage (currently missing)
- Add REWARD_CATEGORY and REWARD_SOURCE to multi-attack reward path trace if it is a separate code path
- Add tests/unit/combat/test_combat_reward_trace.py with trace assertion tests
- Trace keys must use values from RewardClassification.category and RewardClassification.source

## Out of Scope
- Adding reward trace to EntityState
- Changing reward calculation values
- Adding REWARD_CATEGORY or REWARD_SOURCE to non-reward combat outcomes (misses, blocks, etc.)

## Acceptance Criteria
- [ ] resolve_attack trace includes REWARD_CATEGORY and REWARD_SOURCE on a kill
- [ ] resolve_skill_usage trace includes REWARD_CATEGORY and REWARD_SOURCE on a kill
- [ ] resolve_multi_attack trace includes REWARD_CATEGORY and REWARD_SOURCE if it has a separate reward path
- [ ] tests/unit/combat/test_combat_reward_trace.py exists with at least four test cases
- [ ] Single attack monster kill trace test asserts REWARD_SOURCE value
- [ ] Skill attack kill trace test asserts REWARD_SOURCE value
- [ ] Hero defeat trace test asserts HERO_KILL source
- [ ] Reward calculation values (XP, gold) are unchanged

## Related Tickets
- TCK-20260607-COMBAT-REWARD-SERVICE (predecessor — added REWARD_SOURCE to resolve_attack and resolve_multi_attack)
- TCK-20260608-CLASSIFY-DEFEATED-TARGET (dependency — classify_defeated_target provides the classification object with source)

## Related Docs
- docs/mechanics/02_combat_laws.md
- docs/engine/kernel.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/combat.py
- src/engine/combat_rewards.py
- tests/unit/combat/test_combat_reward_trace.py

## Assumptions / Open Questions
- REWARD_SOURCE is already partially implemented in resolve_attack and resolve_multi_attack; skill_usage path needs it added
- Neutral target traces may omit reward keys entirely or include REWARD_CATEGORY=NONE depending on current design — implementation must inspect before deciding

## Implementation Notes
Added REWARD_CATEGORY = classification.category.value to resolve_attack and resolve_multi_attack. Added skill_trace dict to resolve_skill_usage with both REWARD_SOURCE and REWARD_CATEGORY; passed trace= to the CombatUpdate return. Both keys only set on kill/defeat (not on survive).

## Test Summary
80 combat unit tests pass (8 new in test_combat_reward_trace.py).

## Files Changed
- src/engine/combat.py
- tests/unit/combat/test_combat_reward_trace.py (new)

## Completion Summary
All three reward-producing combat paths now emit REWARD_CATEGORY and REWARD_SOURCE in their CombatUpdate trace dicts. 80 tests pass.
