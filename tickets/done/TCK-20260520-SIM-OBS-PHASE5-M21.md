# TCK-20260520-SIM-OBS-PHASE5-M21

## Title
Live Run Status and Snapshot Provider

## Status
DONE

## Request Summary
Expose the current simulation run status safely via new read-only API endpoints to allow developers to query running simulations (current tick, health state, metrics, errors) without blocking the engine's tick loop or scanning all entities.

## Scope
- Define `LiveRunStatus` and `LiveRunSnapshot` data schemas.
- Expose properties on Kernel to safely access run metadata (e.g. `run_id`, `event_recorder`).
- Implement `LiveSnapshotProvider` under `src/observability/live/snapshot_provider.py` which retrieves cached metrics, recent event counts, hard law violations, and runtime status from the engine manager and kernel.
- Create new read-only API endpoints:
  - `GET /api/v1/observability/live/status`
  - `GET /api/v1/observability/live/snapshot`
- Handlers must return safe IDLE responses or appropriate fallback states when no run/engine manager is initialized.
- Comprehensive unit and API tests verifying correctness under both active and idle run states.

## Out of Scope
- Out-of-process process/event streaming via Redis/Kafka (reserved for Phase 6).
- Entity timeline details or entity inspection details (reserved for Milestone 22).
- Live anomaly counting logic (reserved for Milestone 25).
- Frontend visual dashboard (reserved for Milestone 26).

## Acceptance Criteria
- `/api/v1/observability/live/status` returns the correct live run status fields.
- `/api/v1/observability/live/snapshot` returns the current live snapshot, including recent event counts and metric snapshots.
- Both endpoints are completely read-only, non-blocking to the tick loop, and perform no full-world or entity scans.
- Safe, standard IDLE/inactive response format is returned if `V2EngineManager` is not running.
- 100% test coverage for the provider and the FastAPI endpoints.

## Related Tickets
- None

## Related Docs
- `obs_sim_phase5.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/engine/kernel.py`
- `src/api/server.py`
- `src/api/engine_manager.py`
- `src/observability/live/snapshot_provider.py`

## Assumptions / Open Questions
- We assume that `V2EngineManager` is the global single-process manager for the simulation lifespan when serving API requests.
- The `LiveRunStatus` elapsed time will be tracked since the engine manager's loop execution start time.

## Implementation Notes
- Exposed properties on Kernel to let LiveSnapshotProvider query the event recorder and run ID safely.
- Added start timestamp and execution state helper properties on V2EngineManager.
- Implemented LiveSnapshotProvider containing clean schemas and thread-safe snapshot resolvers with idle fallback states.
- Registered `/api/v1/observability/live/status` and `/api/v1/observability/live/snapshot` read-only API endpoints in FastAPI server.

## Test Summary
- Unit tests (`tests/unit/observability/test_live_snapshot_provider.py`) verify idle provider state defaults, status mapping transitions, and complete metrics/event count parsing.
- API integration tests (`tests/api/test_live_observability_status.py`) boot the FastAPI server in a background thread and verify status, snapshot, and pause/resume transitions.
- All 4 tests successfully verified and passed.

## Files Changed
- `src/engine/kernel.py`
- `src/api/engine_manager.py`
- `src/api/server.py`
- `src/observability/live/snapshot_provider.py`
- `tests/unit/observability/test_live_snapshot_provider.py`
- `tests/api/test_live_observability_status.py`

## Completion Summary
- Successfully completed Milestone 21 of Phase 5. Telemetry endpoints are fully operational, thread-safe, read-only, and non-blocking.
