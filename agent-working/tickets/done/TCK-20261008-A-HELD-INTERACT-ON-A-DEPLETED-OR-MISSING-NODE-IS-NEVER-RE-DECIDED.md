---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261008-A-HELD-INTERACT-ON-A-DEPLETED-OR-MISSING-NODE-IS-NEVER-RE-DECIDED
phase: done
date: 2026-10-08
tags: [ecology, economy, resource]
---

# TCK-20261008-A-HELD-INTERACT-ON-A-DEPLETED-OR-MISSING-NODE-IS-NEVER-RE-DECIDED

## Title
An INTERACT whose resource node is missing or has no charges left is held forever as a successful no-op, so the gatherer is never re-decided (same class as the held ATTACK on an incapacitated or out-of-range target).

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while measuring the forage path for decision 27 (rpg-planner ruling B, 2026-10-08, PR 2 of a stack, stacked on #426). Entity 4 (crowded_frontier, seed 42) took berries from tick 60, the node ran dry, and from about tick 100 to 900 it sat on `INTERACT target=<depleted node> outcome=SUCCESS` while its hunger went from 6 to 90. `scheduler.py` re-runs a held `ENTITY_ACT` whose payload is non-empty and never calls the brain for it; `execute_interact` had no failure path, so nothing ended the task. The `evaluate_entity_intent` hook was reached 3 times in 1000 ticks for that entity.

## Scope
1. `CoreActions.execute_interact` takes the state and, when the target node is missing or has no charges, spends nothing and reports a typed `failure_reason` (`SOURCE_MISSING` or `SOURCE_DEPLETED`). `ActionRouter` passes the context.
2. `_is_unrecoverable_action_failure` ends a held INTERACT on those two reasons (a per-action table; the ATTACK list is unchanged), so the payload is cleared and the scheduler runs the brain.
3. Tests for both cases, the control (a node with charges is still held), the scheduler classification, and the reason table.
4. A parity entry (TOWN-197) and the pinned all-gatherer effect, reported (not tuned).

## Out of Scope
- Any hunger or food logic. PR 2 only hands the subject back to the brain; eating carried food stays in the decision-27 / free-meal PR (planner's addition).
- How the brain then chooses (it may pick the same node again; it is re-decided either way).

## Acceptance Criteria
- [x] An INTERACT on a zero-charge node and on a missing node ends the held task (empty payload) and logs one rejection with the typed reason; an INTERACT on a node with charges is held as before. 3 of the 5 new tests fail without the fix.
- [x] A released gatherer is scheduled as `ENTITY_BRAIN` on its next cadence tick; the held one was `ENTITY_ACT`.
- [x] The pinned all-gatherer effect is reported (stored investigation): 15 of 15 digests identical across two runs; alive at t=1100 up in all three worlds, starvation down.
- [x] The scoped test run passes with no existing expectation moved.

## Related Tickets
- `TCK-20261008-RESOURCE-REGROWTH-IS-COMPUTED-BUT-NEVER-MERGED-INTO-THE-WORLD-DYNAMICS-UPDATE` (#426, this is stacked on it), `TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL` (carried food stays there).

## Related Docs
- `docs/parity_ledger/town_resource.yaml` TOWN-197; the held ATTACK reset in `docs/parity_ledger/combat_movement.yaml`.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-A-HELD-INTERACT-ON-A-DEPLETED-OR-MISSING-NODE-IS-NEVER-RE-DECIDED/`

## Related Code Areas
- `src/engine/domain/core_actions.py`, `src/engine/domain/action_router.py`, `src/engine/pipeline_phases/actions.py`, `src/engine/scheduler.py`.

## Assumptions / Open Questions
- No Bible 03/04 chapter or ledger entry covered a held INTERACT, so TOWN-197 is a new parity entry, not a divergence (the code was behind the intent that a task ends when it can no longer succeed).
- Regrowth (#426) makes "depleted now" temporary; the released gatherer can return to the node once it refills.

## Implementation Notes
`interact_target_unavailable(state, target_id)` returns the typed reason or None; with no state or no target (legacy callers) it returns None and the old behaviour is kept. The ATTACK and INTERACT reason sets live in one dict keyed by action.

## Test Summary
New: 5 tests (`tests/unit/actions/test_interact_depleted_node_task_reset.py`). Scoped run: see the stored test plan. CI is the first real run of the full gate set.

## Files Changed
`src/engine/domain/core_actions.py`, `src/engine/domain/action_router.py`, `src/engine/pipeline_phases/actions.py`, `tests/unit/actions/test_interact_depleted_node_task_reset.py`, `docs/parity_ledger/town_resource.yaml`, this ticket and its stored artifacts, `docs/REGISTRY.yaml`.

## Completion Summary
A gatherer whose node runs dry (or vanishes) is now released to the brain instead of repeating a no-op for hundreds of ticks. Pinned effect on every gatherer, base = PR 1: alive at t=1100 2.8 to 4.8, 13.4 to 16.2, 5.6 to 9.8; starvation deaths 13.0 to 10.0, 17.6 to 14.0, 14.0 to 7.6; deterministic 15 of 15.
