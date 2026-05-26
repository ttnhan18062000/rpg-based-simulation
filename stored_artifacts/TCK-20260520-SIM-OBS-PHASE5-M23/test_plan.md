# Test Plan: In-Process Event Publisher & Subscription Filters (Milestone 23)

We will use a comprehensive testing strategy covering pure unit filters, publisher concurrency and capacity, and end-to-end event recorder integration.

## Automated Tests

### 1. Subscription Filter Unit Tests (`test_subscription_filter.py`)
* Test category matches.
* Test severity minimum threshold logic (e.g. `severity_min="WARNING"` matches `WARNING`, `ERROR`, `CRITICAL` but drops `INFO`, `DEBUG`).
* Test entity ID matches.
* Test region ID and quest ID matches.
* Test unknown filters handling (ignored or rejected).

### 2. Live Event Publisher Unit Tests (`test_live_event_publisher.py`)
* Test registration and unregistration of multiple subscribers.
* Test that a subscriber receives only matching events.
* Test bounded capacity backpressure behavior:
  * Slow subscribers whose queues fill up should trigger oldest event eviction starting with low-severity (`DEBUG`, `INFO`).
  * Verify that high-severity events are preserved over low-severity events.
  * Verify dropped event counts.

### 3. Integration Tests (`test_event_recorder_live_publish.py`)
* Test that `EventRecorder.record()` records events locally in the memory buffer, writes them to the JSONL log file, AND successfully publishes them to any registered subscribers.
* Verify that if publishing fails (e.g., a buggy subscriber raises an error), the event is still written to the log file and stored in memory.
* Verify that if live observability is disabled, events are not published but still written to log files.
