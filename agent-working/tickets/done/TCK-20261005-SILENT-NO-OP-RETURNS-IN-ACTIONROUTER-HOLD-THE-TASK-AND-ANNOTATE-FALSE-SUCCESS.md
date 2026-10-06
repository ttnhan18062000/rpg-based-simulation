---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS
phase: done
date: 2026-10-05
tags: [engine, combat, observability]
---

# TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS

## Title
`ActionRouter.execute_action` returns a bare no-op `EntityUpdate` on several paths without reporting a
failure, so `actions.py` annotates `outcome: SUCCESS` with a stale `reason`, never clears the task, and the
scheduler re-dispatches a payload-bearing `ENTITY_ACT` that does nothing — measured holding one entity's
task for ~851 ticks until its target died

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
**This ticket carries the defect that `TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES`
went looking for and did not find.** That ticket's premise — that the missing `OUT_OF_RANGE` reset in
`actions.py:221-230` causes sticky `ATTACK` tasks — was **not** reproduced on `main`. It is closed as a
measured non-defect for its own premise. The 851-tick hold it *discovered* while measuring is real, and has
a different cause, recorded here.

**Traced by `rpg-implementer`** (`probes/posture_check.py`, `frontier_living_world`, seed 42, `audit_mode`
with the budget disabled, entity 34 vs target 11, t155-t175 plus the full verdict list):

- t157: posture is `probe` (a risk-ACCEPTED posture), so the attack dispatches and **legitimately** fails
  `OUT_OF_RANGE`. This is correct behaviour, not the defect.
- t161: posture flips to `avoid`, t165 to `retreat`, and stays risk-rejected thereafter.
- From t161 the posture gate at `src/engine/domain/action_router.py:101-102` returns
  `{entity.id: EntityUpdate(entity_id=entity.id, readiness_delta=0.0)}` — **a bare no-op with no failure** —
  every tick, never reaching `CombatActions.execute_attack`.
- `actions.py` sees no failure, so it annotates `outcome: SUCCESS` while carrying the **stale**
  `reason: OUT_OF_RANGE` from t157, and does not clear the task.
- The scheduler keeps re-dispatching the payload-bearing `ENTITY_ACT`, which does nothing, **from t161 until
  the target dies at t1008 — about 851 ticks.** Readiness was back at 100 from t163 throughout.

**The gate itself is correct and must not be removed.** Its own comment (`action_router.py:80-93`) explains
why it lives here rather than in `tactical.py`: the scheduler re-executes an already-set task every tick
*without* calling `evaluate_entity_intent`, so a gate at the decision point is bypassed for **93.7% of real
attacks** (measured, reference scenario); an earlier `tactical.py` version was removed rather than
superseded, to avoid two parallel implementations. **The policy is right; the return shape is wrong.**

**This is a class, not one path.** At least two no-op returns in the same function share the shape:
- `:101-102` — the posture gate.
- `:113-116` — the final fall-through for an unrecognised action.
A readiness-related no-op is also suspected on the same episode (no verdict at t158-t160 while posture was
accepted and the target adjacent, before readiness returned to 100 at t163) and is **unconfirmed**.

**Why P1.** It silently burns an entity's task slot for arbitrarily long, it corrupts the verdict stream with
a false `SUCCESS` plus a stale `reason`, and by the gate's own 93.7% figure the posture path is the dominant
route into action dispatch — so the exposure is plausibly large. **The rate is NOT established**: one entity,
one episode.

## Scope
1. **Enumerate every return path in `ActionRouter.execute_action` that returns without reporting a failure.**
   Produce the list before fixing anything; the two named above are a starting point, not the answer.
2. **Confirm or refute the suspected readiness no-op** on the t158-t160 window of the traced episode. If it is
   a third instance, it belongs in the same fix.
3. **Direction (planner-ruled, see Assumptions): give each withheld action a typed `ReasonCode`** so the no-op
   becomes an explicit, reported failure and `actions.py`'s existing unrecoverable-clear branch ends the task.
   Do **not** add a second task-termination path when that branch already exists.
4. **Fix the false annotation.** `actions.py` must not annotate `outcome: SUCCESS` when nothing executed, and
   must not carry a `reason` from an earlier tick's verdict into a later annotation. The stale-`reason`
   survival is its own defect and should be fixed even where the outcome is correct.
5. **Measure the exposure** after the fix: how many entity-ticks across the corpus were being spent on held
   tasks that execute nothing, before and after. This is the number that tells the owner whether the 93.7%
   comment implies a large effect.
