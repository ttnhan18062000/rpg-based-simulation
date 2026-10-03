---
ticket_id: TCK-20260619-E31B-OBJECTIVE-FSM
phase: plan
date: 2026-06-20
---

# Implementation Plan — TCK-20260619-E31B-OBJECTIVE-FSM
## Epic 3.1B · Objective State Machine + Stall Detector

---

## Files to Modify

| File | Change |
|---|---|
| `src/engine/scenario_runtime.py` | Add `STALL_THRESHOLD`, `ObjectiveEvaluator`, extend `ScenarioRuntimeService.__slots__`, wire into `_run_loop()` and `step()` |
| `docs/parity_ledger/infrastructure.yaml` | Update INFRA-214: add `ObjectiveEvaluator` to `v2_evidence`, update `text`, update `test_path` |

## Files to Create

| File | Purpose |
|---|---|
| `tests/integration/scenarios/test_scenario_runtime_service.py` | AC integration tests (per ticket spec) |
| `tests/unit/engine/test_objective_evaluator.py` | Fast unit tests for `ObjectiveEvaluator` (recommended addition) |

---

## Step-by-Step Plan

### Step 1 — Extend `__slots__` on `ScenarioRuntimeService`

In `src/engine/scenario_runtime.py`, line 55:

```python
__slots__ = ("_spec", "_kernel", "_state", "_tick", "_paused",
             "_stall_counter", "_last_event_tick")
```

Initialize in `__init__`:
```python
self._stall_counter: int = 0
self._last_event_tick: int = 0
```

### Step 2 — Add `STALL_THRESHOLD` constant

At module level, after imports:
```python
STALL_THRESHOLD: int = 50
```

### Step 3 — Implement `ObjectiveEvaluator`

Pure static class, no kernel reference. `conditions` accepts `list[dict]` (or `None`):

```python
class ObjectiveEvaluator:
    @staticmethod
    def evaluate(
        state: AuthoritativeState,
        conditions: list[dict] | None,
    ) -> ScenarioObjectiveState:
        if not conditions:
            return ScenarioObjectiveState.RUNNING
        for cond in conditions:
            kind = cond.get("kind") if isinstance(cond, dict) else cond.kind
            value = cond.get("value") if isinstance(cond, dict) else cond.value
            if kind == "tick_limit" and state.tick >= value:
                return ScenarioObjectiveState.OBJECTIVE_MET
            if kind == "entity_count":
                alive = sum(1 for e in state.entities.values() if e.combat.alive)
                if alive < value:
                    return ScenarioObjectiveState.OBJECTIVE_FAILED
        return ScenarioObjectiveState.RUNNING
```

Note: `VictoryCondition` is a Pydantic frozen model; when iterating `spec.victory_conditions`,
use attribute access (`cond.kind`, `cond.value`). The `dict` branch is for test convenience.
The safest approach: call `ObjectiveEvaluator.evaluate(state, list(spec.victory_conditions))`
where `spec.victory_conditions` is already a `list[VictoryCondition]`. The evaluator accesses
`.kind` and `.value` directly (both models and dicts with those keys work via `getattr`).

### Step 4 — Add `_evaluate_after_tick()` method

Internal helper called after each `tick_once()` invocation:

```python
def _evaluate_after_tick(self) -> None:
    """Evaluate objective conditions and stall detector after each tick.

    Mutates self._state if a terminal condition is reached. Sets self._paused
    to True to break _run_loop(). Does not call kernel.shutdown() — callers
    use abort() for cleanup.
    """
    # 1. Objective evaluation (takes priority over stall)
    conditions = self._spec.victory_conditions
    if conditions:
        result = ObjectiveEvaluator.evaluate(
            self._kernel.state,
            list(conditions),
        )
        if result != ScenarioObjectiveState.RUNNING:
            self._state = result
            self._paused = True
            return

    # 2. Stall detector
    event_count = getattr(self._kernel, "_current_tick_event_count", 0)
    if event_count > 0:
        self._stall_counter = 0
        self._last_event_tick = self._tick
    else:
        self._stall_counter += 1
        if self._stall_counter > STALL_THRESHOLD:
            self._state = ScenarioObjectiveState.STALLED
            self._paused = True
```

### Step 5 — Wire into `_run_loop()` and `step()`

In `_run_loop()`, after `self._tick += 1`:
```python
self._evaluate_after_tick()
```

In `step()`, after `self._tick += 1`:
```python
self._evaluate_after_tick()
```

Also add terminal state guard at the top of `step()`:
```python
if self._state not in (ScenarioObjectiveState.RUNNING, ScenarioObjectiveState.ABORTED):
    # Already handled: ABORTED guard is already there; extend to cover OBJECTIVE_* and STALLED
    raise RuntimeError(f"Cannot step a scenario in terminal state: {self._state}.")
```
(Adjust the existing ABORTED check to cover all non-RUNNING terminal states.)

### Step 6 — Write tests

1. `tests/integration/scenarios/test_scenario_runtime_service.py` — as specified in test_plan.md
2. `tests/unit/engine/test_objective_evaluator.py` — fast unit tests for `ObjectiveEvaluator`

### Step 7 — Update INFRA-214

In `docs/parity_ledger/infrastructure.yaml`, line 2419–2428:
- Append to `text`: mention `ObjectiveEvaluator`, stall detector, `STALL_THRESHOLD`.
- Append to `v2_evidence`: `+ src/engine/scenario_runtime.py::ObjectiveEvaluator + src/engine/scenario_runtime.py::STALL_THRESHOLD`.
- Append to `test_path`: `+ tests/integration/scenarios/test_scenario_runtime_service.py::TestObjectiveMet::test_scenario_reaches_objective_met`.

---

## Scope Boundaries

In scope:
- `ObjectiveEvaluator` class in `src/engine/scenario_runtime.py`
- Stall detector on `ScenarioRuntimeService`
- Two new test files
- INFRA-214 parity update

Out of scope (E31C, E31D):
- Checkpoint/restore
- REST API layer
- Serialization of `ScenarioObjectiveState` to JSON endpoints

---

## Deviations from Plan

1. **Mock kernel int() guard**: `getattr(kernel, "_current_tick_event_count", 0)` wraps in
   `try: int(...)` because MagicMock kernels in unit tests return a MagicMock attribute (not
   the default 0), causing a `TypeError` on `> 0` comparison. Production behavior is unchanged.

2. **step() terminal guard split**: Plan said "adjust the existing ABORTED check to cover all
   non-RUNNING terminal states." Instead, the ABORTED guard retains its original message
   (`"aborted"`) to avoid breaking 3 existing `match="aborted"` tests. A separate check covers
   OBJECTIVE_MET / OBJECTIVE_FAILED / STALLED with a `"terminal state"` message.

3. **E31A test update**: `test_start_runs_100_ticks_without_error` renamed and updated to use
   `tick_limit=STALL_THRESHOLD` (50). A real zero-entity kernel produces zero events; the stall
   detector correctly fires at tick 51. This is a necessary behavioral consequence, not a bug.
   Documented in Implementation Notes.

4. **Integration tests use mock kernels by default**: Plan did not specify this, but using mock
   kernels for all tests except the `@pytest.mark.slow` real-kernel test avoids 10+ second
   kernel spin-up per test. The slow test still exercises the full real-kernel path.
