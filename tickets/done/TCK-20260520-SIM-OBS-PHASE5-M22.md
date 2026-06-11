---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE5-M22
phase: done
date: 2026-05-20
tags: [sim, obs, phase5, m22]
---

# TCK-20260520-SIM-OBS-PHASE5-M22

## Title
Entity Inspector V1

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement safe, real-time read-only inspection of individual simulation entities. Developers should be able to query the exact state and timeline of a single entity during live simulation execution without causing any locks or full-world scans.

## Scope
- Expose `entity_timeline_store` property on Kernel class.
- Create `EntityInspectionSnapshot` Pydantic model for compact, JSON-safe entity serialization.
- Implement `EntityInspector` to resolve entity details (existence, alive status, position, components, combat summary, inventory summary, quest summary, strategic summary, recent timeline events, latest rejections/anomalies) cleanly.
- Create read-only API endpoint:
  - `GET /api/v1/observability/live/entities/{entity_id}` with support for a `timeline_limit` query parameter.
- Return appropriate fallback states (exists = False, 404 response) for missing/dead/deleted entities.
- Write robust unit tests and API integration tests.

## Out of Scope
- Full-world map/graph rendering (Phase 6).
- Entity timeline event broadcasting/streaming via WebSockets (reserved for Milestone 23/24).
- Modifying entity state directly from the inspector (inspector is strictly read-only).

## Acceptance Criteria
- `/api/v1/observability/live/entities/{entity_id}` returns a compact, JSON-safe entity summary.
- The returned payload does not expose huge raw object graphs or circular nested references.
- Timeline limits can be dynamically queried via `timeline_limit`.
- Appropriate exists=False or HTTP 404 responses are returned for invalid/missing entity IDs.
- Zero locks or blockages on the simulation tick loop thread.
- 100% automated test coverage.

## Related Tickets
- `TCK-20260520-SIM-OBS-PHASE5-M21`

## Related Docs
- `obs_sim_phase5.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/engine/kernel.py`
- `src/api/server.py`
- `src/observability/live/entity_inspector.py`

## Assumptions / Open Questions
- We assume that `entity_id` is an integer.
- Timeline events can be resolved safely from either the entity's active timeline deque or the kernel's `EntityTimelineStore`.

## Implementation Notes
- Exposed `entity_timeline_store` property on `Kernel`.
- Exposed `latest_state` property thread-safely on `V2EngineManager` via locks.
- Created lightweight `EntityInspectionSnapshot` Pydantic model.
- Created `EntityInspector.inspect_entity` resolving compact details thread-safely.
- Registered `/api/v1/observability/live/entities/{entity_id}` endpoint.
- Correctly parsed `timeline_limit` and handled missing entity/idle states with FastAPI `HTTPException(404)`.

## Test Summary
- Unit Tests: `tests/unit/observability/test_entity_inspector.py` (4 passed)
- Integration Tests: `tests/api/test_live_entity_inspection.py` (1 passed)
- Regression Checks: Checked with all live snapshot/API tests, all 9 passed in 8.55s.

## Files Changed
- [kernel.py](file:///home/vboxuser/Work/rpg-based-simulation/src/engine/kernel.py)
- [engine_manager.py](file:///home/vboxuser/Work/rpg-based-simulation/src/api/engine_manager.py)
- [entity_inspector.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/live/entity_inspector.py)
- [server.py](file:///home/vboxuser/Work/rpg-based-simulation/src/api/server.py)
- [test_entity_inspector.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/observability/test_entity_inspector.py)
- [test_live_entity_inspection.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/api/test_live_entity_inspection.py)

## Completion Summary
- Successfully implemented Entity Inspector V1. The API resolves compact, curated single-entity statuses without introducing performance locks or complex database queries. Fully tested, robust, and compliant.
