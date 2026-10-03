---
status: historical
layer: misc
authority: P2
audience: agent
ticket_id: TCK-20260520-SIM-OBS-M36
artifact_type: investigation
tags: [sim, obs, m36]
---

# Investigation: Stream Adapter Design Considerations

We evaluated the stream adapter transport mechanisms, interface structure, and architectural boundaries in the codebase.

## 1. Decoupling Engine Computing Loops
The simulator engine execution ticks run on a deterministic pipeline. If we perform blocking socket/network writes directly during the tick loop:
- Network jitter/latency will degrade the tick rate (e.g. going from <1ms ticks to >100ms ticks).
- Connection dropouts will completely block simulation progress.
- Outages will trigger thread timeouts.

Therefore, `RedisStreamAdapter` **must** employ a Producer-Consumer pattern where:
- The engine thread produces events to an in-memory queue.
- A dedicated background daemon thread consumes from the queue and publishes to Redis stream.

## 2. Queue Backpressure Policy
If Redis is completely offline or slow, the local queue will eventually fill up. If we don't drop events, the queue will grow unboundedly, leading to `OutOfMemory` errors.
If we use a standard queue, we either block (which we cannot do) or raise a `Full` error.
To protect system reliability under pressure, we drop `DEBUG` / `INFO` events first, protecting `WARNING` / `ERROR` / `CRITICAL` events.
By using a thread-safe `collections.deque` and sliding scanning, we can selectively evict low-priority events to squeeze in high-severity events.

## 3. Redis Streams (xadd/xreadgroup)
Redis Streams are ideal for out-of-process messaging:
- `xadd stream_key * field1 val1 ...` adds a message to the stream with auto-generated ID.
- `maxlen` option limits stream length to prevent unbounded Redis storage usage.
- `xgroup_create` registers consumer groups to trace delivery.
- `xreadgroup` reads from the stream as part of a group, keeping track of pending events for each consumer.
- `xack` acknowledges receipt of message.
