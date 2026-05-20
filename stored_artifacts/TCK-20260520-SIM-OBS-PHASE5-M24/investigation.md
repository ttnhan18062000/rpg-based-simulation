# Investigation: WebSocket Live Observatory API

We have investigated the existing WebSocket and routing infrastructures in the V2 engine.

## 1. Existing Endpoints (`src/api/ws/stream.py`)
- `/ws`: Legacy-compatible binary/JSON real-time state streaming.
- `/ws/observe`: WebSocket endpoint filtering standard `SimulationEvent` streams by a single `entity_id`.

## 2. API Router Mounting (`src/api/server.py`)
- The main FastAPI router `stream.router` is mounted under `/api/v1` prefix:
  `app.include_router(stream.router, prefix="/api/v1")`
- A new WebSocket router `/ws/observability/events` will resolve at `/api/v1/ws/observability/events`.

## 3. Subscription & Filter Capabilities (`src/observability/live/event_publisher.py`)
- `LiveEventPublisher`: Managing standard registered `LiveEventSubscriber` objects.
- `SubscriptionFilter`: Model with fields: `event_type`, `event_category`, `severity_min`, `entity_id`, `region_id`, `quest_id`.
- Backpressure disconnect flag is set to `True` if drops >= 50.

## 4. Design Criteria for WebSocket API (Milestone 24)
- **Validation**:
  - `severity_min`: Must be one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (case-insensitive).
  - `category` / `event_category`: Must be one of `"movement"`, `"combat"`, `"resource"`, `"economy"`, `"inventory"`, `"quest"`, `"strategy"`, `"social"`, `"lifecycle"`, `"region"`, `"infrastructure"`, `"hard_law"`, `"anomaly"` (case-insensitive).
  - `entity_id`: Must be convertible to an integer.
  - Reject unsupported query parameter keys.
- **Safety Limits**:
  - Max concurrent WebSocket subscribers = 10.
  - Max queue size = 500 (standard capacity for `LiveEventSubscriber`).
  - Max event payload size check (ensure event Pydantic models are serialized to JSON safe representation).
  - Idle timeout: Auto-disconnect if the socket remains active without ticks/activities for a long period or keep-alive heartbeat ping fails.
- **WebSocket outbound message structures**:
  - `event`
  - `heartbeat`
  - `error`
  - `subscription_ack`
  - `dropped_event_notice`
