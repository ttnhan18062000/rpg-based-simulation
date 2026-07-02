---
ticket_id: TCK-20260619-E31B-OBJECTIVE-FSM
phase: test_plan
date: 2026-06-20
---

# Test Plan — TCK-20260619-E31B-OBJECTIVE-FSM
## Epic 3.1B · Objective State Machine + Stall Detector

---

## Regression Surface

The following existing tests must continue to pass after E31B changes. They exercise
`ScenarioRuntimeService` internals that E31B modifies (`__slots__`, `_run_loop`, `step`).

| Test file | Suite | Rationale |
|---|---|---|
| `tests/unit/engine/test_scenario_runtime_service.py` | All 7 classes | E31B extends `__slots__`, `_run_loop`, `step` — regressions are likely if these are broken |
| `tests/integration/scenarios/test_scenario_catalog_matrix.py` | All | Exercises scenario schema parsing; VictoryCondition must still parse |
| `tests/integration/scenarios/test_scenario_setup_resolver.py` | All | Scenario setup resolver must not be affected by objective evaluation wiring |

Run regression check before any E31B code changes:

```bash
pytest tests/unit/engine/test_scenario_runtime_service.py -x -v
pytest tests/integration/scenarios/test_scenario_catalog_matrix.py tests/integration/scenarios/test_scenario_setup_resolver.py -x -v
```

---

## New Tests Required

All new tests go in:
`tests/integration/scenarios/test_scenario_runtime_service.py` (new file, does not yet exist)

This matches the ticket AC (`test_scenario_reaches_objective_met`,
`test_stall_detector_fires_on_no_events`) and the ticket's `pytest` command.

### Helper fixtures

```python
def _make_spec(**kwargs):
    from src.scenarios.schema import SimulationScenarioDefinition
    defaults = {
        "id": "test_scenario",
        "world_composition": "frontier_living_world",
        "perspective": "hero_guild_perspective",
    }
    defaults.update(kwargs)
    return SimulationScenarioDefinition(**defaults)

def _make_service(**spec_kwargs):
    from src.engine.scenario_runtime import ScenarioRuntimeService
    return ScenarioRuntimeService(_make_spec(**spec_kwargs))
```

---

### AC1 — tick_limit → OBJECTIVE_MET

**Test:** `test_scenario_reaches_objective_met`
**File:** `tests/integration/scenarios/test_scenario_runtime_service.py`

```python
class TestObjectiveMet:
    def test_scenario_reaches_objective_met(self):
        from src.engine.scenario_runtime import ScenarioObjectiveState
        svc = _make_service(victory_conditions=[{"kind": "tick_limit", "value": 50}])
        try:
            svc.start(tick_limit=100)
            assert svc.objective_state == ScenarioObjectiveState.OBJECTIVE_MET
            assert svc.tick == 50  # loop stops at objective transition, not tick_limit
        finally:
            svc.abort()

    def test_tick_limit_not_yet_reached_stays_running(self):
        from src.engine.scenario_runtime import ScenarioObjectiveState
        svc = _make_service(victory_conditions=[{"kind": "tick_limit", "value": 100}])
        try:
            svc.start(tick_limit=50)
            assert svc.objective_state == ScenarioObjectiveState.RUNNING
            assert svc.tick == 50
        finally:
            svc.abort()

    def test_tick_limit_exact_boundary(self):
        """At tick == value the condition fires."""
        from src.engine.scenario_runtime import ScenarioObjectiveState
        svc = _make_service(victory_conditions=[{"kind": "tick_limit", "value": 10}])
        try:
            svc.start(tick_limit=10)
            assert svc.objective_state == ScenarioObjectiveState.OBJECTIVE_MET
        finally:
            svc.abort()

    def test_step_also_triggers_objective_met(self):
        """step() must evaluate objectives, not just _run_loop()."""
        from src.engine.scenario_runtime import ScenarioObjectiveState
        svc = _make_service(victory_conditions=[{"kind": "tick_limit", "value": 3}])
        try:
            svc.step()
            svc.step()
            svc.step()
            assert svc.objective_state == ScenarioObjectiveState.OBJECTIVE_MET
        finally:
            svc.abort()
```

**Why:** AC states "scenario with `tick_limit: 50` reaches OBJECTIVE_MET at tick 50". The
boundary and exact-tick tests guard against off-by-one in `>=` vs `>` comparison. The `step()`
test guards against evaluation being wired only to `_run_loop`.

---

### AC2 — entity_count → OBJECTIVE_FAILED

**Test:** `test_scenario_reaches_objective_failed`

