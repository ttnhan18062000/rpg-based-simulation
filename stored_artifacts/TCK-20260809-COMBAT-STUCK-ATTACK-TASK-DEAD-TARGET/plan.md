---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan — TCK-20260809-COMBAT-STUCK-ATTACK-TASK-DEAD-TARGET

## Real fix: reset the task to idle on an unrecoverable `ATTACK` failure

In `src/engine/pipeline_phases/actions.py::route()`, the real outcome-annotation site (around
line 190-195, currently):
```python
if is_survival and outcome == "SUCCESS":
    annotated_task = replace(task_upd, payload_set={})
else:
    annotated_task = replace(task_upd, payload_set={**payload, "outcome": outcome, **({"reason": reason_value} if reason_value else {})})
```
becomes:
```python
is_unrecoverable_attack_failure = (
    action == "ATTACK" and outcome == "FAILURE"
    and reason_value == ReasonCode.TARGET_INCAPACITATED
)
if (is_survival and outcome == "SUCCESS") or is_unrecoverable_attack_failure:
    annotated_task = replace(task_upd, payload_set={})
else:
    annotated_task = replace(task_upd, payload_set={**payload, "outcome": outcome, **({"reason": reason_value} if reason_value else {})})
```
Real, minimal, additive: only the specific, confirmed-unrecoverable `TARGET_INCAPACITATED`
failure on `ATTACK` gets the reset. `INSUFFICIENT_READINESS`/`OUT_OF_RANGE`/other failure reasons
keep their existing behavior (retry via the readiness gate / next fresh decision), since those
are real, recoverable conditions — resetting on every failure would be a bigger, less-justified
behavior change than this ticket's own confirmed, narrow finding supports.

## What is deliberately NOT touched
- `SystemCadence.strategic_intelligence`'s own cadence mechanism — untouched.
- The 2-pass Collection/action_routing architecture (`Kernel._phase_collection` +
  `AuthoritativeApplyPipeline._route_action_intent`) — confirmed legitimate, not a bug, not
  touched.
- `combat_actions.py::execute_attack()`'s own real `-50.0` readiness penalty on illegal-target
  failures — untouched; this fix stops the *repeated* penalty from compounding uselessly against
  a target that can never become legal again, without changing the penalty itself for a target
  that might still become legal (e.g. `OUT_OF_RANGE`, resolvable by movement).
- `INSUFFICIENT_READINESS`/`OUT_OF_RANGE` failure handling — deliberately left un-reset; these
  are real, recoverable conditions where retrying is not futile the way `TARGET_INCAPACITATED`
  is.

## Rejected alternative
- **Resetting on ANY `ATTACK` failure, not just `TARGET_INCAPACITATED`**: rejected — this
  ticket's own real evidence only demonstrates the stuck-task problem for the unrecoverable case;
  resetting on `OUT_OF_RANGE`/`INSUFFICIENT_READINESS` too would force every attack attempt back
  through the ~10-tick brain-cadence gate even when the target is still legally attackable and
  readiness/range would naturally resolve sooner — a real, unjustified regression risk for a
  case this ticket's own investigation didn't establish is even broken.

## Verification plan
1. Unit test in `tests/unit/pipeline_phases/` (or wherever `actions.py::route()`'s own existing
   tests live — confirm exact location during Implement) covering: `ATTACK` +
   `TARGET_INCAPACITATED` → task reset to idle (`payload_set={}`); `ATTACK` +
   `INSUFFICIENT_READINESS`/`OUT_OF_RANGE` → payload preserved (existing behavior unchanged);
   `EAT`/`REST`/`SLEEP` success → still resets (existing behavior unchanged, regression guard).
2. Full scoped pytest: wherever `actions.py`'s own existing tests live, plus
   `tests/unit/combat/`, `tests/unit/tactical/`.
3. Real corpus re-verification (2000-tick live `Kernel.tick_once()` loop,
   `dungeon_crawl_seed42`/`urban_political_seed42`, corpus-default flags, multiple clean re-runs
   given this session's own repeatedly-observed real run-to-run variance): confirm
   `TARGET_INCAPACITATED` volume drops materially — the fix should convert the observed
   180+-tick real repetition into at most 1-2 real occurrences per (attacker, dead-target) pair
   before the entity re-targets.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md re-confirms real mechanism + quantifies scope | Done |
| Concrete, minimal fix designed and implemented | This plan + Implement phase |
| Real corpus re-verification shows material drop | Test phase |
| Scoped pytest passes | Test phase |
