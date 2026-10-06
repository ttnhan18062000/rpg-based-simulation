---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES
phase: done
date: 2026-10-05
tags: [engine, combat]
---

# TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES

## Title
An `ATTACK` task that fails `OUT_OF_RANGE` is deliberately not reset, so when the target walks away
the attacker re-dispatches the same out-of-range attack instead of re-deciding — the sticky-task
family again, one task kind over from the pursuit defect fixed in the attack-path ticket

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Reported by `rpg-implementer` (Lane A) while closing
`TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK`, and filed here
rather than by the lane because it is a second defect in the same family and deserved its own
acceptance criteria rather than being folded into a batch that was already four tickets wide.

**What was observed** (Lane A, `frontier_living_world`, single run, after fix (A) made the decision
path reachable at all): of the first four recorded `execute_attack` calls, **three were rejected
`OUT_OF_RANGE` at readiness 100**, all of them attacker entity 46 against target entity 17, after the
target had moved out of reach. The attacker kept the task and kept re-dispatching it.

**The mechanism, read in the code** (`src/engine/pipeline_phases/actions.py:221-230`): the
unrecoverable-failure reset is scoped to `TARGET_INCAPACITATED` alone. The comment above it states the
intent explicitly — `INSUFFICIENT_READINESS` and `OUT_OF_RANGE` are "deliberately NOT reset here --
both are real, recoverable conditions (readiness regens; range may close via a fresh pursuit
decision)". That reasoning holds for `INSUFFICIENT_READINESS`, which recovers with no new decision.
It does **not** hold for `OUT_OF_RANGE`: range closes only "via a fresh pursuit decision", and keeping
the `ATTACK` task is exactly what prevents that decision from being taken. The recovery path the
comment names is the path the code blocks.

This is the same shape as the pursuit defect: a task whose completion condition depends on a world
fact that has changed, with no re-evaluation. The fix for pursuit (a live-target reach check ending
the `ENTITY_MOVE`) is the mirror image of what is needed here.

**Why P1 and not P0.** It suppresses attacks that the decision path has already chosen, so it is on
the progression-starvation chain — but the chain's dominant gate is the flee gate
(`TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE`, P0, 143 of 147
forced decisions). Fixing this one raises the ceiling on an attack path the flee gate still mostly
closes, so it is worth doing and is not the headline.

## Scope
1. **Measure the defect on `main` first, before any change.** `origin/main` now contains #344, so this
   is the first measurement of this behaviour on a tree where identical runs do not diverge for
   unrelated reasons. Record, per world, how many `execute_attack` calls are rejected `OUT_OF_RANGE`,
   how many are re-dispatches of a task that already failed the same way, and how many ticks the
   longest such repeat survives. Lane A's three-of-four is a sample from one run on a pre-#344 tree
   and must not be carried forward as the measured value.
2. **Decide the reset rule on the evidence, and state it in the ticket.** The candidate is: reset the
   task on `OUT_OF_RANGE` when the target is a live entity that has moved beyond reach since dispatch,
   leaving `INSUFFICIENT_READINESS` untouched. If the measurement shows the repeat is instead bounded
   (the pursuit fix already re-closes range within a tick or two in most cases), say so and scale the
   change down — a bounded repeat may not justify touching the action pipeline at all.
3. **Implement the chosen rule** in `src/engine/pipeline_phases/actions.py`, and correct the comment at
   :221-230, which will otherwise still assert the reasoning the change overturns.
4. **Tests with a disabling control**, in the house style: with the new condition disabled, exactly the
   tests that assert "the task ends when the target leaves reach" fail and every "must not change"
   test passes. Cover at minimum: target moves out of reach (task ends, entity re-decides);
   `INSUFFICIENT_READINESS` at the same range (task survives, unchanged); target dies
   (`TARGET_INCAPACITATED` path unchanged).
5. **Re-measure after the change** on the same worlds and report the before/after, as samples if they
   are single runs.

## Out of Scope
- The flee gate and the trauma mapping (P0 ticket, **blocked on owner/rule-owner ratification** — do
  not touch the appraisal path here).
- The 10-tick strategic brain cadence in `src/engine/scheduler.py`. **CONTESTED, and the planner has
  endorsed leaving it alone**; the whole point of resetting the task is to let the existing cadence
  take a fresh decision.
- Any widening of the Sticky-Task Law itself. This is one reason code in one phase, not a global
  weakening — the global option was already refused once on this chain.
- `FRIENDLY_FIRE_ILLEGAL` (its own ticket, below in Related Tickets), even though the same run
  surfaced both.

## Acceptance Criteria
- [ ] The pre-change measurement is recorded on post-#344 `main`, per world, with the repeat length.
- [ ] The reset rule is stated in the ticket with the evidence that chose it, including the option of
      not changing the pipeline if the repeat turns out to be bounded.
- [ ] `OUT_OF_RANGE` against a live target that has left reach no longer re-dispatches indefinitely;
      `INSUFFICIENT_READINESS` behaviour is unchanged and a test asserts that.
- [ ] The `actions.py:221-230` comment no longer asserts reasoning the change contradicts.
- [ ] Tests ship with a disabling control, and the control result is recorded.
- [ ] Post-change measurement reported, labelled sample or value according to how it was taken.
- [ ] If engine behaviour changes: `docs/engine/` and `docs/parity_ledger/` updated for the same
      subsystem, per the planner's standing ruling that a hold on engine behaviour covers both.

## Related Tickets
- `TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK` — the pursuit half
  of the same family; **must land first**, since this ticket's measurement is only meaningful on a tree
  where the decision path is reachable.
