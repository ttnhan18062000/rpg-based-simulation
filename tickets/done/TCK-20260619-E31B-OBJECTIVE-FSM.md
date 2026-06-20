---
status: done
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E31B-OBJECTIVE-FSM
phase: done
date: 2026-06-20
tags: [scenario-runtime, objective-state-machine, stall-detector, phase-3]
---

# TCK-20260619-E31B-OBJECTIVE-FSM

## Title
Epic 3.1B · Objective State Machine + Stall Detector

## Status
DONE

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

## Implementation Notes

### E31B deviations from ticket pseudocode

1. **`e.is_alive` → `e.combat.alive`**: Ticket pseudocode used `e.is_alive` which does not
   exist on `EntityState`. Fixed to `e.combat.alive` per investigation.md Risk 2.

2. **Mock kernel int() guard**: `getattr(kernel, "_current_tick_event_count", 0)` returns a
   MagicMock on mock kernels (attribute auto-created). Added `try: int(...)` cast to safely
   handle test environments without impacting production behavior.

3. **Step() terminal guard split**: Instead of one combined terminal-states check (which would
   change the error message for ABORTED and break existing `match="aborted"` tests), the
   ABORTED check retains the original message and the new objective/stall states use a distinct
   `"terminal state"` message.

4. **E31A regression update**: `test_start_runs_100_ticks_without_error` was updated to
   `test_start_runs_ticks_without_error` with `tick_limit=STALL_THRESHOLD`. An empty-world
   real kernel produces zero events per tick, so the stall detector fires at tick 51. Capping
   at 50 is the correct regression test for "runs N ticks without error" under E31B semantics.

5. **Integration tests use mock kernels** (where possible) to avoid slow real-kernel spin-up.
   Only `test_scenario_reaches_objective_met` uses a real kernel and is marked `@pytest.mark.slow`.

### Stall detector simplification

All event kinds count toward the stall counter reset (per investigation.md §Stall Detector).
No per-category filtering is applied; any `_current_tick_event_count > 0` resets the counter.
This is documented in `_evaluate_after_tick()` docstring.

## Test Summary
```bash
pytest tests/integration/scenarios/test_scenario_runtime_service.py -v          # 20 passed
pytest tests/unit/engine/test_objective_evaluator.py -v                          # 17 passed
pytest tests/unit/engine/test_scenario_runtime_service.py -v                     # 30 passed (regression)
```

## Files Changed
- `src/engine/scenario_runtime.py` — Added `STALL_THRESHOLD`, `ObjectiveEvaluator`, extended
  `__slots__`, added `_evaluate_after_tick()`, wired into `_run_loop()` and `step()`, extended
  terminal state guard on `step()`.
- `tests/unit/engine/test_scenario_runtime_service.py` — Updated `test_start_runs_100_ticks_without_error`
  to `test_start_runs_ticks_without_error` (tick_limit=50) for stall-aware behavior.
- `tests/unit/engine/test_objective_evaluator.py` — New: 17 fast unit tests for ObjectiveEvaluator.
- `tests/integration/scenarios/test_scenario_runtime_service.py` — New: 20 integration tests
  covering all 5 acceptance criteria.
- `docs/parity_ledger/infrastructure.yaml` — Updated INFRA-214: added ObjectiveEvaluator,
  STALL_THRESHOLD, stall detector behavior, new test paths.

## Completion Summary
Implemented `ObjectiveEvaluator` (pure static), stall detector (`STALL_THRESHOLD=50`), and
`_evaluate_after_tick()` wired into both `_run_loop()` and `step()`. All 5 ACs verified: 67
tests pass (30 unit regression + 17 unit new + 20 integration). INFRA-214 parity ledger updated.
