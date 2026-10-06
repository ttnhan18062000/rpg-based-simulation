---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-SILENT-NO-OP-RETURNS-IN-ACTIONROUTER-HOLD-THE-TASK-AND-ANNOTATE-FALSE-SUCCESS
artifact_type: investigation
tags: [engine, combat, observability]
---

# Investigation: silent no-op returns in ActionRouter.execute_action

Origin: the 851-tick hold found while measuring `TCK-20261005-STICKY-ATTACK-TASK-SURVIVES-OUT-OF-RANGE-AFTER-THE-TARGET-MOVES`
(see that ticket's `investigation.md` for the trace, `probes/posture_check.py`). Tree: `origin/main` `7a9f302db` plus ticket files.
Measurement settings: real `Kernel.tick_once()`, seed 42, 2000 ticks, `audit_mode=True`, `max_tick_budget_ms=1e9`, one simulation
at a time; "value" = the identical run repeated and matched, "sample" = one run.

## Scope 1: return paths of `ActionRouter.execute_action` (`src/engine/domain/action_router.py`)
| path | returns | reports a failure? |
|---|---|---|
| `SLEEP`/`EAT`/`REST` | `CoreActions.execute_survival` | handler-defined (real effect) |
| readiness not 100 | `NavigationUpdate(failure_reason=r_reason)` | **yes** |
| `RECRUIT`/`TEAM_UP`/`TRADE`/`ALLOCATE_AP`/`TRAIN`/`PROPOSE_MARRIAGE`/`JOIN_CLAN`/`LEAVE_CLAN`/`REPAIR`/`INTERACT` | the handler's result | handler-defined |
| `ATTACK`/`SKILL` with a risk-rejected posture toward that target | bare `EntityUpdate(readiness_delta=0.0)` | **no (fixed: `ACTION_WITHHELD_BY_POSTURE`)** |
| `ATTACK` / `SKILL` / `AOE_ATTACK` | `execute_attack` / `execute_skill` / `execute_aoe_attack` | handler-defined (`execute_attack` reports) |
| anything else (fall-through) | bare `EntityUpdate(readiness_delta=0.0)` | **no (fixed: `UNSUPPORTED_ACTION`)** |
The router itself had exactly two bare no-op returns; both are now reported. **Not enumerated:** whether individual handlers
(`execute_interact`, `execute_repair`, ...) return a bare no-op on their own internal paths. The fall-through was reached by no action
in any of the four corpus worlds (sample, one run each: 0 `UNSUPPORTED_ACTION`), so no recognised action relied on it.

## Scope 2: the suspected readiness no-op on t158-t160: refuted
Entity 34's readiness at t158/t159/t160 was 60/70/80 (< 100). `scheduler.py:73` skips every non-brain work item with
`readiness < 100.0`, so the entity was **not dispatched at all** on those ticks; there was no return path to be silent. The router's own
readiness check would also have reported a failure. Not a third instance.

## Open questions from the ticket
- Does any consumer treat a withheld attack's `outcome: SUCCESS` as a real attack? The only reader of a task payload `outcome` outside
  `actions.py` is `pipeline_phases/clan_lifecycle.py:55`, for `JOIN_CLAN`/`LEAVE_CLAN` only. No consumer for `ATTACK`/`SKILL`. The
  annotation fix changes no consumer's behaviour; the behavioural change is the task now ending.
- Stale posture toward a since-changed target: the gate compares `last_combat_posture_target` with the payload `target_id`, so a posture
  recorded for another target never withholds (pinned by test). A stale posture toward the *same* target persists until
  `CombatEngagementPhase` rewrites it; not investigated further.

## Side finding: the same dispatch is seen twice per tick
`withheld.same_tick_duplicate` = 842 of 1686 withheld dispatches in `frontier_living_world`: every dispatch is checked twice per tick.
This is the documented two-pass Collection / refinement design (parity entry `COMB-307`), unchanged and not a defect.

## Scope 5: exposure (values, matched pairs), before = this ticket's parent tree, after = this change
| world | ATTACK dispatches | withheld entity-ticks | entities | longest held run (ticks) | total dispatches |
|---|---|---|---|---|---|
| crowded_frontier | 0 / 0 | 0 / 0 | 0 / 0 | none | 704 / 704 |
| frontier_living_world | 1693 / 8 | 844 / 2 | 2 / 2 | 839 / 1 | 2862 / 1177 |
| urban_political | 0 / 0 | 0 / 0 | 0 / 0 | none | 869 / 869 |
| dungeon_crawl | 11 / 2 | 4 / 2 | 1 / 1 | 4 / 1 | 11 / 2 |
(`probes/withheld_exposure.py`, `probes/exposure.sh before|after`). Trajectories diverge once an entity re-decides, so the columns are
population comparisons, not per-entity. The 1685 fewer dispatches in `frontier_living_world` match the 1686 withheld ones. The
93.7% comment in `action_router.py` is a different measurement (metropolis scenario) and is **not** implied by these figures.
The original episode, re-traced after the change (`oor_follow.py`, sample): attacker 34 attacks target 11 legally at t166 and the target
is incapacitated at t177; before, the target lived until t1008.
