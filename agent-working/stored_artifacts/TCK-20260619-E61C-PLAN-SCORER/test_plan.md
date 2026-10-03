# Test Plan — TCK-20260619-E61C-PLAN-SCORER

## tests/unit/adventure/test_scoring_plan_bonus.py (8 tests)

1. `test_plan_advance_bonus_applied_when_route_matches_head_goal` — CRAFT_UPGRADE route, pending CRAFT_UPGRADE head goal → plan_advance_bonus=1.5
2. `test_plan_advance_bonus_not_applied_when_goal_completed` — completed head goal → no bonus
3. `test_plan_advance_bonus_not_applied_when_goal_blocked` — blocked head goal → no bonus
4. `test_plan_advance_bonus_not_applied_when_queue_empty` — empty goal_queue → no bonus
5. `test_plan_advance_bonus_not_applied_when_route_family_mismatch` — GATHER_RESOURCE route, CRAFT_UPGRADE goal → no bonus
6. `test_plan_advance_bonus_zero_when_no_plan` — progression_plan=None → bonus=0.0
7. `test_existing_hero_quest_bonus_still_applies` — HERO quest bonus regression guard
8. `test_existing_warrior_mage_bonus_still_applies` — group bonus regression guard
