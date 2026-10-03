# Test Plan — TCK-20260619-E61A-PLAN-MODEL

## Tests in `tests/unit/campaigns/test_progression_plan.py`

1. `test_progression_plan_round_trip` — full ProgressionPlan with populated goal_queue, milestone_checks, revision_triggers; assert to_dict/from_dict round-trip equality
2. `test_progression_plan_empty_queue_round_trip` — empty tuple fields; verifies tuples round-trip to empty tuples (not None)
3. `test_campaign_state_with_plans_round_trip` — CampaignState with progression_plans populated; to_dict/from_dict preserves plans
4. `test_campaign_state_missing_plans_key_backward_compat` — from_dict on dict without "progression_plans" key returns CampaignState with empty dict (no KeyError)

## Coverage

- Normal round-trip: tests 1, 3
- Edge case (empty): test 2
- Backward compat: test 4
