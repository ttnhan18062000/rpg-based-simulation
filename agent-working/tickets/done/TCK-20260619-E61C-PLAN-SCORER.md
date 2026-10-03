---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E61C-PLAN-SCORER
phase: done
date: 2026-06-22
tags: [progression-planner, adventure-scoring, route-family, plan-advance-bonus]
---

# TCK-20260619-E61C-PLAN-SCORER

## Title
Epic 6.1C · AdventureRouteScorer Plan-Advance Bonus

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Extend `AdventureRouteScorer.score()` to apply a plan-advance bonus (+1.5) when a route's
`RouteFamily` matches the head of an entity's active `ProgressionPlan.goal_queue`. The bonus
is flat additive, capped at +3.0 total plan bonus, and only applied when the goal_queue is
non-empty and the head goal is in "pending" or "in_progress" status.

## Scope
- `src/domains/adventure/scoring.py`:
  - `AdventureRouteScorer.score()` gains an optional new parameter:
    `progression_plan: Optional[ProgressionPlan] = None`
  - When `progression_plan` is not None and `goal_queue` is non-empty:
    - Read `head_goal = progression_plan.goal_queue[0]`
    - If `head_goal.status in ("pending", "in_progress")` and
      `route.family.value == head_goal.target_route_family`:
      - Add `plan_advance_bonus = 1.5` to `final_score` (before rounding)
    - Cap: `plan_advance_bonus` is at most 1.5 per route (no stacking)
  - Add `plan_advance_bonus` to the returned dataclass replace call for traceability
  - Guard: if `goal_queue` is empty or all goals are "completed"/"blocked", no bonus applied
- `src/domains/adventure/schema.py`:
  - `AdventureRouteOption` gains optional `plan_advance_bonus: float = 0.0` field for
    introspection / audit trail (matches existing `benefit_score`, `risk_penalty` pattern)
- Parity ledger: add PROG-112 to `docs/parity_ledger/progression.yaml`
  - text: "Routes matching the head BuildGoal target_route_family receive a +1.5 plan-advance bonus"
  - status: verified, priority: P1
- Create `docs/simulation/domains/progression_planner_contract.md` with:
  - Plan-advance scoring formula and cap
  - goal_queue head selection rule
  - status guard (pending/in_progress only)
  - Reference to PROG-110 through PROG-113

## Out of Scope
- Plan revision when goals are blocked (E61D)
- Generating new plans (E61D)
- Multi-goal lookahead (future — only head of queue matters)

## Acceptance Criteria
1. A HERO entity with an active plan whose head goal targets `CRAFT_UPGRADE` scores a `CRAFT_UPGRADE` route 1.5 points higher than an identical route for an entity without a plan
2. The plan-advance bonus is NOT applied when the head goal is "completed" or "blocked"
3. The plan-advance bonus is NOT applied when `goal_queue` is empty
4. `AdventureRouteOption.plan_advance_bonus` equals 1.5 when bonus is active, 0.0 otherwise
5. Existing scorer tests (HERO quest bonus, WARRIOR+MAGE group bonus) still pass unmodified

## Related Tickets
- TCK-20260619-E61B-PLAN-EXPORTER (prerequisite)
- TCK-20260619-E61-PROGRESSION (parent epic)
- TCK-20260619-E61D-PLAN-REVISION (next — depends on this)

## Related Docs
- `stored_artifacts/TCK-20260619-E61-PROGRESSION/investigation.md`
- `docs/parity_ledger/progression.yaml`
- `docs/simulation/domains/progression_planner_contract.md` (created in this ticket)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E61-PROGRESSION/`

## Related Code Areas
- `src/domains/adventure/scoring.py` (AdventureRouteScorer.score)
- `src/domains/adventure/schema.py` (AdventureRouteOption — add plan_advance_bonus field)
- `docs/parity_ledger/progression.yaml`
- `docs/simulation/domains/progression_planner_contract.md` (new)

## Assumptions / Open Questions
- The `ProgressionPlan` type imported from `src.domains.campaigns.progression_plan`; confirm
  no circular import with `src.domains.adventure.scoring` before implementing
  (scoring.py does not currently import from campaigns/)
- If circular import arises: pass `head_goal_route_family: Optional[str]` string instead of
  the full ProgressionPlan object; avoid importing campaigns module in scoring.py
- `AdventureRouteOption.plan_advance_bonus` is audit-only; not used in further scoring math

## Implementation Notes
- Add plan_advance_bonus computation immediately after the HERO quest-opportunity block
  (L129 region of scoring.py) and before the `confidence_bonus` line
- The final_score assignment must include `+ plan_advance_bonus` in the sum at L196
- Cap check: `plan_advance_bonus = min(plan_advance_bonus, 3.0)` — future-proofing if
  multiple plan bonuses are ever introduced; currently this is always 0.0 or 1.5
- `AdventureRouteOption.plan_advance_bonus` must be included in `dataclasses.replace()`
  at the return site

## Test Summary
- `tests/unit/adventure/test_scoring_plan_bonus.py`:
  - `test_plan_advance_bonus_applied_when_route_matches_head_goal`: +1.5 on CRAFT_UPGRADE for entity with pending plan
  - `test_plan_advance_bonus_not_applied_when_goal_completed`: completed head goal → no bonus
  - `test_plan_advance_bonus_not_applied_when_goal_blocked`: blocked head goal → no bonus
  - `test_plan_advance_bonus_not_applied_when_queue_empty`: empty goal_queue → no bonus
  - `test_plan_advance_bonus_not_applied_when_route_family_mismatch`: GATHER_RESOURCE route, CRAFT_UPGRADE goal → no bonus
  - `test_plan_advance_bonus_zero_when_no_plan`: progression_plan=None → bonus=0.0
  - `test_existing_hero_quest_bonus_still_applies`: HERO quest bonus regression guard
  - `test_existing_warrior_mage_bonus_still_applies`: group bonus regression guard

## Files Changed
- `src/domains/adventure/schema.py` (modified — plan_advance_bonus field on AdventureRouteOption)
- `src/domains/adventure/scoring.py` (modified — TYPE_CHECKING import, progression_plan param, section 4b, final score, replace call)
- `tests/unit/domains/adventure/test_scoring_plan_bonus.py` (new — 8 tests)
- `docs/simulation/domains/progression_planner_contract.md` (new — authoritative contract)
- `docs/parity_ledger/progression.yaml` (PROG-112)

## Completion Summary
AdventureRouteScorer.score() gains +1.5 plan-advance bonus when route family matches head BuildGoal.
AdventureRouteOption.plan_advance_bonus audit field added. progression_planner_contract.md written.
8/8 new tests pass; 48/48 adventure unit tests pass (no regressions). PROG-112 verified.
