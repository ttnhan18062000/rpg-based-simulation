---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260420-CORE-MOVEMENT-SLICE
artifact_type: investigation
tags: [core, movement, slice]
---


# Investigation - TCK-20260420-CORE-MOVEMENT-SLICE

## Findings
- The original engine implements movement validation in `src/actions/move.py` and `src/core/logic/legality_service.py`.
- Key constraints are:
  - Actor must be alive.
  - Target must be walkable (not in static blocked tiles).
  - Target must not be occupied by another active entity.
  - Cardinal movement only (clamped to 1 step).
- In V2, the substrate uses a 6-phase loop. Movement resolution happens in Phase 4 (Resolution).
- Workers must be autonomous, so they need `blocked_tiles` and `neighbor_view` in their packet.

## References
- `src/core/logic/legality_service.py`
- `src/actions/move.py`
- `src/core/state.py`
- `src/engine/worker_logic.py`
