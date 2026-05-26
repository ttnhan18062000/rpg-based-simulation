# Investigation: Live Event Publisher & Subscription Filters (Milestone 23)

## Concurrency and Performance Architecture
* **Requirement**: The simulation loop thread calls `EventRecorder.record()`. Any downstream live subscriptions (WebSockets, dev API clients) should ingest these events without blocking the execution path.
* **Solution**:
  * We will introduce a thread-safe `LiveEventSubscriber` that encapsulates a bounded event queue (`collections.deque` or a thread-safe queue) and its matching `SubscriptionFilter`.
  * The `LiveEventPublisher` will maintain a thread-safe registry of active subscribers under a lock.
  * When `publish(event)` is called, the publisher will safely iterate over registered subscribers and try to push the event onto their queue.
  * If a subscriber's queue is full, the backpressure policy will evict the oldest `DEBUG` or `INFO` events from that subscriber's queue. If no lower-severity events are available to evict and the queue is completely filled with high-severity (`WARNING`, `ERROR`, `CRITICAL`) events, it will evict the oldest event, increment a `dropped_events_count` tracker, and flag the subscriber if drops exceed a threshold.

## Filter Matching Logic
* **Severity Matching**: Standard levels map to integers (`DEBUG=0, INFO=1, WARNING=2, ERROR=3, CRITICAL=4`). The filter checks if the event's severity meets or exceeds the filter's `severity_min`.
* **Field Matchers**: Fields (`event_type`, `event_category`, `entity_id`, `region_id`, `quest_id`) check for exact matches if specified in the subscription filter.

## Event Recorder Integration
* **Trigger Point**: Hook into `EventRecorder.record()` immediately after appending the event to the local file/memory buffer.
* **Isolation**: All publisher calls inside the recorder will be wrapped in a broad `try/except` block, preventing downstream subscription or queueing bugs from impacting the primary simulation loop.
