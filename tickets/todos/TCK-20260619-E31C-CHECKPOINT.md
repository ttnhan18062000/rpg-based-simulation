---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E31C-CHECKPOINT
phase: open
date: 2026-06-20
tags: [scenario-runtime, checkpoint, determinism, phase-3]
---

# TCK-20260619-E31C-CHECKPOINT

## Title
Epic 3.1C · Scenario Checkpoint / Restore

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Pause/resume preserves in-memory state. Checkpoint/restore must survive process restarts: serialize full `AuthoritativeState` + RNG state to a named checkpoint file; restore to a fresh `ScenarioRuntimeService` with identical subsequent outcomes (determinism preserved).

**Requires:** TCK-20260619-E31B-OBJECTIVE-FSM

## Scope

### 1. `ScenarioCheckpointer` — new file `src/engine/scenario_checkpoint.py`

```python
class ScenarioCheckpointer:
    @staticmethod
    def save(state: AuthoritativeState, path: str) -> None:
        """Serialize AuthoritativeState + RNG checkpoint to JSON file."""
        data = {
            "tick": state.tick,
            "rng_checkpoint": state.rng_checkpoint,
            "state": state.to_canonical_dict(),  # deep serialization
        }
        with open(path, "w") as f:
            json.dump(data, f)

    @staticmethod
    def load(path: str) -> tuple[AuthoritativeState, int]:
        """Restore AuthoritativeState from checkpoint. Returns (state, tick)."""
        ...
```

**First step:** Verify `AuthoritativeState.to_canonical_dict()` produces a complete, restorable snapshot (including all entity states, nodes, regions, quest_registry, etc.). If not, identify missing fields before implementing restore path.

### 2. Wire into `ScenarioRuntimeService`

```python
def checkpoint(self, name: str) -> str:
    """Write checkpoint to named file, return path."""
    path = f"checkpoints/{self._spec.id}_{name}.json"
    ScenarioCheckpointer.save(self._kernel.state, path)
    return path

def restore(self, path: str) -> None:
    """Restore from checkpoint. Replaces current kernel state."""
    state, tick = ScenarioCheckpointer.load(path)
    # Rebuild kernel from restored state
    ...
```

## Out of Scope
- Incremental checkpoints (just full-state snapshots)
- Checkpoint rotation/cleanup

## Acceptance Criteria
- Checkpoint at tick 25, restore to fresh service, run to tick 50 → identical events to non-checkpoint run
- `test_checkpoint_restore_determinism` passes
- `state.rng_checkpoint` is included in checkpoint file

## Related Tickets
- TCK-20260619-E31-SCENARIO-RUNTIME (parent epic)
- TCK-20260619-E31B-OBJECTIVE-FSM (required)
- TCK-20260619-E31D-REST-API (blocked on this)

## Related Docs
- `docs/core/state.md` (immutability law — serialize/restore must preserve it)
- `docs/parity_ledger/infrastructure.yaml` (checkpoint/replay entries — update to `verified` on completion)

## Related Code Areas
- `src/engine/checkpoint.py` (CanonicalHashScheduler — reference for RNG checkpoint field)
- `src/engine/scenario_checkpoint.py` (new)
- `src/core/state.py` (AuthoritativeState.to_canonical_dict())

## Test Summary
```bash
pytest tests/integration/scenarios/test_scenario_runtime_service.py::test_checkpoint_restore_determinism -x -v -m slow
```
## Files Changed
_To be filled on completion._
## Completion Summary
_To be filled on completion._
