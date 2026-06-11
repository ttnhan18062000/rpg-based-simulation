---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-PHASE5-M24
artifact_type: plan
tags: [sim, obs, phase5, m24]
---

# Implementation Plan: WebSocket Live Observatory API

We propose a robust, production-grade WebSocket API exposing simulation events to external developer tools with strict validation and security controls.

## Proposed Changes

### Component: WebSocket Server Routing (`src/api/ws/stream.py`)
- We will add the endpoint `@router.websocket("/ws/observability/events")`.
- It will parse and validate incoming query filters from `websocket.query_params`.
- Max websocket subscribers will be strictly capped at 10.
- Heartbeats will run asynchronously to maintain connection health.

#### Detailed Flow of the Connection

1. **Safety and Client Capacity Validation**:
   - Check if current active connections exceed `MAX_WEBSOCKET_SUBSCRIBERS = 10`.
   - If exceeded, close connection with code 1008 (Policy Violation) and exit.

2. **Query Parsing and Parameter Validation**:
   - Read from `websocket.query_params`.
   - Allowed parameters: `severity_min`, `entity_id`, `category` (mapping to `event_category`), `event_category`, `event_type`, `region_id`, `quest_id`.
   - Reject any query parameter not in the allowed list with WebSocket close code 1003 (Unsupported Data).
   - Validate `severity_min`: case-insensitive check against `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
   - Validate `category`/`event_category`: case-insensitive check against standard EventCategory literals.
   - Validate `entity_id`: must be parsable as a valid integer.
   - If validation fails, send a structured `error` message and close connection with code 1003.

3. **Handshake and Acknowledgment**:
   - Accept connection `await websocket.accept()`.
   - Create `SubscriptionFilter` and `LiveEventSubscriber`.
   - Register subscriber with `LiveEventPublisher.get_instance()`.
   - Send `subscription_ack` outbound message containing the resolved subscription filters.

4. **Event Streaming and Pacing Loop**:
   - Run a periodic tick loop (e.g., every 50ms).
   - Retrieve queued events using `subscriber.get_events()`.
   - For each event, send a serialized JSON payload of shape:
     ```json
     {
       "type": "event",
       "run_id": "...",
       "event": { ...SimulationEvent... }
     }
     ```
   - Track drops. If drops increase, send a `dropped_event_notice` with current count.
   - If `subscriber.disconnect_flag` is set, close connection with code 1008 and clean up.

5. **Heartbeat and Keep-Alive**:
   - Concurrently execute a heartbeat loop. Every 5 seconds, send an outbound `heartbeat` message.

6. **Cleanup on Disconnect**:
   - On `WebSocketDisconnect` or client disconnect, unregister subscriber and decrement active client count.
