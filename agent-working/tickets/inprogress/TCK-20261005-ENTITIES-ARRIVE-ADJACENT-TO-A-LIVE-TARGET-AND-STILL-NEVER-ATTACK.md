---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK
phase: implement
date: 2026-10-05
tags: [combat, strategy, cognition]
---

# TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK

## Title
`crowded_frontier` navigates within 1 tile of a live hostile in 3779 of 3839 combat-objective samples
and dispatches **zero** decision-path attacks — the starvation chain's headline symptom survives both
#291 and the entity-target fix

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
**The measurement in this ticket is `rpg-implementer`'s**, taken as the A/B control for
`TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES` and reported to
`rpg-planner` on 2026-10-05. Filed separately because it is not that ticket's defect and would
survive its fix intact — the planner's call, not the implementer's.

`TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` exists because the decision-driven `ATTACK` path
fires 0-2 times per 1000-2000 ticks while the incidental opportunity-attack mechanic fires
181-2177. Its item (1) investigation root-caused that to the dispatch discard: `COMBAT_ENGAGE` won
the goal competition and the win was thrown away. `TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND`
(PR #291) fixed the discard and merged 2026-10-04.

**The discard is fixed and the attack count did not move.** Measured at 2000 ticks, seed 42,
`audit_mode`, `LocalSequentialExecutor`, live holders only, both arms of the termination A/B:

| | `crowded_frontier` | `frontier_living_world` |
|---|---|---|
| combat objectives are kind `defeat_enemy` | 6891 / 6891 samples | — |
| navigation within 1 tile of the **live** target | **3779 / 3839** | — |
| `CombatActions.execute_attack` dispatches (control / fixed) | **0 / 0** | **5 / 5** |
| `resolve_attack` calls (control / fixed) | **0 / 0** | **1 / 1** |

So on `crowded_frontier` entities now hold a correctly-kinded objective against a live enemy, resolve
its current position, walk to within one tile of it in 98.4% of samples — and attack **zero** times.

**This is the original "arrived and do nothing" symptom, with the arrival now correct.**
`TCK-20261002`'s own framing was that entities navigate to where the enemy *was* and emit an empty
`EntityUpdate` forever. Fixing the position only moved the failure one step later: they arrive at
where the enemy *is*, and still emit nothing. The terminus is presumably the arrived-noop branch at
`src/engine/tactical.py:297-299` (bare `EntityUpdate(entity_id=…)`) but that is a lead, not a
finding — it has not been traced for this case.

**Second, narrower discrepancy.** On `frontier_living_world`, 5 dispatches produce **1**
`resolve_attack` call. Four of five dispatched attacks do not reach resolution. That ratio is small
enough to trace exactly and may be a different defect from the zero-dispatch case.

## Scope
1. Trace, for one `crowded_frontier` sample where an entity is within 1 tile of its live target and
   holds an `ACTIVE` `defeat_enemy` objective, what the tactical pass actually returns and why no
   attack is dispatched. One traced sample end-to-end beats a survey.
2. Establish whether the zero-dispatch case and the 4-of-5 unresolved-dispatch case are the same
   defect or two. Do not assume.
3. Record which gate rejects the attack — legality, range, posture, cooldown, target eligibility, or
   none of them (i.e. the dispatch is simply never attempted). **"None of them, the branch is never
   reached" is a valid and likely answer**, and distinguishing "rejected" from "never attempted" is
   the main thing this ticket must deliver.
4. Relate the finding to the incidental opportunity-attack mechanic, which fires 181-2177 times in
   the same runs. Whatever lets the incidental path attack is a working positive control for
   whatever blocks the decision path; use it as one rather than reasoning about the decision path in
   isolation.

## Out of Scope
- The entity-target fix and objective termination — `TCK-20261002`. This ticket **assumes that
  landed** and measures what is left.
- Tuning combat volume, XP thresholds or engagement rates. `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME`
  is explicitly blocked until combat volume is not starved, and retuning against a starved path is
  the exact failure that epic warns about twice.
- The incidental opportunity-attack mechanic itself. It is the control, not the subject.
- `src/core/**` and `src/engine/{kernel,governor}.py` — contested, and partly held by `TCK-20261002`
  while that is open. Claim before editing.

## Acceptance Criteria
- [ ] One `crowded_frontier` sample traced end-to-end from "entity within 1 tile of live target with
      an ACTIVE `defeat_enemy` objective" to the tactical pass's actual return value, with the
      branch that terminates it named by `file:line` at a stated commit.
- [ ] Scope 3's distinction is answered explicitly: the attack is **rejected by X**, or **never
      attempted because Y**. An answer of "never attempted" must name the condition that was not met.
- [ ] Scope 2 answered: one defect or two, with the evidence.
- [ ] The decision-path attack count is re-measured after any fix, on both worlds, both reported
      whatever they are — including if the count stays at zero.
- [ ] The measurement uses live holders only and a counter whose scope is stated. The existing
      counter counts decision-path dispatches and `resolve_attack` calls and is **silent on the
      incidental mechanic**, so it cannot speak to total combat volume; any claim about total volume
      needs a counter that says so.
- [ ] Determinism: canonical/replay/fingerprint sweep green, any moved hash explained not
      regenerated.

## Related Tickets
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — **this sits on the chain's critical path.** The
  chain's own `SEQUENCE.md` records item (1) as having answered the root question; this ticket says
  the answer was incomplete, so that file needs a correction once this is understood. Do not edit
  the sequence file on the strength of this ticket alone.
- `TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND` (done, #291) — fixed the
  discard. Its AC6 also landed contradicted; unrelated to this, but the same PR.
- `TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES` — produced this
  measurement as its control arm.
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (done) — the original 181-2177 vs 0-2
  split and the measurement method reused here.
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` — chain item (2), a corpus measurement
  ticket on this same path. Its numbers depend on what this ticket finds.
- `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME` — chain item (5), blocked last.

## Related Docs
- `docs/mechanics/02_combat_laws.md` — damage formula, tactical modifiers, victory outcomes
- `docs/engine/contracts/tactical_contract.md` — objective resolution and the tactical pass
- `docs/parity_ledger/combat_movement.yaml`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION/`

## Related Code Areas
- `src/engine/tactical.py:297-299` — the arrived-noop branch, **a lead not a finding**
- `src/domains/combat_engagement/` — `CombatActions.execute_attack`, `resolve_attack`
- `src/engine/legality.py` — a candidate gate
- `src/ai/goals/scorers.py::CombatEngageScorer` — produces the objective

## Assumptions / Open Questions
- Line numbers are from before `TCK-20261002`'s edits to `src/engine/tactical.py`. **Re-derive them**;
  that ticket changes this file substantially.
- `crowded_frontier` shows 0 dispatches and `frontier_living_world` shows 5. Whether that is the same
  defect at two severities or two different things is **open** and is Scope 2.
- Whether the decision-path attack count was ever *expected* to rise from #291 alone is not recorded
  anywhere. #291's own scope was the objective-kind discard, and nobody appears to have predicted a
  specific attack count for after it. So this ticket should not be read as "#291 failed" — it is
  "the chain's symptom is still present and the next cause is unidentified".
- The A/B's two arms differ only by the termination hook, so the identical attack counts across arms
  (0/0, 5/5) are evidence the termination fix neither helps nor harms engagement — **not** evidence
  about what blocks it.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
