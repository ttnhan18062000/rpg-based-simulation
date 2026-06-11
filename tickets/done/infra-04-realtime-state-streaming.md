---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: infra-04-realtime-state-streaming
phase: done
date: unknown
tags: [infra, realtime, state, streaming]
---

# [DONE] infra-04: Realtime State Streaming (WebSockets / SSE)

## Objective
Replace the `/api/v1/state` HTTP polling mechanism with a persistent streaming connection that pushes delta updates to the frontend.

## Rationale
Polling every 80ms forces continuous and aggressive JSON serialization of the *entire* `WorldState` snapshot. As entity numbers grow, this ties up FastAPI threads and overloads network bandwidth. Delta streaming only diffs (changed entities) significantly slashes overhead.

## Scope & Affected Systems
- **Target Files**: `src/api/routes/stream.py` (new), `src/api/app.py`, `frontend/src/hooks/useSimulation.ts`.
- **Implementation Steps**:
  1. Add `websockets` (or `sse-starlette`) to backend requirements.
  2. Implement an Entity-Level Delta tracker in `EngineManager` (diffing the current and previous tick's `Snapshot`).
  3. Create a `/api/v1/stream` endpoint in FastAPI that yields atomic state patches (e.g., `{"tick": 1150, "updated_entities": [...], "removed_entities": [...]}`).
  4. Refactor the React `useSimulation` hook to connect via WebSocket/EventSource, listen for patches, and apply them cleanly to a local React state store.
  5. (Optional but recommended) Swap JSON encoding for MessagePack across the socket.

## Dependencies
- Non-blocking. Ideal to have `infra-03` telemetry in place to measure the exact latency improvements. Must be completed before hitting 1000+ entities in Epic-17.

## Acceptance Criteria
- API payload sizes decrease by 90%+ during idle ticks.
- Client successfully reconstructs full snapshot locally from deltas without visual stutter.
- Backend CPU utilization drops under heavy client connection load.

**Tier:** standard
**Type:** chore
**Priority:** P1
