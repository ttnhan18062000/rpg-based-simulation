# Implementation Plan - Entity Inspector V1 (Milestone 22)

Expose single-entity inspection capabilities for active or dead simulation entities in real-time, non-blocking, and thread-safe manner.

## User Review Required
> [!IMPORTANT]
> The inspection payload returns a compact, curated summary of the entity rather than full raw nested state objects. This prevents infinite JSON circular references and minimizes memory footprint.

## Proposed Changes

### Core Engine and Observability
---
#### [MODIFY] [kernel.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py)
Expose the kernel's `EntityTimelineStore` property so that external providers/inspectors can query live events of a given entity ID.

```python
    @property
    def entity_timeline_store(self) -> EntityTimelineStore:
        return self._entity_timeline_store
```

#### [MODIFY] [engine_manager.py](file:///home/vboxuser/Work/rpg-based-simulation/src/api/engine_manager.py)
Expose the `latest_state` property thread-safely:
```python
    @property
    def latest_state(self) -> Optional[AuthoritativeState]:
        with self._state_lock:
            return self._latest_state
```

#### [NEW] [entity_inspector.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/live/entity_inspector.py)
Implement:
- `EntityInspectionSnapshot` (Pydantic model) containing all necessary fields.
- `EntityInspector` resolving the snapshot safely, reading from `V2EngineManager.latest_state` and `kernel.entity_timeline_store`.
- Uninitialized/missing entities return `exists = False`.

### API Exposure
---
#### [MODIFY] [server.py](file:///home/vboxuser/Work/rpg-based-simulation/src/api/server.py)
Register API endpoint:
- `GET /api/v1/observability/live/entities/{entity_id}`
Returns the `EntityInspectionSnapshot` or raising a `404` or returning a safe `exists=False` default when uninitialized.

## Verification Plan

### Automated Tests
- Unit Tests: `tests/unit/observability/test_entity_inspector.py`
  - Test inspecting active entities.
  - Test inspecting dead/deleted/missing entities.
  - Test timeline event boundaries and pagination/limiting.
- Integration API Tests: `tests/api/test_live_entity_inspection.py`
  - Launch active background simulation.
  - Query `/api/v1/observability/live/entities/{entity_id}`.
  - Confirm properties match schemas and limits are respected.
