---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED
phase: open
date: 2026-10-06
tags: [combat, cognition]
---

# TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED

## Title
An `ATTACK` task whose target is out of reach (melee, Manhattan distance 2: diagonal) is kept, annotated `FAILURE/OUT_OF_RANGE`, and re-dispatched every ~5 ticks for as long as the pair stays put: the brain is never re-run, so nothing closes the range.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found while re-measuring `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE` (found by `rpg-implementer`, filed on `rpg-feature-planning`'s request, non-blocking for that PR). In `frontier_living_world` (seed 42, 2000 ticks, `audit_mode`, budget off) with the AGENCY-06 dread change, `execute_attack` is called 298 times against 30 before the change. 274 of the 298 are `OUT_OF_RANGE` and 267 come from **one entity** (49) holding an `ATTACK` task on entity 18.

**Mechanism, traced (not a hypothesis):**
1. Melee legality is `Manhattan distance <= 1` (`src/engine/legality.py:291`: `effective_range <= 1.5 and dist > 1` gives `OUT_OF_RANGE`). Entity 49 at `(64, 41)` and entity 18 at `(65, 42)` are diagonal: distance 2, so every attack fails with `OUT_OF_RANGE` and costs 50 readiness (`combat_actions.py:60`).
2. `ActionRoutingPhase.route` ends an `ATTACK` task only for `TARGET_INCAPACITATED` (and the router's any-action reasons). `OUT_OF_RANGE` is deliberately kept as recoverable ("range may close via a fresh pursuit decision", `pipeline_phases/actions.py:257`) and the payload is annotated `{"action": "ATTACK", "target_id": 18, "outcome": "FAILURE", "reason": "OUT_OF_RANGE"}`.
3. The scheduler re-runs the brain only for an **empty** `ENTITY_ACT` payload (`scheduler.py:68`, `is_idle_act = work_kind == "ENTITY_ACT" and not ent.task.payload`). The annotated payload is non-empty, so the brain is not run and no pursuit decision is ever made. The task is dispatched again whenever readiness regenerates to 100 (50 to 100 at +10/tick: one call per ~5 ticks).
4. Neither entity moves, so the range never closes. From tick 242 entity 49 stays at `(64, 41)` against a target at `(65, 42)`, `stale_ticks` 1 throughout, in the trace to tick 642 (and 267 calls over the run).

**Independent of the dread term (constructed reproduction on `7daef8075`, which has no `regional_dread`):** `probes/repro_oor.py` routes a melee `ATTACK` task through `ActionRoutingPhase.route` for a hostile at Manhattan distance 1, 2 and 5. Distance 1 gives `outcome: SUCCESS` (readiness -100); distance 2 and 5 give `outcome: FAILURE, reason: OUT_OF_RANGE` (readiness -50) with a **non-empty payload kept**, i.e. `is_idle_act == False`, no brain re-run. So the hold needs only a held `ATTACK` task and a target the entity cannot reach. The dread change only altered the trajectory so this pair formed; in the pre-change corpus run there were 10 `OUT_OF_RANGE` calls in total and no long hold.

**Not established:** why entity 18 also stays put at `(65, 42)` (not traced), and what moved entity 49 tick to tick in the first 14 failing ticks (ticks 173 to 186 it changed position every tick while its task stayed the held `ATTACK`).

## Scope
1. Decide whether `OUT_OF_RANGE` on a held `ATTACK` should end the task (so the brain re-decides and can pursue or reposition) or whether a diagonal-adjacent melee pair should be treated as in reach. **A rules question, not an obvious fix: ask the world-rules owner** (whether diagonal adjacency counts as melee reach is world semantics; `legality.py` currently says no).
2. Implement the ruling through the existing typed-failure shape (`_is_unrecoverable_action_failure` and `ReasonCode`, as in the `TARGET_INCAPACITATED` and #362 cases), with a disabling control.
3. Re-measure `frontier_living_world` and `crowded_frontier` (seed 42, 2000 ticks, `audit_mode`, budget off, twice): `execute_attack` calls split by outcome, longest `OUT_OF_RANGE` hold, and the decision-path attack count.

## Out of Scope
- The dread mapping (`AGENCY-06`), `kernel.py`, `scheduler.py` (contested) unless the ruling needs it: if the fix is "re-run the brain on a held out-of-range ATTACK" it is a `scheduler.py` change and must go through the planner.

## Acceptance Criteria
- [ ] The reach rule (diagonal adjacency) is ruled by the world-rules owner and recorded.
- [ ] A constructed test fails on `main` and passes after the fix (disabling control stated).
- [ ] The longest `OUT_OF_RANGE` hold in both corpus worlds is reported before and after, including zeros.
- [ ] Docs and parity ledger updated if behaviour changes.

## Related Tickets
- `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE` — where it was found; its PR body states that `frontier_living_world`'s 298 `execute_attack` includes 267 from this loop (deliberate attacks ~31, flat).
- `TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS` — the same held-task family (#362).
- `TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET` (done) — the dead-target case of the same hold.

## Related Docs
- `docs/mechanics/02_combat_laws.md` §7 (legality and the readiness gate)
- `docs/engine/kernel.md` (Sticky-Task Law)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE/probes/` (`atk_outcomes.py`, `before_after_out.txt`); `trace49.py` and `repro_oor.py` alongside it.

## Related Code Areas
- `src/engine/pipeline_phases/actions.py` (`_is_unrecoverable_action_failure`, the clear branch)
- `src/engine/scheduler.py:68` (`is_idle_act`) — contested
- `src/engine/legality.py:285-292` (melee reach rule)

## Assumptions / Open Questions
- Whether a diagonal pair is "in reach" is a world-semantics question for the world-rules owner, not for implementation.
- Whether other `ATTACK` failures (`LOS_OBSTRUCTED`, `INSUFFICIENT_READINESS`) hold the same way was not measured.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
