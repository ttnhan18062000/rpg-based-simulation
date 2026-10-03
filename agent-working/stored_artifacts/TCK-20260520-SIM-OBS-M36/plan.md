---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M36
artifact_type: plan
tags: [sim, obs, m36]
---

# Technical Plan: Production Stream Adapter

We will implement a resilient, highly-optimized, non-blocking Redis Streams integration to support out-of-process live analytics (Milestone 36).

## Proposed Components

### 1. RedisStreamAdapter Enhancement
- Move connection and `ping()` into a background safe loop or reconnect method `_connect()`.
- Maintain a lock-guarded `collections.deque` queue to prevent blocking of engine threads.
- Implement backpressure policy logic:
  - Bounded size: `max_queue_size`.
  - Drop policy: Drop `DEBUG` / `INFO` immediately if queue is full.
  - If a high-severity event is queued, search for any low-severity items in the queue to evict; if none exist, drop the high-severity event.
- Background publishing thread popping and publishing elements continuously.
- Health status monitoring with `last_success_at`, `queue_size`, `backpressure_active` metrics.

### 2. RedisStreamConsumer (Consumer Group Interface)
- Create `RedisStreamConsumer` to register a consumer group on the Redis stream.
- Thread-safe read and ack loop logic with customizable callback handlers.
- Safe extraction preventing poison pill deadlocks on malformed payloads.

### 3. FastAPI Endpoint
- Register a live `/api/v1/observability/live/stream-health` endpoint that queries the active stream adapter singleton's `health()` data.

## Verification Checklist

### Unit Tests
- `tests/unit/observability/test_redis_stream_adapter.py`:
  - Verify non-blocking enqueue operations.
  - Verify backpressure evictions (low severity evicting, high severity dropping if full).
  - Verify fallback behavior when Redis is offline.

### Integration Tests
- `tests/integration/observability/test_stream_backpressure.py`:
  - Simulate slow publishing or buffer saturation and assert correct eviction distribution.
- `tests/integration/observability/test_stream_consumer_basic.py`:
  - Run live consumer group loop with local Redis service, asserting exact message routing and ACKs.
