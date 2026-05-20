# Implementation Plan - Live Run Status and Snapshot Provider

## Goal
Establish a safe, performant, in-process "Live Observatory" status and snapshot architecture that exposes the current simulation's execution state, health, errors, and aggregated event counts via read-only REST endpoints.

## Proposed Changes

### `src/engine/kernel.py` [MODIFY]
- Add properties `event_recorder` and `run_id` to `Kernel` class to allow access to the running simulation's active recorders and run identifier.

### `src/api/engine_manager.py` [MODIFY]
- Track `_started_at` timestamp inside `V2EngineManager.start()`.
- Add public getters for checking running/paused/stopped/starting states to determine live run status.

### `src/observability/live/snapshot_provider.py` [NEW]
- Define `LiveRunStatus` and `LiveRunSnapshot` data schemas using Pydantic.
- Implement `LiveSnapshotProvider` retrieving in-memory stats, including tick count, health status, error counters, cumulative violations, and event type distributions.
- Support safe default/inactive schemas when the manager is uninitialized or not running.

### `src/api/server.py` [MODIFY]
- Register two new read-only API endpoints:
  - `GET /api/v1/observability/live/status`
  - `GET /api/v1/observability/live/snapshot`
- Inject the snapshot provider and resolve status properties in a thread-safe and non-blocking manner.

## Verification Plan

### Automated Tests
- Unit tests in `tests/unit/observability/test_live_snapshot_provider.py` verifying status model fields, fallback/idle responses, and snapshot metric resolution.
- API tests in `tests/api/test_live_observability_status.py` verifying integration with FastAPI, correct JSON rendering under both idle and running states, and performance constraints (non-blocking).
