---
status: active
artifact_type: plan
ticket_id: TCK-20260619-E31A-SCENARIO-SERVICE
date: 2026-06-20
---

# Plan: TCK-20260619-E31A-SCENARIO-SERVICE

## Ordered Steps

### Step 1 — Add `VictoryCondition` + `victory_conditions` to `SimulationScenarioDefinition`
**File:** `src/scenarios/schema.py`

- Add `VictoryCondition` Pydantic model with fields: `kind: str` (literal: `"tick_limit"` | `"entity_count"`) and `value: int`.
- Add model validator on `VictoryCondition` that rejects unknown `kind` values.
- Add `victory_conditions: Optional[List[VictoryCondition]] = None` to `SimulationScenarioDefinition`.
- `extra="forbid"` already on `SimulationScenarioDefinition` — no change needed.
- Existing YAML files without `victory_conditions` continue to parse (field is Optional).

**Scope guard:** Do NOT touch `ALLOWED_INITIAL_CONDITION_CATEGORIES`. Do NOT change `initial_conditions` validator.

**AC mapped:** AC1 (spec parsing), victory_conditions round-trip test.

---

### Step 2 — Add `ScenarioObjectiveState` enum and `ScenarioRuntimeService` class
**File:** `src/engine/scenario_runtime.py` (new file)

#### 2a. `ScenarioObjectiveState(str, Enum)`
```
RUNNING, OBJECTIVE_MET, OBJECTIVE_FAILED, STALLED, ABORTED
```

#### 2b. `ScenarioRuntimeService`
Fields:
- `_spec: SimulationScenarioDefinition`
- `_kernel: Kernel | None`
- `_state: ScenarioObjectiveState` (init: RUNNING)
- `_tick: int` (init: 0)
- `_paused: bool` (init: False)

Methods:
- `start(tick_limit: int = 500) -> None`: Build `RuntimeProfile`, `AuthoritativeState(tick=0, seed=0)`, `DeterministicRNG(seed=0)`. Construct `Kernel(profile, state, rng, flags={"no_replay": True})`. Run tick loop: `while self._tick < tick_limit and not self._paused and self._state == RUNNING: kernel.tick_once(); self._tick += 1`.
- `pause() -> None`: Set `_paused = True`.
- `resume(tick_limit: int = 500) -> None`: Clear `_paused`; continue tick loop from current `_tick`.
- `step() -> None`: Advance exactly one tick (calls `tick_once()` once, increments `_tick`). Raises if kernel not started or aborted.
- `abort() -> None`: Set `_state = ABORTED`. Call `self._kernel.shutdown()` if kernel exists.
- Properties: `tick`, `objective_state`, `alive_entity_count` (returns `len(self._kernel.state.entities)` or 0).

**Scope guard:** Do NOT implement victory condition evaluation (E31B). `objective_state` always returns `_state` as-is — evaluation hook is left for E31B.

**AC mapped:** AC1, AC2, AC3, AC4.

---

### Step 3 — Write tests
**File:** `tests/unit/engine/test_scenario_runtime_service.py` (new file)

Tests per test_plan.md:
1. `test_scenario_objective_state_importable`
2. `test_start_runs_n_ticks_without_error` — minimal spec, `start(tick_limit=100)`, assert `service.tick == 100`
3. `test_pause_halts_progression` — step 5 ticks, pause, assert tick==5, step while paused is no-op
4. `test_resume_continues_from_pause_tick` — pause at 5, resume to 10, assert tick==10
5. `test_abort_calls_kernel_shutdown` — mock kernel, assert shutdown called, state==ABORTED
6. `test_step_advances_exactly_one_tick`
7. `test_alive_entity_count`
8. `test_victory_conditions_schema_round_trip` — parse spec with `victory_conditions`, assert `VictoryCondition` typed correctly
9. `test_victory_conditions_unknown_kind_raises` — unknown kind raises ValueError
10. `test_spec_without_victory_conditions_parses` — backward compat

**Scope guard:** Do NOT import or test E31B objective evaluation. Use `flags={"no_replay": True}` to avoid file I/O in tests.

---

### Step 4 — Update ticket Implementation Notes

**File:** `tickets/inprogress/TCK-20260619-E31A-SCENARIO-SERVICE.md`

## Dependency Map

- Step 1 has no dependencies.
- Step 2 depends on Step 1 (`SimulationScenarioDefinition` is the `spec` type).
- Step 3 depends on Steps 1 and 2.
- Step 4 depends on Steps 1–3.

## Acceptance Criteria → Steps

| AC | Step |
|---|---|
| `start()` runs 100 ticks without error | Step 2 + Step 3 test 2 |
| `pause()` halts tick; `resume()` continues | Step 2 + Step 3 tests 3–4 |
| `abort()` calls `kernel.shutdown()` | Step 2 + Step 3 test 5 |
| `ScenarioObjectiveState` enum importable | Step 2 + Step 3 test 1 |
| All existing kernel tests pass | Step 2 (no Kernel code changes) |

## Scope Guards (summary)

- Do NOT touch `ALLOWED_INITIAL_CONDITION_CATEGORIES`.
- Do NOT implement objective condition evaluation (E31B).
- Do NOT add checkpoint/restore (E31C).
- Do NOT add REST API (E31D).
- Do NOT add threading to the service (tick loop is synchronous).
- Do NOT modify any existing Kernel code.

## Deviations

_(none yet — filled during implementation if needed)_
