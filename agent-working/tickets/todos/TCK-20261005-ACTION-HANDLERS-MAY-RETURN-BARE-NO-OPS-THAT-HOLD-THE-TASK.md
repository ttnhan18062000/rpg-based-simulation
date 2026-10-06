---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261005-ACTION-HANDLERS-MAY-RETURN-BARE-NO-OPS-THAT-HOLD-THE-TASK
phase: open
date: 2026-10-05
tags: [engine, investigation]
---

# TCK-20261005-ACTION-HANDLERS-MAY-RETURN-BARE-NO-OPS-THAT-HOLD-THE-TASK

## Title
The silent-no-op fix covered `ActionRouter.execute_action`'s own returns; whether the per-action handlers
(`execute_interact`, `execute_repair`, ...) return the same bare no-op that holds a task was not enumerated

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Follow-up flagged by `rpg-implementer` when closing
`TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS`. That ticket
enumerated and fixed the router's own two bare no-op returns (the posture gate and the unsupported-action
fall-through), now reported as `ACTION_WITHHELD_BY_POSTURE` and `UNSUPPORTED_ACTION`. **It did not enumerate
the handler-internal paths** the router delegates to. If any handler returns
`EntityUpdate(readiness_delta=0.0)` with no `failure_reason`, it reproduces the same defect for that action
kind: `actions.py` sees no failure, the task is never cleared, and the scheduler re-dispatches a task that
does nothing.

**Why P2, not P1.** The measured instance (an ~839-tick held `ATTACK`) was the router's posture gate, now
fixed; on `frontier_living_world` that fix took withheld entity-ticks from 844 to 2. No handler-internal
instance has been observed. This ticket establishes whether one exists.

## Scope
1. Enumerate every handler the router dispatches to and every return path in each that returns without a
   `failure_reason`.
2. For each, determine whether it can be reached while a task is held — a no-op that can only occur on a
   fresh decision is harmless; one that recurs on a held task is the defect.
3. Measure held-task exposure per action kind under `audit_mode` with the budget disabled, same method as
   the parent ticket.
4. Fix only instances that are reachable on a held task, using the parent ticket's shape: a typed
   `ReasonCode` and the existing unrecoverable-clear branch in `actions.py`. No second termination path.

## Out of Scope
- The router's own returns (done in the parent).
- The posture gate's policy.
- `scheduler.py` (CONTESTED, not granted).

## Acceptance Criteria
- [ ] Complete list of handler-internal non-failure returns, each marked reachable-on-held-task or not.
- [ ] Held-task exposure per action kind, as values.
- [ ] Reachable instances fixed with typed reasons and a disabling-control test; unreachable ones recorded.
- [ ] If nothing is reachable, stated plainly and the ticket closed as a measured non-defect.

## Related Tickets
- `TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS` — parent.

## Related Docs
- `docs/engine/kernel.md` — Sticky-Task Law; divergence 2.69; parity `COMB-330`.

## Related Stored Artifacts
- The parent ticket's probes (withheld entity-ticks, longest held run).

## Related Code Areas
- `src/engine/domain/action_router.py` and every handler it dispatches to.
- `src/engine/pipeline_phases/actions.py` — the unrecoverable-clear branch.

## Assumptions / Open Questions
- **Lane.** Lane A, after its current batch.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
