from __future__ import annotations
import os
import json
import pytest
from src.observability.events import SimulationEvent
from src.observability.stream.adapters import RedisStreamAdapter
from src.observability.stream.consumer import RedisStreamConsumer

# Check local Redis availability
redis_available = False
try:
    import redis
    client = redis.from_url("redis://localhost:6379/0", socket_connect_timeout=1.0)
    client.ping()
    redis_available = True
    client.close()
except Exception:
    redis_available = False

pytestmark = pytest.mark.skipif(
    not redis_available,
    reason="Local Redis server is not running or unreachable on port 6379."
)


def make_event(message: str) -> SimulationEvent:
    return SimulationEvent(
        event_type="consumer_test",
        event_category="economy",
        severity="INFO",
        source_system="integration",
        message=message,
        tick=5
    )


def test_live_stream_consumer_group_lifecycle():
    """
    Verifies that the consumer connects, registers consumer group,
    receives published events, invokes callbacks, ACKs them,
    and handles bad payloads elegantly.
    """
    stream_name = "integration:test:consumer_stream"
    group_name = "integration:test:consumer_group"
    
    # 1. Clear any pre-existing stream key in local Redis to guarantee clean test
    import redis
    rc = redis.from_url("redis://localhost:6379/0")
    rc.delete(stream_name)
    
    adapter = RedisStreamAdapter(
        redis_url="redis://localhost:6379/0",
        stream_name=stream_name,
        max_queue_size=10
    )
    
    # Publish 3 valid events
    adapter.publish(make_event("message alpha"))
    adapter.publish(make_event("message beta"))
    adapter.publish(make_event("message gamma"))
    adapter.flush()
    
    # 2. Boot consumer group
    consumer = RedisStreamConsumer(
        redis_url="redis://localhost:6379/0",
        stream_name=stream_name,
        group_name=group_name,
        consumer_name="test_worker"
    )
    
    received_messages = []
    
    def event_handler(event: SimulationEvent):
        received_messages.append(event.message)
        
    # Read & process
    processed = consumer.read_and_process(event_handler, block_ms=500)
    assert processed == 3
    assert "message alpha" in received_messages
    assert "message beta" in received_messages
    assert "message gamma" in received_messages
    
    # Read again, should find no new events
    processed_empty = consumer.read_and_process(event_handler, block_ms=100)
    assert processed_empty == 0
    
    # 3. Inject a malformed event (poison pill) directly to Redis stream to verify robustness
    rc.xadd(stream_name, {"payload": "invalid-json-payload-string"})
    
    # Consumer should read the malformed payload, handle it gracefully, log error, and ACK to clear it
    processed_poison = consumer.read_and_process(event_handler, block_ms=200)
    assert processed_poison == 0  # 0 successfully processed, but cleared from queue
    
    # 4. Cleanup
    adapter.close()
    consumer.close()
    rc.delete(stream_name)
    rc.close()


def test_handler_exception_triggers_bounded_retry_then_dlq_live():
    """
    A handler that always raises must be retried up to MAX_DELIVERY_ATTEMPTS via real
    Redis PEL/XCLAIM state, then routed to the derived DLQ stream -- never silently dropped.
    """
    stream_name = "integration:test:dlq_stream"
    group_name = "integration:test:dlq_group"

    import redis
    rc = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    rc.delete(stream_name)
    rc.delete(f"{stream_name}:dlq")

    adapter = RedisStreamAdapter(
        redis_url="redis://localhost:6379/0",
        stream_name=stream_name,
        max_queue_size=10
    )
    adapter.publish(make_event("will always fail"))
    adapter.flush()

    consumer = RedisStreamConsumer(
        redis_url="redis://localhost:6379/0",
        stream_name=stream_name,
        group_name=group_name,
        consumer_name="test_worker"
    )
    consumer.connect()
    # Reclaim only considers entries idle at least RECLAIM_IDLE_MS; shrink it so the test
    # doesn't need to sleep 30s per sweep.
    consumer.RECLAIM_IDLE_MS = 50

    call_count = {"n": 0}

    def failing_handler(event: SimulationEvent):
        call_count["n"] += 1
        raise RuntimeError("handler always fails")

    consumer.read_and_process(failing_handler, block_ms=200)
    assert call_count["n"] == 1

    import time
    for _ in range(consumer.MAX_DELIVERY_ATTEMPTS - 1):
        time.sleep(0.06)
        consumer.read_and_process(failing_handler, block_ms=100)

    assert call_count["n"] == consumer.MAX_DELIVERY_ATTEMPTS

    # One final sweep to route the now-exhausted entry to the DLQ.
    time.sleep(0.06)
    consumer.read_and_process(failing_handler, block_ms=100)
    assert call_count["n"] == consumer.MAX_DELIVERY_ATTEMPTS

    dlq_entries = rc.xrange(f"{stream_name}:dlq")
    assert len(dlq_entries) == 1
    dlq_fields = dlq_entries[0][1]
    assert dlq_fields["message"] == "will always fail"
    assert dlq_fields["dlq_reason"] == "max delivery attempts exceeded"

    pending = rc.xpending(stream_name, group_name)
    assert pending["pending"] == 0

    adapter.close()
    consumer.close()
    rc.delete(stream_name)
    rc.delete(f"{stream_name}:dlq")
    rc.close()
