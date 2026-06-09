# Plan — TCK-20260608-CLASSIFY-DEFEATED-TARGET

## Steps
1. Add HOSTILE_CREATURE to RewardCategory enum
2. Add _HOSTILE_CREATURE_CLASSIFICATION to CombatRewardClassificationService
3. Add classify_defeated_target classmethod (faction check → EntityRole fallback)
4. Update 3 call sites in combat.py
5. Extend test_combat_rewards.py with 5 new tests
6. Update COMB-280 parity ledger entry

## Deviations
None.
