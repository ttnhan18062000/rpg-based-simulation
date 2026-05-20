# Test Plan: Stream Adapter & Consumer

We will comprehensively test unit behaviors and integration resilience for the Production Stream Adapter.

## 1. Unit Tests
Target: `tests/unit/observability/test_redis_stream_adapter.py`

- **Test Non-Blocking Queue Ingestion**:
  - Enqueue a series of mock events.
  - Assert that `publish` returns immediately.
  - Mock `redis.Redis` and verify `xadd` is eventually called inside the background thread.
- **Test Backpressure Policies**:
  - Mock queue and fill it up.
  - Verify `DEBUG` / `INFO` are dropped and count is incremented.
  - Verify `WARNING` / `ERROR` evict existing `DEBUG` / `INFO` items in the queue.
  - Verify queue remains bounded.
- **Test Degradation & Fallbacks**:
  - Mock `ImportError` or client connection exceptions and assert the adapter enters a graceful degraded state without raising crashes.

## 2. Integration Tests
Target: `tests/integration/observability/test_stream_backpressure.py` and `tests/integration/observability/test_stream_consumer_basic.py`

- **Stream Backpressure Integration**:
  - Stand up a mock slow Redis connection or mock failures.
  - Saturate the system and assert eviction outcomes.
- **Consumer Group Basic Integration**:
  - Boot a local Redis server (if present, otherwise skip test gracefully).
  - Publish events to stream.
  - Spawn `RedisStreamConsumer` inside a test runner, consuming and acknowledging events.
  - Verify double-delivery protection and ack state.
