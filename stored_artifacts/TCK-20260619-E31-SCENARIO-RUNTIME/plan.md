---
ticket_id: TCK-20260619-E31-SCENARIO-RUNTIME
phase: plan
date: 2026-06-20
---

# Plan: Scenario Runtime Service — Epic Scope

## Child Ticket Sequence

```
E31A (ScenarioRuntimeService + kernel lifecycle)
  └──► E31B (objective state machine)
         └──► E31C (checkpoint/restore)
                └──► E31D (REST API)
```

Sequential — each builds on prior.

## Child Ticket Summary

| Ticket | Scope | Key Deliverable |
|---|---|---|
| E31A | `ScenarioRuntimeService` class wrapping `Kernel`; start/pause/resume/step/abort; `victory_conditions` in scenario schema | `src/engine/scenario_runtime.py` (new) |
| E31B | Objective state machine: RUNNING→OBJECTIVE_MET/OBJECTIVE_FAILED/STALLED/ABORTED; stall detector; condition evaluator | `src/engine/scenario_objectives.py` (new) |
| E31C | Full-state checkpoint: serialize `AuthoritativeState` + RNG to file; restore to fresh service | Checkpoint serializer in `src/engine/` |
| E31D | 3 REST endpoints: GET status, POST checkpoint, POST restore | `src/api/routes/scenarios.py` (new) |

## Acceptance Path

1. E31A: `ScenarioRuntimeService(spec).start()` runs 100 ticks and is pauseable
2. E31B: scenario with `victory_conditions: [{kind: "tick_limit", value: 100}]` reaches OBJECTIVE_MET
3. E31C: checkpoint at tick 50, restore, run to 100 → identical events as uninterrupted run
4. E31D: `GET /api/v1/scenarios/{id}/status` returns live `{tick, alive_entities, objective_state}`
