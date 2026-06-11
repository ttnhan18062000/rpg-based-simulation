---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE5-M24
phase: done
date: 2026-05-20
tags: [sim, obs, phase5, m24]
---

# TCK-20260520-SIM-OBS-PHASE5-M24

## Title

WebSocket Live Observatory API

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement Milestone 24: WebSocket Live Observatory API to expose live events to developer tools through a robust, thread-safe, and rate-limited WebSocket endpoint.

## Scope

- Create a brand new WebSocket endpoint `GET /api/v1/ws/observability/events`.
- Support subscription filtering via query parameters: `severity_min`, `entity_id`, `category` (mapping to `event_category`), `event_type`, `region_id`, `quest_id`.
- Support and validate subscription query parameters properly (valid severity, valid category, integer entity_id format). Reject invalid or unsupported filters clearly.
- Send standardized WebSocket outbound message types: `event`, `heartbeat`, `error`, `subscription_ack`, `dropped_event_notice`.
- Register the `LiveEventSubscriber` on connect and safely unregister it on disconnect.
- Implement safety limits: max subscribers limit, max queue per subscriber limit, and backpressure disconnect threshold.

## Out of Scope

- Client-to-server dynamic filter updates post-handshake (filters are defined via query params on connection).
- Full live monitoring HTML dashboard UI.

## Acceptance Criteria

- WebSocket successfully connects and receives matching events.
- Invalid query parameters or severity/category filters are rejected cleanly with a clear error payload.
- Active subscriptions are successfully cleaned up and unregistered upon client disconnection.
- Backpressure drops (if any) are reported to the client via `dropped_event_notice`.
- Periodic `heartbeat` keeps the connection alive.
- Concurrent client limit is strictly enforced.

## Related Tickets

- `TCK-20260520-SIM-OBS-PHASE5-M23` (Done)

## Related Docs

- `obs_sim_phase5.md`

## Related Stored Artifacts

- `stored_artifacts/TCK-20260520-SIM-OBS-PHASE5-M24/`

## Related Code Areas

- `src/api/ws/stream.py`
- `src/api/server.py`
- `src/observability/live/event_publisher.py`

## Assumptions / Open Questions

- Query parameter `category` is mapped to `event_category` in the subscription filter.
- Client limits will reject new connections with WebSocket close code 1008 if capacity is reached.

## Implementation Notes

- Designed a dedicated `asyncio.Lock` per WebSocket connection to guard and serialize concurrent outgoing `send_json(...)` calls from the polling loop and keep-alive heartbeat loop, preventing write-collision race conditions.
- Implemented robust filter validation for query parameters.
- Enforced a max subscriber limit of 10 concurrent clients using a global thread-safe counter.
- Developed a concurrent background `receive_task` to instantly catch client-initiated disconnections via `websocket.receive_text()`, allowing immediate, correct subscriber cleanup and counter decrements.
- Registered a testing endpoint `/api/v1/test/publish_event` to programmatically publish mock events from the integration test suite, allowing fast, synchronous, and 100% deterministic event stream testing.

## Test Summary

- Added exhaustive integration test suite in `tests/api/test_observability_websocket.py` verifying:
  - Valid handshake, subscriber ack, and heartbeat loop.
  - Query parameter validation and rejection of unsupported parameters (close code 1003).
  - Validation of severity levels and entity ID formatting (close code 1003).
  - Safe, deterministic live event delivery and category-based event filtering.
  - Enrollment and strict enforcement of the 10-subscriber capacity cap (close code 1008).
- Ran all tests in the API directory with 100% success.

## Files Changed

- `src/api/ws/stream.py`
- `src/api/server.py`
- `tests/api/test_observability_websocket.py`

## Completion Summary

- Implemented the WebSocket Live Observatory endpoint at `/api/v1/ws/observability/events` with lock-based write safety and instant cleanup.
- Verified system stability under multi-client concurrency.
