# Plan: Observability Event Streaming, standalone anomaly workers, historical API, and retention policies

This plan outlines the architecture, code locations, and testing paths for the remaining Milestones of the RPG Simulation Live Observatory Phase 6.

## 1. Milestone 29: Event Stream Adapter Interface
We will introduce an adapter layer in `src/observability/stream/` to decouple the engine and `EventRecorder` from dynamic transport mechanisms.
- **Interfaces**:
  - `EventStreamAdapter`: Abstract base class with async/sync methods: `publish(event: SimulationEvent) -> None`, `publish_batch(events: List[SimulationEvent]) -> None`, `health() -> Dict[str, Any]`, `flush() -> None`, `close() -> None`.
- **Implementations**:
  - `NullEventStreamAdapter`: Performs no-ops (safe drop policy).
  - `InProcessEventStreamAdapter`: Routes events directly to the thread-safe `LiveEventPublisher`.
  - `RedisStreamAdapter`: Skeleton publishing JSON events to Redis Streams. Will wrap connections safely with try/except so that if `redis` library is missing or offline, the engine does not fail.
- **Config & Registry**:
  - Update `src/observability/config.py` with configurations for `stream_backend` (env `SIM_STREAM_BACKEND`), `redis_url` (`SIM_REDIS_URL`), `stream_name` (`SIM_STREAM_NAME`), `max_queue_size`, etc.
  - Create a factory `get_event_stream_adapter(config: ObservabilityConfig) -> EventStreamAdapter`.

## 2. Milestone 30: External Anomaly Worker V1
We will build a standalone worker process capable of analyzing raw simulation run artifacts completely out-of-process.
- **Worker Class**:
  - `ExternalAnomalyWorker` loading historical `.jsonl` files (simulation events, metric windows) for a specific `run_id`, executing the standard `RuleEngine` rule list, and serializing `anomalies.json` into the run directory.
  - Writes a `worker_status.json` tracking processed records, counts, status, and processing timestamp.
- **CLI Command**:
  - `rpg-observe worker analyze-run <run_id>`

## 3. Milestone 31: Historical Query API
We will expose past simulation runs, sweeps, and analytical datasets via read-only REST API endpoints.
- **Routes**:
  - `GET /api/v1/observability/history/runs`: Lists completed runs.
  - `GET /api/v1/observability/history/runs/{run_id}`: Returns run metadata and health stats.
  - `GET /api/v1/observability/history/runs/{run_id}/anomalies`: Returns run anomalies list.
  - `GET /api/v1/observability/history/runs/{run_id}/report`: Returns the markdown or JSON executive report.
  - `GET /api/v1/observability/history/sweeps`: Lists completed sweeps.
  - `GET /api/v1/observability/history/sweeps/{sweep_id}`: Returns sweep details.
- **Integrations**:
  - Interacts directly with `RunArtifactRepository` and `RunSetArtifactRepository`.
  - Features path traversal validation checking that `run_id`/`sweep_id` are safe alphanumeric strings.
  - Pagination limit defaulted to 50 runs maximum.

## 4. Milestone 32: Retention and Data Lifecycle Policy
We will implement data retention rules to prevent unbounded local file growth.
- **Classifiers**:
  - Expired Runs: Runs exceeding recent retention threshold (7 days by default).
  - Protected Runs: Runs that are failed, critical, or sources for baseline envelopes are classified as protected and kept for 30 days.
- **Cleanup Levels**:
  - Dry Run: Shows plan of what files would be deleted.
  - Deletion: Performs actual cleaning of raw events, metrics, and raw logs, preserving high-level summary manifests where configured.
- **CLI Commands**:
  - `rpg-observe retention plan`
  - `rpg-observe retention clean --confirm`

## 5. Milestone 33: Deployment Profiles and Scale Validation
We will group observability features under named configuration profiles.
- **Profiles**:
  - `local`: Developer UI, WebSocket, in-process stream enabled.
  - `ci`: WebSocket, Loki, Prometheus disabled; minimal reporting enabled.
  - `long_run`: Metrics, Parquet exports, DuckDB, event records enabled.
- **Scale Harness**:
  - Evaluates system performance, recording tick compute times and memory metrics, outputting artifact sizes and overhead indicators in a concise report.