```python
class TestObjectiveFailed:
    def test_entity_count_condition_fires_when_alive_below_threshold(self):
        """entity_count fires when alive-entity count < condition value."""
        from src.engine.scenario_runtime import ScenarioObjectiveState
        from unittest.mock import MagicMock, patch
        # Use mock kernel so we can control state.entities without full world
        svc = _make_service(victory_conditions=[{"kind": "entity_count", "value": 1}])
        mock_kernel = MagicMock()
        # Simulate zero alive entities
        dead_entity = MagicMock()
        dead_entity.combat.alive = False
        mock_kernel.state.entities = {1: dead_entity}
        mock_kernel._current_tick_event_count = 0
        svc._kernel = mock_kernel
        # Manually invoke one evaluation cycle
        from src.engine.scenario_runtime import ObjectiveEvaluator
        conditions = [c.model_dump() for c in _make_spec(
            victory_conditions=[{"kind": "entity_count", "value": 1}]
        ).victory_conditions]
        result = ObjectiveEvaluator.evaluate(mock_kernel.state, conditions)
        assert result == ScenarioObjectiveState.OBJECTIVE_FAILED

    def test_entity_count_above_threshold_stays_running(self):
        from src.engine.scenario_runtime import ScenarioObjectiveState, ObjectiveEvaluator
        from unittest.mock import MagicMock
        live_entity = MagicMock()
        live_entity.combat.alive = True
        mock_state = MagicMock()
        mock_state.entities = {1: live_entity, 2: live_entity}
        mock_state.tick = 10
        conditions = [{"kind": "entity_count", "value": 1}]
        result = ObjectiveEvaluator.evaluate(mock_state, conditions)
        assert result == ScenarioObjectiveState.RUNNING
```

**Why:** Guards the `e.combat.alive` correctness. A naive `len(state.entities)` check would
give wrong results; these tests enforce the filtering predicate.

---

### AC3 — STALLED fires when no meaningful events for STALL_THRESHOLD ticks

**Test:** `test_stall_detector_fires_on_no_events`

```python
class TestStallDetector:
    def test_stall_detector_fires_on_no_events(self):
        """STALLED fires after STALL_THRESHOLD consecutive ticks with zero events."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, STALL_THRESHOLD
        from unittest.mock import MagicMock
        # Scenario with no victory conditions so objective evaluation never fires
        svc = _make_service()
        mock_kernel = MagicMock()
        mock_kernel.state.entities = {}
        mock_kernel.state.tick = 0
        mock_kernel._current_tick_event_count = 0  # always zero events
        svc._kernel = mock_kernel
        # Manually drive tick loop to threshold
        # (direct invocation to avoid building real kernel)
        for _ in range(STALL_THRESHOLD + 1):
            svc._tick += 1
            svc._after_tick_hook()  # or inline evaluation — depends on implementation
        assert svc.objective_state == ScenarioObjectiveState.STALLED

    def test_stall_resets_when_events_fire(self):
        """A tick with events resets the stall counter."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, STALL_THRESHOLD
        from unittest.mock import MagicMock
        svc = _make_service()
        mock_kernel = MagicMock()
        mock_kernel.state.entities = {}
        mock_kernel.state.tick = 0
        svc._kernel = mock_kernel
        # 49 idle ticks
        mock_kernel._current_tick_event_count = 0
        for _ in range(STALL_THRESHOLD - 1):
            svc._stall_counter += 1  # simulate idle ticks
        assert svc._stall_counter == STALL_THRESHOLD - 1
        # One tick with events resets counter
        mock_kernel._current_tick_event_count = 3
        svc._evaluate_stall()  # or equivalent internal method
        assert svc._stall_counter == 0
        assert svc.objective_state == ScenarioObjectiveState.RUNNING

    def test_stall_threshold_is_50(self):
        from src.engine.scenario_runtime import STALL_THRESHOLD
        assert STALL_THRESHOLD == 50

    def test_stall_not_fired_before_threshold(self):
        """STALL_THRESHOLD - 1 idle ticks do not trigger STALLED."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, STALL_THRESHOLD
        svc = _make_service()
        from unittest.mock import MagicMock
        mock_kernel = MagicMock()
        mock_kernel._current_tick_event_count = 0
        mock_kernel.state.entities = {}
        mock_kernel.state.tick = 0
        svc._kernel = mock_kernel
        svc._stall_counter = STALL_THRESHOLD - 1
        # One more idle tick, but not yet at threshold
        # Simulate one evaluation with zero events
        # (counter goes to STALL_THRESHOLD - 1, not yet > threshold)
        assert svc.objective_state == ScenarioObjectiveState.RUNNING
```

**Note:** The exact method name for the stall evaluation hook (`_after_tick_hook`,
`_evaluate_stall`, or inline in `_run_loop`) is not yet decided. Tests should be written
to match the implementation. The above shows the intent; revise method names during
implementation to match actual API. Unit tests using the internal `_stall_counter` field
are acceptable since this is an integration test file co-owned by the ticket.

