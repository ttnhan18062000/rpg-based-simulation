---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E31A-SCENARIO-SERVICE
phase: done
date: 2026-06-20
tags: [scenario-runtime, kernel-lifecycle, service-layer, phase-3]
---

# TCK-20260619-E31A-SCENARIO-SERVICE

## Title
Epic 3.1A · ScenarioRuntimeService + Kernel Lifecycle

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
No controllable scenario execution layer exists. This ticket creates `ScenarioRuntimeService` — a service that owns a running `Kernel`, exposes start/pause/resume/step/abort, and extends scenario YAML with `victory_conditions`.

**Blocks:** TCK-20260619-E31B-OBJECTIVE-FSM

## Scope

### 1. Extend scenario YAML schema with `victory_conditions`

Add to scenario spec (`data/content/simulation_scenarios/*.yaml`):
```yaml
victory_conditions:
  - kind: tick_limit    # run N ticks → OBJECTIVE_MET
    value: 500
  - kind: entity_count  # when alive_entities < N → OBJECTIVE_FAILED
    value: 1
```
Confirm schema location (`src/content/` or `src/worldbuilding/schema.py`) before modifying.

### 2. Implement `ScenarioRuntimeService` — new file `src/engine/scenario_runtime.py`

```python
class ScenarioRuntimeService:
    def __init__(self, spec: ScenarioSpec):
        self._kernel: Kernel | None = None
        self._spec = spec
        self._state: ScenarioObjectiveState = ScenarioObjectiveState.RUNNING
        self._tick: int = 0

    def start(self) -> None: ...   # build kernel, begin tick loop
    def pause(self) -> None: ...   # halt tick loop, preserve state
    def resume(self) -> None: ...  # restart tick loop from pause point
    def step(self) -> None: ...    # advance exactly one tick
    def abort(self) -> None: ...   # shutdown kernel, set ABORTED state

    @property
    def tick(self) -> int: ...
    @property
    def objective_state(self) -> ScenarioObjectiveState: ...
    @property
    def alive_entity_count(self) -> int: ...
```

### 3. Add `ScenarioObjectiveState` enum

```python
class ScenarioObjectiveState(str, Enum):
    RUNNING = "RUNNING"
    OBJECTIVE_MET = "OBJECTIVE_MET"
    OBJECTIVE_FAILED = "OBJECTIVE_FAILED"
    STALLED = "STALLED"
    ABORTED = "ABORTED"
```

Place in `src/engine/scenario_runtime.py` or `src/core/enums.py`.

## Out of Scope
- Objective condition evaluation logic (E31B)
- Checkpoint/restore (E31C)
- REST API (E31D)

## Acceptance Criteria
- `ScenarioRuntimeService(spec).start()` runs 100 ticks without error
- `.pause()` halts tick progression; `.resume()` continues from pause tick
- `.abort()` calls `kernel.shutdown()` to prevent thread leak
- `ScenarioObjectiveState` enum is importable
- All existing kernel tests pass (no regressions)

## Related Tickets
- TCK-20260619-E31-SCENARIO-RUNTIME (parent epic)
- TCK-20260619-E31B-OBJECTIVE-FSM (blocked on this)

## Related Code Areas
- `src/engine/scenario_runtime.py` (new)
- `src/engine/kernel.py:L34` (Kernel — read before wrapping)
- `src/domains/campaigns/runner.py` (CampaignRunner — reference pattern for kernel usage)
- Scenario YAML schema files

## Assumptions / Open Questions
- Does `Kernel` support pause/resume natively, or does the service need to manage the tick loop itself? Read `src/engine/kernel.py` before implementing.
- Is `ScenarioSpec` already a typed model? Check `src/domains/campaigns/spec.py` or `src/content/` for where scenario specs are loaded.

## Implementation Notes

Implemented in three steps:

1. **`src/scenarios/schema.py`**: Added `VictoryCondition` Pydantic model (frozen, `extra="forbid"`, allowed kinds: `tick_limit` | `entity_count`) and optional `victory_conditions: Optional[List[VictoryCondition]] = None` field to `SimulationScenarioDefinition`. Existing YAML files without the field continue to parse.

2. **`src/engine/scenario_runtime.py`** (new): Added `ScenarioObjectiveState(str, Enum)` with 5 values (RUNNING, OBJECTIVE_MET, OBJECTIVE_FAILED, STALLED, ABORTED) and `ScenarioRuntimeService` class. The service owns a `Kernel` built in `_build_kernel()` using the same minimal-profile pattern as `CampaignRunner`. Tick loop is synchronous; `pause()`/`resume()` are cooperative flag operations. `abort()` calls `kernel.shutdown()`. `step()` advances exactly one tick. Victory condition *evaluation* is deferred to E31B.

3. **`tests/unit/engine/test_scenario_runtime_service.py`** (new): Unit tests covering all 5 ACs across 7 test classes.

Clarification resolved: `ScenarioSpec` in ticket pseudocode → actual type is `SimulationScenarioDefinition`. `ScenarioObjectiveState` placed in `src/engine/scenario_runtime.py` to keep engine-layer concerns co-located.

## Test Summary
```bash
pytest tests/unit/engine/ -x -v
```

## Files Changed
- `src/scenarios/schema.py` — Added `VictoryCondition` model and `victory_conditions` field
- `src/engine/scenario_runtime.py` — New file: `ScenarioObjectiveState` enum + `ScenarioRuntimeService`
- `tests/unit/engine/test_scenario_runtime_service.py` — New file: unit tests

## Completion Summary
Implemented `ScenarioRuntimeService` + `ScenarioObjectiveState` in `src/engine/scenario_runtime.py`. Extended `SimulationScenarioDefinition` with optional `victory_conditions: List[VictoryCondition]` (kinds: `tick_limit`, `entity_count`). Service wraps `Kernel` with a synchronous tick loop; `pause()`/`resume()` are cooperative flag operations; `abort()` calls `kernel.shutdown()`. 30 new unit tests across 7 test classes; all 162 existing engine unit tests that were previously passing continue to pass. Parity entry INFRA-214 added to `docs/parity_ledger/infrastructure.yaml`. Unblocks TCK-20260619-E31B-OBJECTIVE-FSM.
