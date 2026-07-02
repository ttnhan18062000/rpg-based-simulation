# Plan — TCK-20260619-E61C-PLAN-SCORER

## Changes

1. `src/domains/adventure/schema.py`: add `plan_advance_bonus: float = 0.0` to AdventureRouteOption after blocker_penalty
2. `src/domains/adventure/scoring.py`:
   - Add TYPE_CHECKING import for ProgressionPlan
   - Add `progression_plan: Optional["ProgressionPlan"] = None` to score() signature
   - Add section 4b: plan_advance_bonus computation (head_goal status guard + route.family.value match)
   - Include plan_advance_bonus in final_score formula
   - Include plan_advance_bonus in dataclasses.replace() call
3. `docs/simulation/domains/progression_planner_contract.md` (new)
4. `tests/unit/adventure/test_scoring_plan_bonus.py` (new — 8 tests)
5. `docs/parity_ledger/progression.yaml` (PROG-112)

## Score Formula (updated)

`score = urgency + benefit + personality_bias + plan_advance_bonus + confidence_bonus - risk_penalty - blocker_penalty`

## Plan-Advance Bonus Logic

```
plan_advance_bonus = 0.0
if progression_plan is not None and progression_plan.goal_queue:
    head_goal = progression_plan.goal_queue[0]
    if head_goal.status in ("pending", "in_progress"):
        if route.family.value == head_goal.target_route_family:
            plan_advance_bonus = 1.5
plan_advance_bonus = min(plan_advance_bonus, 3.0)  # cap for future stacking
```