---

### AC4 — No-victory-conditions guard

```python
class TestNoVictoryConditions:
    def test_no_conditions_stays_running(self):
        """Spec with victory_conditions=None never transitions via evaluator."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, ObjectiveEvaluator
        from unittest.mock import MagicMock
        state = MagicMock()
        state.tick = 9999
        result = ObjectiveEvaluator.evaluate(state, [])
        assert result == ScenarioObjectiveState.RUNNING

    def test_none_conditions_guard(self):
        """Passing None conditions (defensive) returns RUNNING."""
        from src.engine.scenario_runtime import ScenarioObjectiveState, ObjectiveEvaluator
        from unittest.mock import MagicMock
        state = MagicMock()
        result = ObjectiveEvaluator.evaluate(state, None)
        assert result == ScenarioObjectiveState.RUNNING
```

---

### AC5 — Terminal state guard on step()

```python
class TestTerminalStateGuards:
    def test_step_raises_after_objective_met(self):
        from src.engine.scenario_runtime import ScenarioObjectiveState
        svc = _make_service(victory_conditions=[{"kind": "tick_limit", "value": 1}])
        try:
            svc.start(tick_limit=10)
            assert svc.objective_state == ScenarioObjectiveState.OBJECTIVE_MET
            # step() on a non-RUNNING service should raise or be a no-op
            # Confirm it does not silently re-enter the tick loop
            import pytest
            with pytest.raises((RuntimeError, Exception)):
                svc.step()
        finally:
            svc.abort()
```

---

### ObjectiveEvaluator unit tests (can go in unit/ instead)

These are fast, no-kernel tests and could also live in
`tests/unit/engine/test_objective_evaluator.py`:

```python
class TestObjectiveEvaluatorUnit:
    def test_tick_limit_exact(self):
        ...  # state.tick == value → OBJECTIVE_MET
    def test_tick_limit_exceeded(self):
        ...  # state.tick > value → OBJECTIVE_MET
    def test_tick_limit_not_reached(self):
        ...  # state.tick < value → RUNNING (no early exit from this condition)
    def test_entity_count_correct_predicate(self):
        ...  # ensures e.combat.alive not e.is_alive
    def test_multiple_conditions_first_match_wins(self):
        ...  # tick_limit at 5, entity_count at 2; at tick=5 with 3 alive → OBJECTIVE_MET
    def test_unknown_condition_kind_skipped(self):
        ...  # unknown kind should not raise; just skip (or raise ValueError)
```

---

## Scoped Pytest Commands

Primary (per ticket AC):
```bash
pytest tests/integration/scenarios/test_scenario_runtime_service.py -x -v -m slow
```

Unit layer (fast, no real kernel):
```bash
pytest tests/unit/engine/test_scenario_runtime_service.py tests/unit/engine/test_objective_evaluator.py -x -v
```

Regression check (run before and after E31B):
```bash
pytest tests/unit/engine/test_scenario_runtime_service.py tests/integration/scenarios/test_scenario_catalog_matrix.py tests/integration/scenarios/test_scenario_setup_resolver.py -x -v
```

Full engine unit suite:
```bash
pytest tests/unit/engine/ -x -v
```

Do NOT run `pytest tests/` — the full suite includes slow integration scenarios and unrelated
subsystems.

---

## Anti-Drift Test Guards

1. **`test_stall_threshold_is_50`** — asserts `STALL_THRESHOLD == 50`. If someone changes the
   constant without updating tests/documentation, this fails explicitly.

2. **`test_entity_count_correct_predicate`** — exercises `e.combat.alive` specifically. If
   someone refactors to `len(state.entities)`, this test catches it via a scenario with a dead
   entity still in the dict.

3. **`test_step_also_triggers_objective_met`** — guards against objective evaluation being
   wired only to `_run_loop()` and not `step()`.

4. **`test_none_conditions_guard`** — guards against `NoneType` iteration crash when
   `victory_conditions` is `None`.

5. **Regression suite** — all 30 E31A unit tests must pass. The `__slots__` extension is the
   highest-risk structural change; `TestAbort::test_abort_calls_kernel_shutdown` and
   `TestPauseResume::test_resume_continues_from_pause_tick` are the most likely to surface
   regressions from `_run_loop()` edits.

6. **Parity ledger guard** — after implementation, update INFRA-214
   (`docs/parity_ledger/infrastructure.yaml`, line 2419) to reference `ObjectiveEvaluator`
   and the new integration test path. The parity ledger is not tested automatically but is
   reviewed at epic close.
