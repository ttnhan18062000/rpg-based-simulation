---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE5-M21
artifact_type: investigation
tags: [sim, obs, phase5, m21]
---

# Investigation - Live Run Status and Snapshot Provider

## Thread Safety and Performance Guards
- The FastAPI server runs on an event loop while `V2EngineManager` ticks the engine on a dedicated background thread (`v2-engine-loop`).
- To avoid any performance impact or blocking behavior on the ticking thread, we must not lock the state lock for long periods or perform any heavy computations inside the HTTP requests.
- `V2EngineManager` already keeps a cached copy of the minimal summary (`self._latest_snapshot`), metrics snapshot (`self._latest_metrics_snapshot`), and state (`self._latest_state`).
- Our `LiveSnapshotProvider` will query these cached properties and the thread-safe deque of `RuntimeStatus.signal_history` without scanning the simulation state.
- Reading events will query the `EventRecorder.events` list. To be safe, we will construct simple counts and status summaries without holding locks or executing long iterations.

## Live Status Mapping
The engine states can be mapped directly based on manager properties:
- `IDLE`: `V2EngineManager` is not running and thread is not alive.
- `RUNNING`: `V2EngineManager` is active and not paused.
- `PAUSED`: `V2EngineManager` is active and paused.
- `STOPPING`: `V2EngineManager` is in the process of shutting down.

## Data Schemas Design
1. **LiveRunStatus**:
   - `run_id`: `str` or `None`
   - `scenario_name`: `str` (or `"default"`)
   - `scenario_type`: `str` (or `"default"`)
   - `status`: `str` (`"IDLE"`, `"RUNNING"`, `"PAUSED"`, `"STOPPING"`, `"FAILED"`, `"COMPLETED"`)
   - `current_tick`: `int`
   - `ticks_requested`: `int` or `None` (representing infinite/continuous)
   - `started_at`: `str` (ISO format or `None`)
   - `elapsed_seconds`: `float`
   - `observability_mode`: `str` (from `ObservabilityConfig.get_mode().name` or standard setting)
   - `governor_mode`: `str` (RuntimeMode mapping: `"NORMAL"`, `"DEGRADED"`, `"CRITICAL"`, etc.)
   - `health_state`: `str` (Calculated based on error presence or violations)
   - `last_error`: `str` or `None`
   - `last_hard_law_violation_tick`: `int`

2. **LiveRunSnapshot**:
   - `run_status`: `LiveRunStatus`
   - `latest_world_metrics`: `Dict[str, Any]` (from the engine manager's metrics snapshot)
   - `latest_runtime_status`: `Dict[str, Any]` (current metrics and phase costs)
   - `recent_event_counts`: `Dict[str, int]` (event type distribution from EventRecorder)
   - `hard_law_violation_count`: `int`
