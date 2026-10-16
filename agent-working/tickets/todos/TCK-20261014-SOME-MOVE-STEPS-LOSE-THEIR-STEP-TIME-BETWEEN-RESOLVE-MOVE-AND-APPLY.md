---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261014-SOME-MOVE-STEPS-LOSE-THEIR-STEP-TIME-BETWEEN-RESOLVE-MOVE-AND-APPLY
phase: open
date: 2026-10-14
tags: []
---

# TCK-20261014-SOME-MOVE-STEPS-LOSE-THEIR-STEP-TIME-BETWEEN-RESOLVE-MOVE-AND-APPLY

## Title
About 0.03% of frontier steps move an entity with an ordinary move update that carries no `step_ready_tick_set`, although `MovementSystem._step_ready_tick` returned one at the `resolve_move` call. A second move path in one tick is suspected.

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found by the D75 swap and yield completion recount (rpg-implementer-3, 2026-10-14; TCK-20261014-SWAPS-AND-YIELDS-PAY-TERRAIN-STEP-TIME-D75-COMPLETION; audit_mode, PYTHONHASHSEED=0, frontier_living_world, seeds 42-46, 5000 ticks, fix on rpg-next 2740426eb): 249031 steps, 0 taken while the entity was held, 78 steps untimed (0.03%): raider 28, scout 24, worker 18, wild_creature 7, leader 1. Each is an ordinary move: `moved_this_tick` true, no failure reason, a `target_set`, but the update applied that tick has `step_ready_tick_set` None, so `step_ready_tick` is unchanged.
Trace on seed 42, raider 24, ticks 177-186: `_step_ready_tick` returned a value (180.0, 181.5, 182.5, ...) at each `resolve_move` call, but the entity's start-of-tick position differed from the position `resolve_move` saw (for example, the tick-start state had it at (112,39) and `resolve_move` was called with (112,38) and a target one tile back), and the applied update carries `last_cooperation_decision: SOLO`. That points at a second movement resolution for the same entity within one tick, or an update whose navigation part is replaced on merge.

## Scope
- Find the code path that produces the move update without `step_ready_tick_set` (candidates: the cooperation phase's merge, a second `resolve_move` call from the action path `src/engine/domain/movement_actions.py`, a merge that replaces `navigation`).
- Make every stepping path set `step_ready_tick`; add the test.

## Out of Scope
- Teleports and displacement to a safe region (not steps).

## Acceptance Criteria
- Untimed steps and steps taken while held are 0 on the five-seed frontier recount.
- A test pins the path found. State hash change is measured alone under audit_mode with base-vs-base.

## Related Tickets
TCK-20261014-SWAPS-AND-YIELDS-PAY-TERRAIN-STEP-TIME-D75-COMPLETION; TCK-20261014-TERRAIN-COST-BECOMES-TIME-A-STEP-COSTING-N-TAKES-N-TIMES-AS-LONG-D75.

## Related Docs
docs/guidelines/intentional_divergences.md 2.126 (the named residual).

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/movement.py (resolve_move, _step_ready_tick); src/domains/cooperation/phase.py (the merge near line 189); src/engine/domain/movement_actions.py; src/core/updates.py (NavigationUpdate.merge).

## Assumptions / Open Questions
- Runs after the route step (rpg-planner).

## Implementation Notes
TBD

## Test Summary
TBD

## Files Changed
TBD

## Completion Summary
TBD
