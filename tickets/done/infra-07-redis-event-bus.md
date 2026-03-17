# [DONE] infra-07: Redis Streams Event Bus

## Objective
Replace the in-memory Python `asyncio.Queue` mechanism with a Redis Streams event bus. This decouples the core `EngineManager` simulation loop from the FastAPI HTTP tier and allows the API to scale horizontally.

## Rationale
Currently, the Python engine loop iterates over a set of registered listener functions and pushes State Snapshots directly into individual client `asyncio.Queue` objects. This couples the execution context of the engine directly to open HTTP connections. 

By introducing Redis (`redis.asyncio`), the Engine simply publishes `XADD` commands to a `sim:ticks` stream. Multiple FastAPI instances can then independently subscribe to this stream (`XREAD`) and relay the deltas to frontend SSE connections. This perfectly supplements `infra-04` (Realtime State Streaming) by making it distributed.

## Scope & Affected Systems
- **Target Files**: `docker-compose.yml`, `pyproject.toml`, `src/api/engine_manager.py`, `src/api/routes/stream.py`
- **Implementation Steps**:
  1. Add a `redis` service to `docker-compose.yml`.
  2. Add `redis` to our Python dependencies (`pyproject.toml`).
  3. Rewrite `EngineManager._publish_snapshot_and_events` to serialize the Snapshot delta and SimEvents to JSON, then `XADD` them to a Redis Stream (`sim:stream`).
  4. Rewrite `src/api/routes/stream.py` (the `/api/v1/stream` endpoint) to connect to Redis and `XREADBLOCK` on the stream, formatting the received data as SSE strings.
  5. Refactor automated testing to either mock `redis` or skip actual execution tests when a Redis instance is missing.

## Dependencies
- Must be completed before any horizontal scaling of the `backend` container is attempted.

## Acceptance Criteria
- Engine loop completes its ticks without tracking specific `subscriber` callbacks.
- FastAPI endpoints retrieve ticks from Redis without error.
- SSE stream matches the original functionality structurally but routes through Redis infrastructure.
