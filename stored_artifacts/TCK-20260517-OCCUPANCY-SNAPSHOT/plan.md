---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260517-OCCUPANCY-SNAPSHOT
artifact_type: plan
tags: [occupancy, snapshot]
---

# Implementation Plan: OccupancySnapshot

## Goal

Implement `OccupancySnapshot` to provide a frozen, per-tick spatial read model for entity tile occupancy and tie-breaking priority.

## Proposed Changes

### 1. `src/engine/occupancy_snapshot.py` [NEW]
Implement `OccupancySnapshot` dataclass:
```python
@dataclass(frozen=True)
class OccupancySnapshot:
    tick: int
    occupancy_by_tile: dict[tuple[int, int], int]
    priority_by_entity: dict[int, int]

    @classmethod
    def from_state(cls, state: AuthoritativeState) -> OccupancySnapshot: ...

    def occupant_at(self, tile: tuple[int, int]) -> int | None: ...
    def is_occupied(self, tile: tuple[int, int]) -> bool: ...
    def get_priority(self, entity_id: int) -> int: ...
```

### 2. `src/engine/legality.py` [MODIFY]
Provide an optional `snapshot: OccupancySnapshot | None` argument or helper in `LegalityServiceV2` to utilize the snapshot during movement legality checks.

## Verification

- Unit tests in `tests/unit/optimization/test_occupancy_snapshot.py`.
- Verify full test suite compliance with `pytest tests/unit/ -m "not slow"`.
