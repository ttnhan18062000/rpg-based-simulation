---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261005-ACTION-HANDLERS-MAY-RETURN-BARE-NO-OPS-THAT-HOLD-THE-TASK
artifact_type: investigation
tags: [engine, investigation]
---

# Investigation: can an action handler return a bare no-op on a HELD task?

Answer: **no reachable instance.** Nothing is fixed; the ticket closes as a measured non-defect.

## 1. What can be a held task

A held task is an `ENTITY_ACT` whose payload carries an `action`. In `src/`, only `tactical.py` writes one: `INTERACT` (300), `EAT` (312), `REST` (320), `HOLD` (665), `SKILL` (767), `ATTACK` (784). (`src/certification/scenarios.py` writes `ATTACK` tasks for fixtures only.) The `ActionIntentAdapter` (`src/engine/intent/action_intent.py`) returns updates that set no task, and its callers (`tactical.py` 366/377, `information_intent_execution.py`) use them once, at decision time; its bare returns (105, 155, 257, 289) are therefore decision-time only, never re-dispatched.

## 2. Every non-failure return, by handler

| Handler return | Class | On a held task? |
|---|---|---|
| `execute_survival` final `return {}` | unreachable: router only passes SLEEP/EAT/REST | no |
| `execute_survival` REST (readiness 0, rest pressure -30) | real effect; survival success resets the task to idle (`actions.py` 261) | no |
| `execute_interact` | always an `InteractionUpdate(progress_delta=1)`: a real effect | recurs, but it is progress, not a no-op |
| `execute_attack` final `EntityUpdate(readiness_delta=0.0)` (combat_actions.py 138) | bare, but only when `context` is falsy | no: every production dispatcher passes a non-None context (`actions.py` 196, `executor.py` 152, `worker_logic.py` 42), and no context type defines `__bool__`/`__len__` |
| `execute_skill` | every early exit carries a typed `failure_reason`; the last is a real update | no bare return |
| `execute_aoe_attack` `return updates` (may omit the actor) | would read as `NO_ACTION_UPDATE` (a failure), not bare | no producer of `AOE_ATTACK` exists in `src/` |
| `execute_repair` with nothing to repair (readiness -10) | bare | no held-task producer: only the adapter issues `REPAIR`, setting no task |
| `execute_join_clan` accept / `execute_leave_clan` success | bare by design; the durable write is in `ClanLifecyclePhase` | no held-task producer in `src/` |
| `execute_recruit`, `team_up`, `trade`, `train`, `propose_marriage`, `allocate_ap` | typed failures or real updates | no producer in `src/` |
| `HOLD` (no handler) | was a bare fall-through | already fixed by the parent: `UNSUPPORTED_ACTION` ends the task |

## 3. Measured exposure (probes/handler_exposure.py, probes/exposure_before.log)

`Kernel.tick_once()`, seed 42, 2000 ticks, `audit_mode`, budget disabled, 4 worlds x 2 runs; **all pairs matched (values)**. A run is consecutive dispatches by one entity of the same (action, target) with no other dispatch between (a first version required consecutive ticks and would have hidden a task that repeats every ~5 ticks; it was discarded).

- The corpus dispatches only `ATTACK` and `INTERACT`. No other handler ran in any world.
- **`BARE` dispatches: 0 in every world and action kind** (`bare_in_runs_ge_2` is 0).
- `INTERACT`: 431 / 475 / 521 dispatches (`crowded_frontier` / `frontier_living_world` / `urban_political`), 5 to 7 runs, longest 90, max gap 11, every dispatch an `EFFECT`.
- `ATTACK`: 31 / 21 / 4 / 2 dispatches; longest run 7, 8, 2, 1. Failures are typed (`ACTION_WITHHELD_BY_POSTURE`, `OUT_OF_RANGE`, `TARGET_INCAPACITATED`).

## 3a. Positive control

`probes/classify_control.py` feeds the probe's own `classify` a constructed bare update (`readiness_delta` 0.0 and -10.0), a typed failure, an effect and `None`: it returns `BARE`, `BARE`, `FAIL:UNSUPPORTED_ACTION`, `EFFECT`, `FAIL:NO_ACTION_UPDATE`. The zero bare count is therefore a measured zero, not a classifier that cannot see one.

## 3b. Reproduction note: working directory

`src/core/registries.py` seeds content from the cwd-relative `data/content`, so a probe's result depends on the directory it is started from. The first run of `probes/exposure_before.log` was launched through a script that inherited the harness cwd, a different worktree whose `data/content` differs (`world_modules/*.yaml`). It was re-run with the cwd set to this worktree (`probes/measure.sh` now `cd`s first; `probes/exposure_before_rerun_correct_cwd.log`): **all 14 result lines are identical** to the first run, so the numbers in section 3 stand.

## 4. Limits

- Handlers the corpus never dispatches are cleared by code reading (no `src/` producer), not by measurement.
- The concurrent worker path was not run; its context argument is shown to be non-None by reading.
- Whether an `INTERACT` against a depleted or missing node still counts as progress is not checked here: `execute_interact` does not validate its target, and the 90-dispatch runs end on their own, but the apply path's handling of a missing node was not traced.
