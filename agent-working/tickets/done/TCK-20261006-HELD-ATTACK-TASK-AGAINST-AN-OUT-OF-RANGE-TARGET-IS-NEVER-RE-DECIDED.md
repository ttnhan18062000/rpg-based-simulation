---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED
phase: done
date: 2026-10-06
tags: [combat, cognition]
---

# TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED

## Title
An `ATTACK` task whose target is out of reach (melee, Manhattan distance 2: diagonal) is kept, annotated `FAILURE/OUT_OF_RANGE`, and re-dispatched every ~5 ticks for as long as the pair stays put: the brain is never re-run, so nothing closes the range.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
A melee `ATTACK` that comes back `OUT_OF_RANGE` now ends its task so the brain re-decides, and a completed pursuit no longer takes one more step in the same tick (the second root cause the first fix exposed); a diagonal melee pair now strikes within two brain cadences. Melee adjacency is orthogonal (Manhattan <= 1, world rule MOV-07, designer ruling under memo row 20).

Found while re-measuring `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE` (found by `rpg-implementer`, filed on `rpg-feature-planning`'s request, non-blocking for that PR). In `frontier_living_world` (seed 42, 2000 ticks, `audit_mode`, budget off) with the AGENCY-06 dread change, `execute_attack` is called 298 times against 30 before the change. 274 of the 298 are `OUT_OF_RANGE` and 267 come from **one entity** (49) holding an `ATTACK` task on entity 18.

**Mechanism, traced (not a hypothesis):**
1. Melee legality is `Manhattan distance <= 1` (`src/engine/legality.py:291`: `effective_range <= 1.5 and dist > 1` gives `OUT_OF_RANGE`). Entity 49 at `(64, 41)` and entity 18 at `(65, 42)` are diagonal: distance 2, so every attack fails with `OUT_OF_RANGE` and costs 50 readiness (`combat_actions.py:60`).
2. `ActionRoutingPhase.route` ends an `ATTACK` task only for `TARGET_INCAPACITATED` (and the router's any-action reasons). `OUT_OF_RANGE` is deliberately kept as recoverable ("range may close via a fresh pursuit decision", `pipeline_phases/actions.py:257`) and the payload is annotated `{"action": "ATTACK", "target_id": 18, "outcome": "FAILURE", "reason": "OUT_OF_RANGE"}`.
3. The scheduler re-runs the brain only for an **empty** `ENTITY_ACT` payload (`scheduler.py:68`, `is_idle_act = work_kind == "ENTITY_ACT" and not ent.task.payload`). The annotated payload is non-empty, so the brain is not run and no pursuit decision is ever made. The task is dispatched again whenever readiness regenerates to 100 (50 to 100 at +10/tick: one call per ~5 ticks).
4. Neither entity moves, so the range never closes. From tick 242 entity 49 stays at `(64, 41)` against a target at `(65, 42)`, `stale_ticks` 1 throughout, in the trace to tick 642 (and 267 calls over the run).

**Independent of the dread term (constructed reproduction on `7daef8075`, which has no `regional_dread`):** `probes/repro_oor.py` routes a melee `ATTACK` task through `ActionRoutingPhase.route` for a hostile at Manhattan distance 1, 2 and 5. Distance 1 gives `outcome: SUCCESS` (readiness -100); distance 2 and 5 give `outcome: FAILURE, reason: OUT_OF_RANGE` (readiness -50) with a **non-empty payload kept**, i.e. `is_idle_act == False`, no brain re-run. So the hold needs only a held `ATTACK` task and a target the entity cannot reach. The dread change only altered the trajectory so this pair formed; in the pre-change corpus run there were 10 `OUT_OF_RANGE` calls in total and no long hold.

**Not established:** why entity 18 also stays put at `(65, 42)` (not traced), and what moved entity 49 tick to tick in the first 14 failing ticks (ticks 173 to 186 it changed position every tick while its task stayed the held `ATTACK`).

## Scope
**Ruled 2026-10-06 (rpg-feature-planning; designer under the owner's delegation, MOV-07): melee adjacency is orthogonal, so a diagonal pair is out of reach and steps one orthogonal tile before striking. The answer also governs `_target_in_attack_reach` (#366) and the bracketing flank geometry (a bracketing flank is de-facto pursuit and ends in orthogonal reach; confirmed by one constructed case, `positioning.py` untouched). The held-task part is engineering and a Sticky-Task Law gap: `actions.py:257` kept the task "so range may close via a fresh pursuit decision" while `scheduler.py:68` re-runs the brain only for an empty payload, so that decision never came; the two lines contradicted each other. Second ruling (A): the same-tick overshoot after pursuit completion is in scope; hold granted on `src/engine/pipeline_phases/movement.py` for this ticket only (the guard reads the real completion signal, `navigation.target_clear`; the yield push stays untouched). The int() versus float distance disagreement is its own P3 ticket.**
1. Decide whether `OUT_OF_RANGE` on a held `ATTACK` should end the task (so the brain re-decides and can pursue or reposition) or whether a diagonal-adjacent melee pair should be treated as in reach. **A rules question, not an obvious fix: ask the world-rules owner** (whether diagonal adjacency counts as melee reach is world semantics; `legality.py` currently says no).
2. Implement the ruling through the existing typed-failure shape (`_is_unrecoverable_action_failure` and `ReasonCode`, as in the `TARGET_INCAPACITATED` and #362 cases), with a disabling control.
3. Re-measure `frontier_living_world` and `crowded_frontier` (seed 42, 2000 ticks, `audit_mode`, budget off, twice): `execute_attack` calls split by outcome, longest `OUT_OF_RANGE` hold, and the decision-path attack count.

## Out of Scope
- The dread mapping (`AGENCY-06`), `kernel.py`, `scheduler.py` (contested) unless the ruling needs it: if the fix is "re-run the brain on a held out-of-range ATTACK" it is a `scheduler.py` change and must go through the planner.

## Acceptance Criteria
- [x] The reach rule is ruled and recorded: orthogonal adjacency, MOV-07 (designer, memo row 20).
- [x] A constructed test fails on `main` and passes after the fix: a diagonal melee pair strikes by tick 19 (bound 20 = two brain cadences); with the movement guard restored to the old rule the first strike is tick 39; the out-of-range clear has its own unit tests (with the reason removed from `_ENDS_HELD_ATTACK_REASONS` 6 tests fail: 5 of the new ones and the reversed one).
- [x] The longest `OUT_OF_RANGE` run per entity is reported before and after: 4 / 258 to 2 / 2 (`crowded_frontier` / `frontier_living_world`), 0 runs of 3 or more after.
- [x] Docs and parity ledger updated: Bible 02 section 7, `kernel.md`, `tactical_contract.md` section 3, divergence 2.74, parity COMB-333.

## Related Tickets
- `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE` — where it was found; its PR body states that `frontier_living_world`'s 298 `execute_attack` includes 267 from this loop (deliberate attacks ~31, flat).
- `TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS` — the same held-task family (#362).
- `TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET` (done) — the dead-target case of the same hold.

## Related Docs
- `docs/mechanics/02_combat_laws.md` §7 (legality and the readiness gate)
- `docs/engine/kernel.md` (Sticky-Task Law)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED/` (plan, investigation, test plan, `probes/`); the earlier trace probes are in `agent-working/stored_artifacts/TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE/probes/` (`atk_outcomes.py`, `trace49.py`, `repro_oor.py`).

## Related Code Areas
- `src/engine/pipeline_phases/actions.py` (`_is_unrecoverable_action_failure`, the clear branch)
- `src/engine/scheduler.py:68` (`is_idle_act`) — contested
- `src/engine/legality.py:285-292` (melee reach rule)

## Assumptions / Open Questions
- Whether a diagonal pair is "in reach" is a world-semantics question for the world-rules owner, not for implementation.
- Whether other `ATTACK` failures (`LOS_OBSTRUCTED`, `INSUFFICIENT_READINESS`) hold the same way was not measured.

## Implementation Notes
Two root causes, both measured. (1) `ActionRoutingPhase.route` kept an `OUT_OF_RANGE` `ATTACK` task; `_ENDS_HELD_ATTACK_REASONS = {TARGET_INCAPACITATED, OUT_OF_RANGE}` now ends it (same empty-payload clear), the stale comment and the old pinning test are reversed, and `INSUFFICIENT_READINESS` is still kept. Every `OUT_OF_RANGE` call in both worlds came from a held task (0 on the decision tick) and every tactical `ATTACK` decision passes `verify_attack_legality`, so clearing hands the entity to a tactical pass that pursues whenever an attack is not legal; planner's worry about an out-of-reach ATTACK emission was not reproduced (the few float-distance cases are fractional positions that legality's `int()` truncation accepts). (2) After a pursuit completed, `MovementPhase.route_movement_intent` still stepped the entity because it read the tick-start navigation target and ignored the update's `target_clear`; `_already_settled_this_tick` now skips an entity whose update carries `target_clear` with no new `target_set`. Found by building the constructed pair the acceptance asked for: with only (1) the pair still did not strike.

Measured (seed 42, 2000 ticks, `audit_mode`, budget off, each arm twice identical; campaign episode 70 ticks seeds 42 and 1337), before `7f361ee73` vs after, `crowded_frontier` / `frontier_living_world`: longest consecutive `OUT_OF_RANGE` run per entity 4 / 258 to 2 / 2; tactical `ATTACK` decisions 9 / 9 to 21 / 56; decision-tick `execute_attack` 6 / 8 to 19 / 23; deliberate `resolve_attack` 22 / 22 to 23 / 27; opportunity-attack calls 105 / 130 to 88 / 123; `PANIC_RETREAT` share of tactical decisions 18.7% / 8.8% to 14.0% / 8.1%. Campaign: seed 42 0 `ATTACK` decisions both arms; seed 1337 1 decision both arms, deliberate `resolve_attack` 5 to 1. Disclosed re-baseline; SimQ anchor movement not measured locally.

## Test Summary
New: `tests/unit/actions/test_held_attack_out_of_range.py` (out-of-range melee and ranged clear, in-reach and readiness kept, classification), `tests/unit/engine/test_diagonal_melee_pair_strikes.py` (the pair strikes by tick 20; control with the guard removed misses the bound; one bracketing case ends only in orthogonal reach). Reversed: `test_attack_out_of_range_resets_task_to_idle` (it asserted the old kept-task behaviour). Updated: `tests/unit/core/test_partial_rejection.py::test_partial_rejection_occupancy_vs_combat` read the rejection off the kept task annotation (`FAILURE/OUT_OF_RANGE`); it now reads the same rejection from the audit trail (`rejections_delta`, `rejection_events`) and asserts the task ended, its intent (the move proceeds, the attack is rejected for range not faction) unchanged. CI caught it: my first scoped sweep left out `tests/unit/core`, so it ran the CI job's exact directory list afterwards (1798 passed). Scoped sweep (`tests/unit/engine`, `actions`, `combat`, `strategic`, `kernel`, the campaign episode tests, three determinism tests): 976 passed, 1 skipped, 2 xfailed (the two campaign xfails unchanged, no flip). Code-health ratchet (scratch venv with ruff, mypy, complexipy, ast-grep): 0 new, 0 worse (it first failed on one un-annotated parameter of my new helper, `ANN001` 5 > ceiling 4, fixed by annotating it, baseline untouched). Parity schema ratchet: 0 rose, 0 new.

## Files Changed
`src/engine/pipeline_phases/actions.py`, `src/engine/pipeline_phases/movement.py`, `tests/unit/actions/test_held_attack_out_of_range.py`, `tests/unit/actions/test_action_routing_task_reset.py`, `tests/unit/engine/test_diagonal_melee_pair_strikes.py`, `docs/mechanics/02_combat_laws.md`, `docs/engine/kernel.md`, `docs/engine/contracts/tactical_contract.md`, `docs/guidelines/intentional_divergences.md` (2.74), `docs/parity_ledger/combat_movement.yaml` (COMB-333), `docs/REGISTRY.yaml`, this ticket, the new `TCK-20261006-ATTACK-LEGALITY-TRUNCATES-MANHATTAN-DISTANCE-BUT-PURSUIT-REACH-DOES-NOT.md` (P3), `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING.md` (AC removed), stored artifacts.

## Completion Summary
An out-of-range `ATTACK` now ends its task and a completed pursuit stops walking in the same tick, so a diagonal melee pair closes by one orthogonal step and strikes within two brain cadences. Disclosed re-baseline: pursuit endings and held attacks changed on every world, so combat trajectories and any SimQ pillar reading attacks, retreats or survival can move. Known gaps: the SimQ grade-anchor movement is stated, not measured (calibration reports absent locally); `crowded_frontier` and `frontier_living_world` deaths read 38 of 38 and 49 of 49 in both arms so that counter is uninformative; legality's `int()` truncation versus the pursuit reach test's float distance on fractional positions is filed as its own P3 ticket and not fixed; the entity-49 target (entity 18) staying static was not traced, only shown independent of the dread term.
