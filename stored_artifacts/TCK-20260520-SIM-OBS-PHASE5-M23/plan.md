# Implementation Plan: In-Process Event Publisher & Subscription Filters (Milestone 23)

## User Review Required
> [!NOTE]
> This is a purely in-process event publishing system designed to remain extremely fast and lightweight. It provides thread-safe subscription queues for real-time observability (e.g. WebSockets) without writing to disks or external brokers.

## Proposed Changes

### Observability Layer

#### [NEW] [event_publisher.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/live/event_publisher.py)
* Define the `SubscriptionFilter` Pydantic model.
* Define `LiveEventSubscriber` class with:
  - Bounded queue (default capacity 500 events).
  - Backpressure policy: evicts oldest low-severity events first, tracks dropped events.
* Define `LiveEventPublisher` class providing registration, unregistration, thread-safe publishing, and singleton access.

#### [MODIFY] [event_recorder.py](file:///home/vboxuser/Work/rpg-based-simulation/src/observability/event_recorder.py)
* Add a reference to the global `LiveEventPublisher` instance (or initialize an active publisher instance).
* In `record(event)`, publish the event to matching subscribers with error isolation.

## Verification Plan

### Automated Tests
* **Unit Tests**:
  * `tests/unit/observability/test_subscription_filter.py`: Matches category, severity levels, specific entities, invalid fields.
  * `tests/unit/observability/test_live_event_publisher.py`: Bounded queue, registering/unregistering, backpressure and slow clients.
* **Integration Tests**:
  * `tests/integration/observability/test_event_recorder_live_publish.py`: Verifies EventRecorder successfully delegates to LiveEventPublisher after recording, maintaining file writes and live queues.
