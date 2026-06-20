---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E31B-OBJECTIVE-FSM
phase: open
date: 2026-06-20
tags: [scenario-runtime, objective-state-machine, stall-detector, phase-3]
---

# TCK-20260619-E31B-OBJECTIVE-FSM

## Title
Epic 3.1B · Objective State Machine + Stall Detector

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`ScenarioRuntimeService` (E31A) has `objective_state` but no evaluation logic. This ticket wires `victory_conditions` evaluation: at each tick, check if any condition is met → transition to OBJECTIVE_MET/FAILED; stall detector fires when no meaningful events for N ticks → STALLED.

**Requires:** TCK-20260619-E31A-SCENARIO-SERVICE

## Scope

### 1. `ObjectiveEvaluator` — evaluates `victory_conditions` per tick

```python
class ObjectiveEvaluator:
    @staticmethod
    def evaluate(state: AuthoritativeState, conditions: list[dict]) -> ScenarioObjectiveState:
        for cond in conditions:
            if cond["kind"] == "tick_limit" and state.tick >= cond["value"]:
                return ScenarioObjectiveState.OBJECTIVE_MET
            if cond["kind"] == "entity_count" and len([e for e in state.entities.values() if e.is_alive]) < cond["value"]:
                return ScenarioObjectiveState.OBJECTIVE_FAILED
            # add more condition kinds as needed
        return ScenarioObjectiveState.RUNNING
```

### 2. Stall detector

In `ScenarioRuntimeService`: track `_last_event_tick`. After each tick, if `simulation_events` produced zero meaningful events (combat/quest/harvest/death — not just idle ticks), increment stall counter. If stall counter > STALL_THRESHOLD (default: 50 ticks), set `STALLED`.

### 3. Wire evaluator into `ScenarioRuntimeService.step()`

After each tick: call `ObjectiveEvaluator.evaluate()` and update `_state`. If no longer RUNNING, call `kernel.shutdown()`.

## Acceptance Criteria
- Scenario with `victory_conditions: [{kind: tick_limit, value: 50}]` reaches OBJECTIVE_MET at tick 50
- Scenario with all entities dead reaches OBJECTIVE_FAILED
- STALLED fires when no meaningful events for STALL_THRESHOLD ticks
- `test_scenario_reaches_objective_met` passes
- `test_stall_detector_fires_on_no_events` passes

## Related Tickets
- TCK-20260619-E31-SCENARIO-RUNTIME (parent epic)
- TCK-20260619-E31A-SCENARIO-SERVICE (required)
- TCK-20260619-E31C-CHECKPOINT (blocked on this)

## Related Code Areas
- `src/engine/scenario_runtime.py` (extend with ObjectiveEvaluator)
- `tests/integration/scenarios/test_scenario_runtime_service.py`

## Test Summary
```bash
pytest tests/integration/scenarios/test_scenario_runtime_service.py -x -v -m slow
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
