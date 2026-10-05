---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION
phase: inprogress
date: 2026-10-05
tags: [engine, combat]
---

# TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION

## Title
`BRACKETING` is the single largest forced-decision outcome at 55%, it issues an entity-targeted
`ENTITY_MOVE` in `REPOSITION` mode, and the pursuit completion condition deliberately excludes every
mode but `PURSUE` — so the sticky-task defect may be fixed for one movement mode and live in the bigger one

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
**This ticket exists because the three-gate map's answer changed when it was re-measured.** Gate 3 (the
flee gate) was recorded as the dominant gate at `PANIC_RETREAT` 143 of 147 (97%). Re-run post-#344 by
`rpg-implementer` on the same read-only forced-decision probe: **353 calls, `PANIC_RETREAT` 141 (40%),
`BRACKETING` 194 (55%), `ATTACK` 15 (4%), plain move 3.** `BRACKETING` is now the largest non-attack
outcome and it had never been named.

**The planner's reason for filing it as a gate rather than an observation**, verified in the code:

- `src/engine/tactical.py:591-597` — the `BRACKETING` branch emits a `TaskUpdate` with
  `work_kind_set="ENTITY_MOVE"`, `payload_set={"target_position": bracket_pos, "reason": "BRACKETING",
  "target_id": target.id}` and `NavigationUpdate(movement_mode_set=MovementMode.REPOSITION)`.
  **That is the same shape as the pursuit defect**: an `ENTITY_MOVE` carrying a live entity `target_id`.
- `src/engine/candidate_selector.py:94` — `pursuit_reached_attack_range` returns `False` unless
  `entity.navigation.movement_mode == MovementMode.PURSUE`. Its docstring (`:89-90`) states the
  exclusion is deliberate: "other moves also carry a `target_id` (guarding a leader, seeking cover) and
  must keep their own lifecycle."
- `src/engine/pipeline_phases/movement.py:242` names `PURSUE/INTERCEPT/KITING/BRACKETING` together as
  "real entity-tracking modes", so the engine itself already groups them.

The exclusion was a reasonable conservative scoping call, and for guarding and cover-seeking it is
correct. **But `BRACKETING` is neither**: it is combat positioning against a live hostile target, which
is the same situation the pursuit fix exists to resolve. So the fix may have closed the sticky-task hole
for `PURSUE` and left it open for the mode that fires more often.

**This is the third instance of one family.** Gate 1 was sticky pursuit `ENTITY_MOVE` (fixed).
`TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES` is sticky `ATTACK`
re-dispatch. This is sticky `BRACKETING`. The pattern — a task whose completion depends on a world fact
that changed, with no re-evaluation — is worth naming as such rather than fixing a fourth time blind.

**Not yet established, and the ticket must not assume it:** whether `BRACKETING` moves actually fail to
terminate. 55% of decisions *choosing* `BRACKETING` is not the same as those moves going sticky. It is
plausible they complete normally on arrival at `bracket_pos`, in which case this is a non-defect and the
right outcome is to record that and close.

## Scope
1. **Measure, before changing anything**, on post-#344 `main` with the attack-path fix landed: for each
   `BRACKETING` `ENTITY_MOVE`, how many ticks it survives, whether it ends on arrival at `bracket_pos`,
   and whether `evaluate_entity_intent` is re-entered afterwards. Report the distribution, not a mean.
2. **Discriminate the two outcomes explicitly.** Either (a) `BRACKETING` moves terminate on arrival and
   the decision is re-entered — then there is no defect here and the ticket closes with that recorded; or
   (b) they persist after the target has moved, exactly as pursuit did — then the completion condition
   needs extending.
3. **If (b): decide the scope of the extension on evidence, not by symmetry.** The candidate is to widen
   the mode gate to the entity-tracking modes that are combat positioning against a hostile
   (`BRACKETING`, and check `INTERCEPT`/`KITING` the same way), while leaving guarding and cover-seeking
   alone. Do **not** simply drop the mode check — the docstring's reasoning for excluding guarding and
   cover is sound and dropping it would break those lifecycles.
4. **Tests with a disabling control**, house style: with the new condition disabled, exactly the
   "`BRACKETING` ends when the target leaves the bracket" tests fail and every "must not change" test
   passes, including a guarding move and a cover-seeking move that must keep their lifecycles.
5. **Re-measure the forced-decision split afterwards.** If the fix works, the `BRACKETING` share should
   fall and `ATTACK` should rise; report both, and say so if it does not happen.
6. Report the result to the planner either way. If (a), say so plainly — a measured non-defect closes a
   question that currently distorts the three-gate map.

## Out of Scope
- The flee gate and the trauma→panic mapping
  (`TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE`, P1, **blocked on
  ratification**).
- `src/engine/scheduler.py` — still CONTESTED and not granted.
- Dropping the `movement_mode` gate wholesale, per scope 3.
- The `frontier_living_world` opportunity-attack shift (38 → 644), which is its own unexplained
  observation in the attack-path ticket.

## Acceptance Criteria
- [ ] `BRACKETING` move lifetimes measured on post-#344 `main` with the attack-path fix landed, reported
      as a distribution.
- [ ] Outcome (a) or (b) stated explicitly with the numbers that chose it.
- [ ] If (b): the mode gate is widened only to combat-positioning entity-tracking modes, with guarding
      and cover-seeking shown unchanged by test.
- [ ] `INTERCEPT` and `KITING` checked for the same defect and the finding recorded, even if not fixed here.
- [ ] Disabling-control result recorded.
- [ ] Post-fix forced-decision split re-measured and reported.
- [ ] `docs/engine/` and `docs/parity_ledger/` updated if behaviour changes, per the standing ruling.

## Related Tickets
- `TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK` — gate 1, the pursuit
  half. **Must land first**; this ticket's measurement is only meaningful with that fix in place.
- `TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES` — the sticky `ATTACK`
  sibling. Same family, one task kind over.
- `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE` — gate 3, whose
  dominance this result withdrew.
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — the chain all of these serve.

## Related Docs
- `docs/engine/kernel.md` — the Sticky-Task Law and the pursuit-completion note added by gate 1.
- The tactical contract section on entity-targeted objectives.

## Related Stored Artifacts
- The attack-path ticket's `probes/` (with README), including `forced_brain.py`, which produced the
  353-call split. **Extend it rather than writing a new harness.**

## Related Code Areas
- `src/engine/tactical.py:591-597` — the `BRACKETING` branch.
- `src/engine/candidate_selector.py:78-94` — `pursuit_reached_attack_range` and its `PURSUE`-only gate.
- `src/engine/pipeline_phases/movement.py:242` — the entity-tracking mode list.

## Assumptions / Open Questions
- **Lane.** Lane A. `tactical.py` is already ruled Lane A; `candidate_selector.py` is the fix's own file.
- Open: does `bracket_pos` get recomputed as the target moves, or is it a snapshot like the pursuit
  navigation target was? If it is a snapshot, the move is chasing a stale tile and the defect is worse
  than a missing completion condition.
- Open: is the 55% share stable across worlds, or is it a `crowded_frontier` artifact? The split came
  from one world.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
