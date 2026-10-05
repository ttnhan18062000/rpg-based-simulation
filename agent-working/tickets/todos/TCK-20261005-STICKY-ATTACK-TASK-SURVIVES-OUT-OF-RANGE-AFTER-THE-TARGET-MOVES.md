---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES
phase: open
date: 2026-10-05
tags: [engine, combat]
---

# TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES

## Title
An `ATTACK` task that fails `OUT_OF_RANGE` is deliberately not reset, so when the target walks away
the attacker re-dispatches the same out-of-range attack instead of re-deciding — the sticky-task
family again, one task kind over from the pursuit defect fixed in the attack-path ticket

## Status
OPEN

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
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
