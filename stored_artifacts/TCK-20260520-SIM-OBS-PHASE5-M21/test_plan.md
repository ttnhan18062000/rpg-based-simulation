# Test Plan - Live Run Status and Snapshot Provider

## Scope of Testing

### 1. Unit Testing (`tests/unit/observability/test_live_snapshot_provider.py`)
- **Idle Provider State**: Verify that when `V2EngineManager` is not initialized or not running, the provider returns clean defaults with status `IDLE` (no exceptions thrown).
- **Active Provider State**: Verify that when `V2EngineManager` is running, status correctly maps to `RUNNING` or `PAUSED`, tick count matches, and metrics snapshots match what's cached in the manager.
- **Data Parity**: Verify that `LiveRunStatus` and `LiveRunSnapshot` deserialize and serialize cleanly, matching the API specs exactly.
- **Event Counts Retrieval**: Verify that event counts by type are accurately extracted from the kernel's `EventRecorder` and mapped inside the snapshot.

### 2. API Integration Testing (`tests/api/test_live_observability_status.py`)
- **FastAPI Endpoints Resolution**: Verify `/api/v1/observability/live/status` and `/api/v1/observability/live/snapshot` endpoints load and return JSON content.
- **Running States Handling**: Query the endpoints under active simulation running state (started via fastapi lifecycle), and verify that tick increment updates the returned JSON tick correctly.
- **Paused States Handling**: Pause the simulation via the standard `/api/v1/control/pause` control endpoint, query `/api/v1/observability/live/status`, and verify the status reports `"PAUSED"`.
- **Under Load Performance**: Ensure querying endpoints doesn't introduce tick loop overhead or contention.
