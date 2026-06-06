# TCK-20260520-SIM-OBS-PHASE5-M23

## Title
In-Process Event Publisher and Subscription Filters

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Create a lightweight, in-process event publishing system that enables downstream developer tooling (like live WebSockets) to subscribe to real-time simulation events with precise filters without blocking the simulation tick loop.

## Scope
- Implement `SubscriptionFilter` matching by:
  - event_type (exact or wildcard)
  - event_category (exact match)
  - severity_min (minimum level comparison)
  - entity_id (associated entity)
  - region_id (region)
  - quest_id (quest)
- Implement `LiveEventSubscriber` containing a thread-safe, bounded event queue, associated filter, and dropped event stats.
- Implement `LiveEventPublisher` providing:
  - Registering and unregistering subscribers.
  - Safe, non-blocking publishing loop executing matching logic.
  - Simple, robust backpressure: when a subscriber's queue is full, evict the oldest DEBUG/INFO events first, count dropped events, and disconnect extremely slow clients.
- Integrate `LiveEventPublisher` with `EventRecorder`:
  - After recording an event, if live observability is active, publish the event.
  - Publisher errors are completely isolated, ensuring that a publisher failure never affects simulation execution or file persistence.

## Out of Scope
- Out-of-process event brokers (Redis, Kafka, NATS).
- WebSocket route registration (reserved for Milestone 24).
- Dynamic SQL-like query language for filters.

## Acceptance Criteria
- Subscribers only receive events that match their `SubscriptionFilter`.
- Extremely slow subscribers do not block or delay the simulation tick loop.
- Subscriptions are thread-safe and isolated.
- 100% automated test coverage.

## Related Tickets
- `TCK-20260520-SIM-OBS-PHASE5-M22`

## Related Docs
- `obs_sim_phase5.md`

## Related Stored Artifacts
- None

## Related Code Areas
- `src/observability/event_recorder.py`
- `src/observability/live/`

## Assumptions / Open Questions
- We assume standard Python `queue.Queue` or a custom thread-safe list queue can be used for subscription buffers.
- Bounded capacity of queues defaults to 500 events to prevent memory ballooning.

## Implementation Notes
- Designed a high-performance, thread-safe, memory-bounded, and completely isolated publisher/subscriber system in `src/observability/live/event_publisher.py`.
- Implemented an elegant backpressure eviction policy that evicts the oldest of the absolute lowest severity events among DEBUG/INFO first to preserve higher-severity event context, and tracks dropped counts to auto-disconnect extremely slow clients.
- Linked the publisher into `EventRecorder.record()` under absolute `try-except` isolation to guarantee zero-risk to simulation tick loop or persistence.

## Test Summary
- Added unit test suite `tests/unit/observability/test_subscription_filter.py` covering category, severity order thresholds, specific entity matching, and extra-filter forbid configurations.
- Added unit test suite `tests/unit/observability/test_live_event_publisher.py` covering subscription registries, routing, bounded capacity backpressure, lowest-severity preservation, and slow client disconnection.
- Added integration test suite `tests/integration/observability/test_event_recorder_live_publish.py` covering end-to-end recording, disk persistence, and publisher routing integration.
- Verified 100% green build on all 85 tests.

## Files Changed
- `src/observability/live/event_publisher.py` (NEW)
- `src/observability/event_recorder.py` (MODIFY)
- `tests/unit/observability/test_subscription_filter.py` (NEW)
- `tests/unit/observability/test_live_event_publisher.py` (NEW)
- `tests/integration/observability/test_event_recorder_live_publish.py` (NEW)

## Completion Summary
- Successfully established a secure, live-observability event pipeline. Any downstream subscriber can selectively register and listen to filtered simulation streams in a zero-overhead, non-blocking manner.