6. **Tests with a disabling control**: with the new reporting disabled, exactly the "a withheld attack ends
   the task" tests fail and every "must not change" test passes — including one asserting that a
   risk-ACCEPTED posture still dispatches, and one asserting that **absence** of a recorded posture still does
   not withhold (the gate's documented behaviour).
7. Update `docs/engine/` and `docs/parity_ledger/` for the action-dispatch subsystem, and record the
   divergence.

## Out of Scope
- **Removing or loosening the posture gate.** The policy is correct and deliberately sited; only its return
  shape and the resulting annotation are in scope.
- `src/engine/scheduler.py` — **CONTESTED, not granted.** The scheduler re-dispatching a set task is the
  documented Sticky-Task Law working as designed; the defect is that nothing ends the task.
- The flee gate / trauma mapping, and gate 4 (`BRACKETING`). Separate tickets. Note the posture values driving
  this (`avoid`, `retreat`, `panic_flee`) come from the same appraisal path as the flee gate, so the two
  interact — but do not fold them together.
- Re-opening `TCK-20261005-STICKY-ATTACK-...OUT-OF-RANGE`. Its premise was tested and not reproduced.

## Acceptance Criteria
- [x] Complete list of non-failure return paths in `ActionRouter.execute_action`.
- [x] The suspected readiness no-op confirmed or refuted on the t158-t160 window.
- [x] A withheld action reports a typed `ReasonCode`; the task is cleared by the existing unrecoverable branch.
- [x] `actions.py` no longer annotates `SUCCESS` when nothing executed, and no longer carries a stale `reason`
      across ticks.
- [x] A risk-ACCEPTED posture still dispatches; absence of a recorded posture still does not withhold. Both
      pinned by test.
- [x] Disabling-control result recorded.
- [x] Held-task exposure measured before and after, corpus-wide, under `audit_mode` with the budget disabled.
- [x] `docs/engine/` + `docs/parity_ledger/` updated; divergence recorded.
- [x] The 851-tick episode re-measured after the fix and reported.

## Related Tickets
- `TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES` — the ticket whose
  measurement found this; **closed as a non-defect for its own premise**, superseded here.
- `TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK` (#347) — gate 1, the
  pursuit half of the sticky-task family.
- `TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION` — gate 4.
- `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE` — supplies the appraisal
  that produces `avoid`/`retreat` postures.
- `TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET` — the one task-clearing path that does exist, and the
  branch this fix should reuse.

## Related Docs
- `docs/engine/kernel.md` — the Sticky-Task Law; the scheduler's behaviour here is correct per that law.
- `docs/engine/authoritative_pipeline.md` and the action-dispatch contract.
- `docs/combat/observability_rulebook.md` — a false `SUCCESS` in the verdict stream is an observability defect
  as much as a behavioural one.

## Related Stored Artifacts
- `probes/posture_check.py` and `probes/oor_follow.py` from the sticky-`ATTACK` ticket — the trace that
  produced this. Extend rather than rebuild.

## Related Code Areas
- `src/engine/domain/action_router.py:80-116` — the gate, its rationale comment, and both no-op returns.
- `src/engine/pipeline_phases/actions.py:221-230` — the annotation and the unrecoverable-clear branch.
- `src/core/enums.py` — `ReasonCode` (89 members today).

## Assumptions / Open Questions
- **Lane.** Lane A. **Hold granted by the planner on `src/engine/domain/action_router.py`**, plus
  `docs/engine/` and `docs/parity_ledger/` for the same subsystem per the standing ruling.
- **Planner ruling on direction, with the reasoning, so it is not re-litigated:** the typed-`ReasonCode`
  option is preferred over simply ending the task with an empty payload. Ending the task silently would fix
  the hold but leave the system unable to say *why* an attack did not happen — and the gate's own 93.7%
  claim lives in a comment precisely because nothing emits a verdict for a withheld attack. A typed reason
  fixes the hold, repairs the verdict stream, and reuses the existing clear branch instead of adding a second
  termination path. **Verified before ruling: `ReasonCode` is not registry-governed or ratcheted** — no
  `tools/gate_checks/*` references it — so adding a member needs no owner sign-off.
- Open: does any consumer treat `outcome: SUCCESS` from a withheld attack as a real attack today? If so,
  fixing the annotation changes their behaviour, and that is a behavioural change needing its own note.
- Open: the gate reads `entity.identity.properties["last_combat_posture"]` keyed against
  `last_combat_posture_target`. A stale posture toward a since-changed target would withhold wrongly; not
  investigated.

## Implementation Notes
Planner-ruled direction followed: a typed `ReasonCode`, reusing `actions.py`'s existing unrecoverable-clear branch rather than a
second termination path. `ReasonCode` gains `ACTION_WITHHELD_BY_POSTURE` and `UNSUPPORTED_ACTION` (no gate or registry pins the
enum). The router's two bare no-op returns (the posture gate, the fall-through) now return
`NavigationUpdate(failure_reason=...)` with `readiness_delta=0.0`, the shape the readiness check and `execute_attack`'s rejections already
use. `route()` clears the task for either reason whatever the action kind (the branch was `ATTACK`+`TARGET_INCAPACITATED` only), the
rejection is counted and audited, and a `reason` sitting beside an `outcome` is dropped before the new annotation is written (a
decision-time `reason` with no `outcome` is kept). The posture gate's policy is untouched.

Answers recorded in `investigation.md`: the router has exactly two bare no-op returns, both fixed; **handler-internal no-ops were not
enumerated**. The suspected readiness no-op on t158-t160 is **refuted** (readiness 60-80, so `scheduler.py:73` never dispatched the
entity; there was no return path). No consumer treats an `ATTACK`/`SKILL` payload `outcome` as a real attack (`clan_lifecycle.py:55` reads
it for `JOIN_CLAN`/`LEAVE_CLAN` only). A stale posture toward the same target persists until `CombatEngagementPhase` rewrites it: not
investigated further. The fall-through was reached by no action in four corpus worlds (sample).

Exposure (values, matched pairs, seed 42, 2000 ticks, `audit_mode`, budget disabled), before to after: `frontier_living_world` withheld
entity-ticks 844 to 2, longest held run 839 to 1, `ATTACK` dispatches 1693 to 8, total dispatches 2862 to 1177; `dungeon_crawl` 4 to 2,
longest run 4 to 1; `crowded_frontier` and `urban_political` 0 `ATTACK` dispatches both ways. **One world carries the effect; this is not
a rate elsewhere, and the "93.7%" in the router comment is a different measurement that these figures do not imply.** The original
episode re-traced (sample): attacker 34 attacks target 11 legally at t166, target incapacitated at t177 (before: alive until t1008).
Side note: every dispatch is seen twice per tick by the documented two-pass design (`COMB-307`), unchanged.

Strategic intelligence and the inspector read `navigation.last_failure_reason`, so a withheld attack now sets it once per dispatch (the
task is then cleared); `execute_attack`'s own rejections already did the same, and the regression sweep is green, but the strategic
side effect was not measured separately.

## Test Summary
`tests/unit/actions/test_action_routing_withheld_action.py`: 16 tests. Three disabling controls, each restored with `git checkout`:
posture reporting removed fails exactly the 6 withheld-clears tests (21 others pass, including
`tests/mechanic_scenarios/test_combat_judgement_withdrawal.py`); stale-reason filter removed fails exactly 1 (24 pass); any-action clear
removed fails exactly 6 (19 pass). Must-not-change pins: 4 risk-accepted postures dispatch, absent and other-target posture do not
withhold, decision-time `reason` kept, dead-target branch unchanged. Regression
(`tests/unit/actions tests/unit/combat tests/unit/engine tests/mechanic_scenarios tests/architecture -m "not slow"`): 629 passed,
1 skipped, 4 deselected. `tests/tools/test_generate_registry.py::...test_check_flag_detects_no_drift_against_real_registry` failed locally before main's #350
(the registry regenerated in place and indexed Lane B's untracked ticket file); after merging main it passes, and a clean-export
`generate_registry.py --check` also reported "In sync". `tests/codebase` needs `ast-grep`/`mypy`, which this environment lacks (see Review notes).

## Files Changed
- `src/core/enums.py`, `src/engine/domain/action_router.py`, `src/engine/pipeline_phases/actions.py`
- `tests/unit/actions/test_action_routing_withheld_action.py` (new)
- `docs/mechanics/02_combat_laws.md`, `docs/engine/kernel.md`, `docs/guidelines/intentional_divergences.md` (2.69),
  `docs/parity_ledger/combat_movement.yaml` (`COMB-330`), `docs/REGISTRY.yaml`
- probes and records under `agent-working/stored_artifacts/` (`withheld_exposure.py`, `exposure.sh`, `fallthrough_actions.py`, `regress.sh`)

## Completion Summary
A dispatched action that did nothing (the combat-posture gate, an unrecognised action) is now reported as a typed failure and ends its
task, so the brain re-decides; the annotation no longer says SUCCESS for it or carries a stale reason. The held-task exposure in
`frontier_living_world` fell from 844 entity-ticks (one run of 839) to 2. Not established: the rate outside the four corpus worlds, and
whether handler-internal paths return the same bare no-op.
