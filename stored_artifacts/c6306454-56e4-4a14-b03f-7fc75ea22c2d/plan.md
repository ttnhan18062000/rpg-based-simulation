# Implementing Bracketing Bonus for Multi-Attacks

The current implementation of `CombatResolutionSystem.resolve_multi_attack` fails to apply tactical bonuses such as flanking, high ground, and cover. While `resolve_attack` (single attack) handles these correctly, multi-attacks (used for Opportunity Attacks and simultaneous hits) only sum raw damages.

## Proposed Changes

### Combat Resolution System

#### [MODIFY] [combat.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/combat.py)
- Create a private method `_get_tactical_multipliers(attacker, defender, state, is_opportunity_attack)` that returns `(atk_mult, def_mult, trace)`.
- Extract tactical logic from `resolve_attack` into this helper.
- Update `resolve_attack` to use the helper.
- Update `resolve_multi_attack` to use the helper inside its attacker loop.
- Ensure `FLANKING_BONUS` and `SURROUNDED` bonuses are correctly applied when multiple attackers are present.

## Verification Plan

### Automated Tests
- `pytest tests/tactical/test_bracketing_bonus.py::test_bracketing_bonus_requires_active_attackers -v -s`
- Update the above test to assert the EXACT damage including the flanking bonus (expected: 18 * 1.15 = 20.7 -> 20 or 21 depending on rounding).
- Add a new test case `test_bracketing_bonus_ignores_inactive_attackers` where one flanking entity is dead/inactive.

### Manual Verification
- Check the `trace` in the `CombatUpdate` to ensure "FLANKING" and "HIGH_GROUND" markers are correctly recorded during multi-attacks.
