---
status: active
artifact_type: test_plan
ticket_id: TCK-20260619-E31A-SCENARIO-SERVICE
date: 2026-06-20
---

# Test Plan: TCK-20260619-E31A-SCENARIO-SERVICE

## Regression Surface (existing tests that must pass)

```bash
pytest tests/unit/engine/ -x -v
```

Key tests that must not regress:
- `tests/unit/engine/test_lifecycle_supervisor.py` — Kernel shutdown/ShutdownReport
- `tests/unit/engine/test_sort_tiebreaker.py` — Kernel phase resolution ordering
- `tests/unit/engine/test_content_hotpath_guard.py` — ContentWarmupService / tick guard
- `tests/unit/engine/test_capability_registry.py` — engine capability registry

## New Tests Required (per AC)

File: `tests/unit/engine/test_scenario_runtime_service.py`

### AC1: `ScenarioRuntimeService(spec).start()` runs 100 ticks without error
```python
def test_start_runs_100_ticks_without_error():
    # Build a minimal SimulationScenarioDefinition
    # Call service.start() with tick_limit=100
    # Assert no exception raised, service.tick == 100
```

### AC2: `.pause()` halts tick progression; `.resume()` continues from pause tick
```python
def test_pause_halts_tick_progression():
    # Run 10 ticks, pause, assert tick==10
    # Attempt step while paused → no-op or raises
    # resume(), run 10 more ticks → tick==20

def test_resume_continues_from_pause_tick():
    # start → step to tick 5 → pause → resume → step to tick 10
    # Assert tick count is continuous, no tick skipped
```

### AC3: `.abort()` calls `kernel.shutdown()` to prevent thread leak
```python
def test_abort_calls_kernel_shutdown():
    # Mock kernel.shutdown
    # start() then abort()
    # Assert kernel.shutdown() was called exactly once
    # Assert service.objective_state == ScenarioObjectiveState.ABORTED
```

### AC4: `ScenarioObjectiveState` enum is importable
```python
def test_scenario_objective_state_enum_importable():
    from src.engine.scenario_runtime import ScenarioObjectiveState
    assert ScenarioObjectiveState.RUNNING == "RUNNING"
    assert ScenarioObjectiveState.OBJECTIVE_MET == "OBJECTIVE_MET"
    assert ScenarioObjectiveState.OBJECTIVE_FAILED == "OBJECTIVE_FAILED"
    assert ScenarioObjectiveState.STALLED == "STALLED"
    assert ScenarioObjectiveState.ABORTED == "ABORTED"
```

### AC5: All existing kernel tests pass (no regressions)
Covered by the regression surface block above.

### Additional: victory_conditions schema round-trip
```python
def test_victory_conditions_round_trip():
    # Parse a SimulationScenarioDefinition YAML that includes victory_conditions
    # Assert VictoryCondition objects are correctly typed
    # Assert tick_limit and entity_count kinds are accepted
    # Assert unknown kind raises validation error
```

### Additional: step() advances exactly one tick
```python
def test_step_advances_exactly_one_tick():
    # start service, step once → tick==1, step again → tick==2
```

### Additional: alive_entity_count property
```python
def test_alive_entity_count_returns_entity_count():
    # after start, alive_entity_count reflects kernel.state.entities length
```

## Scoped Pytest Commands

```bash
# New tests only
pytest tests/unit/engine/test_scenario_runtime_service.py -x -v

# Regression: full engine unit suite
pytest tests/unit/engine/ -x -v

# Combined
pytest tests/unit/engine/ -x -v
```

## Anti-Drift Test Guards

- Test that `SimulationScenarioDefinition` with `victory_conditions` containing an unknown `kind` raises `ValueError`.
- Test that `SimulationScenarioDefinition` without `victory_conditions` still parses (backward compat).
- Test that `_paused` flag on service does not affect `kernel._stopped` — they are orthogonal.
