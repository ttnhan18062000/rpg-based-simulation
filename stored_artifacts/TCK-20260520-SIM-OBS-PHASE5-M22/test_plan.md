---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE5-M22
artifact_type: test_plan
tags: [sim, obs, phase5, m22]
---

# Test Plan - Entity Inspector V1 (Milestone 22)

## 1. Unit Tests (`tests/unit/observability/test_entity_inspector.py`)
- **Active Entity Inspection**:
  - Mock/initialize a mock `V2EngineManager` with an active `AuthoritativeState` containing a fully populated `EntityState`.
  - Populate some simulation events in the `EntityTimelineStore`.
  - Instantiate `EntityInspector` and request the active entity.
  - Assert that all compact summary fields (`combat_summary`, `inventory_summary`, `quest_summary`, `strategic_summary`, `recent_timeline_events`) are perfectly populated and correct.
  - Assert that `exists` is `True` and `alive` is `True`.
- **Missing Entity Handling**:
  - Request an entity ID that is not present in the state.
  - Assert that the returned `EntityInspectionSnapshot` has `exists=False`, with safe fallback values for all other fields.
- **Dead Entity Inspection**:
  - Mock an `EntityState` with `combat.alive = False` and `combat.hp = 0`.
  - Assert that the returned `EntityInspectionSnapshot` has `exists=True`, but `alive=False`.
- **Timeline Limits**:
  - Populate a large timeline (e.g. 50 events) in `EntityTimelineStore` for an entity.
  - Query with `timeline_limit = 5`.
  - Assert that exactly 5 events are returned, properly formatted.

## 2. API Integration Tests (`tests/api/test_live_entity_inspection.py`)
- **Server Spinup**:
  - Use `subprocess.Popen` to launch the API server locally on a random port.
- **Query Idle State**:
  - Query `/api/v1/observability/live/entities/42` when the simulation is idle/uninitialized.
  - Assert that it returns a clear 404 or `exists=False` default state gracefully.
- **Simulation Active Inspection**:
  - Post command to start a live simulation run.
  - Wait for tick > 1.
  - Fetch list of active entities.
  - Pick a valid entity ID and query `/api/v1/observability/live/entities/{entity_id}`.
  - Assert HTTP 200 OK and validate JSON schema correctness.
  - Query with `?timeline_limit=3` and assert it successfully limits the event count returned.
- **Graceful Shutdown**:
  - Shutdown the server subprocess properly.