- `TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET` — the dead-target reset the current code does
  perform, and the origin of the comment being corrected here.
- `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE` — P0, the
  dominant gate on the same chain; **blocked on ratification, do not start**.
- `TCK-20261005-TACTICAL-HOSTILE-LIST-AND-LEGALITY-DISAGREE-ABOUT-WHO-IS-HOSTILE` — surfaced by the
  same run.

## Related Docs
- `docs/engine/` tactical/action contract (the sticky-task note added by the attack-path ticket).
- The kernel contract's Sticky-Task Law, as cited in the attack-path ticket's `kernel.md` edit.

## Related Stored Artifacts
- The attack-path ticket's `probes/` (with README) — the recorded-`execute_attack` instrumentation this
  measurement should reuse rather than rebuild. Paths are hard-coded; edit before running, one
  simulation at a time.

## Related Code Areas
- `src/engine/pipeline_phases/actions.py:221-230` — the reset condition and its comment.
- `src/engine/candidate_selector.py` — `pursuit_reached_attack_range` / `pursuit_completion_update`,
  the mirror-image helper from the pursuit fix.
- `src/engine/legality.py:274+` — where range is actually evaluated (`get_manhattan_dist`, plus the
  environmental range multiplier, which means "out of reach" is not a fixed radius).

## Assumptions / Open Questions
- **Lane.** Lane A (`actions.py` sits in the action pipeline Lane A already holds for this family).
  `scheduler.py` is not needed and is not granted.
- **Open question for the implementer, not the planner:** the range check carries an environmental
  multiplier (`legality.py` range_mult). Decide and record whether "has left reach" is evaluated
  against the multiplied range or the base range — they can disagree in bad weather, and picking the
  base range would re-introduce a sticky task whenever the multiplier shrinks reach.
- The attacker-46/target-17 pair recurring in three of four samples may be one entity pair, not a
  general pattern. The scope-1 measurement settles that; do not generalise from it beforehand.

## Implementation Notes
Scope 1 measured on `origin/main` `7a9f302db` (contains #344 and #347; source identical, only ticket files differ):
`audit_mode=True`, tick budget disabled, seed 42, 2000 ticks, one simulation at a time, every world run twice and the
pairs matched exactly, so the figures are **values**. `execute_attack` calls / `OUT_OF_RANGE` / repeats: crowded_frontier
0/0/0, urban_political 0/0/0, dungeon_crawl 4/0/0, frontier_living_world 7/2/1. The one repeat is two verdicts for one
pair inside a single tick. That table counts verdicts only. Lane A's "three of four" was a pre-fix sample and is not
reproduced.

**Correction (same session).** The first reading of that table, "bounded, close with no change", was wrong: a task held
after `OUT_OF_RANGE` that never re-dispatches produces no further verdicts, so verdict streaks cannot see it. Following
the attacker's task (`probes/oor_follow.py`, `frontier_living_world`): attacker 34 failed `OUT_OF_RANGE` against target 11
at t157, then held `ENTITY_ACT ATTACK` on target 11 until the target died at t1008 (about 851 ticks), through readiness back
at 100, the target adjacent (t158-t166) and the target 7 tiles away (t172+), with no further `execute_attack` verdict.
Nothing ends the task. One entity, one event: the defect is real on main, its frequency is not established. Unexplained,
not traced: why the held task does not re-dispatch at all while in reach with readiness 100.

Scope 2 rule: the scale-down-to-nothing outcome is **withdrawn**; scopes 3-5 apply (see `investigation.md`). Open
question answered: "left reach" is judged against the multiplied range (`legality.py:284`).

**Mechanism (later the same session, `probes/posture_check.py`, a sample).** The 851-tick hold is **not** the missing `OUT_OF_RANGE`
reset. At t157 attacker 34's posture toward target 11 was `probe` (risk-accepted), so the `OUT_OF_RANGE` was a legitimate attack
failure. The posture flipped to `avoid` at t161 and `retreat` at t165, and from t161 the action router's posture gate
(`action_router.py`) returned a bare no-op every tick: no failure, so the payload was annotated `outcome: SUCCESS` (with the stale
`reason: OUT_OF_RANGE`), the task was kept, and the scheduler re-dispatched it until the target died. That defect, which this ticket's
measurement discovered, is fixed under `TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS`.
The planner ruled (a) closes as a measured non-defect for its own premise and that the `actions.py:221-230` comment is left alone
(nothing showed the `OUT_OF_RANGE` non-reset holding a task). Frequency caveat kept: one entity, one episode.

## Test Summary
No tests: nothing was changed under this ticket's own premise. Evidence is the verdict-count measurement (values, 4 worlds x 2 runs
matched) and the task trace (`oor_follow.py`, `posture_check.py`, samples). The existing `test_attack_out_of_range_does_not_reset_task`
still pins the un-reset `OUT_OF_RANGE` behaviour and passes.

## Files Changed
- `agent-working/stored_artifacts/.../probes/`: `oor_probe.py`, `measure.sh`, `oor_follow.py`, `posture_check.py` (measurement only)
- no `src/`, `tests/` or `docs/engine/` change under this ticket

## Completion Summary
Closed as a measured non-defect for its own premise (the missing `OUT_OF_RANGE` reset is not what holds sticky `ATTACK` tasks on `main`).
Its measurement found a different, real defect (a posture-withheld dispatch is a silent success that keeps the task, held ~851 ticks in
one world), fixed in `TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS`. Not established:
whether an `OUT_OF_RANGE` task can be held by any other route; the 11 `execute_attack` calls in the sample cannot show that it cannot.
