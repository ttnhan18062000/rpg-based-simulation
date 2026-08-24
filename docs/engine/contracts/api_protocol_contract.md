---
status: active
layer: engine
authority: P1
audience: developer
---

# API, Protocol, and Transport Compatibility Contract

This document defines the supported network and system interfaces for the engine.

## 1. REST API Parity
- **Base Path**: `/api/v1`
- **Supported Routes**:
    - `GET /health`: Engine liveness. Returns `status` (`ok` | `degraded` | `unhealthy`), computed
      from the V2EngineManager background tick thread's liveness and last-tick recency, independent
      of operator-pause state. Also returns `version`, `timestamp`, and an `engine` object
      (`thread_alive`, `paused`, `last_tick_age_seconds`, `staleness_threshold_seconds`,
      `errors_total`, `run_id`). HTTP 503 on `unhealthy` (thread dead); HTTP 200 for `ok`/`degraded`.
    - `GET /api/v1/state`: Current simulation summary (tick, entities count, seed).
    - `POST /api/v1/control/pause`: Pause simulation.
    - `POST /api/v1/control/resume`: Resume simulation.
- **Future Parity**: Full metadata and map routes will be recovered in subsequent phases if required for specific cutover scenarios.

## 2. WebSocket Protocol (BWS)
- **Endpoint**: `ws://[host]:[port]/api/v1/ws`
- **Handshake**: Clients must send `{"type": "handshake", "format": "json" | "msgpack"}` upon connection.
- **Payloads**:
    - **Initial**: Full state summary.
    - **Streaming**: Per-tick entity delta (`changed`/`removed`/`tick`/`events`, plus a
      `snapshot_as_of_tick` field attached per-connection) — not an unconditional full-state
      resend. Suppressed on quiet ticks (no changed/removed entities) except a 20-tick heartbeat.
      See `docs/observability/read_model_service_contract.md`'s `tick_delta` row for the presenter
      chain.
- **Serialization**: Supports JSON and MessagePack (binary).

## 3. Transport & Compression
- **GZip**: Supported for all HTTP responses over 512 bytes.
- **Timeouts**: API server respects standard HTTP timeouts; WebSocket has a 10-second inactivity buffer for queue management.

## 4. Headless Execution
- **CLI Mode**: Fully supported via `python3 -m src cli`.
- **System Service**: The engine is designed to run as a headless system process using `uvicorn` or similar ASGI servers.
- **Non-Interactive**: All configuration is handled via CLI flags, Environment variables, or YAML files.

## 5. Known Divergences
- **Frontend Serving**: The server currently does not mount the `frontend/dist` directory by default; it focuses on the API surface.
- **Redis Dependency**: The engine removes the mandatory Redis requirement for WebSocket streaming, using an in-process `StateBroadcaster` (via `V2EngineManager` listeners).
