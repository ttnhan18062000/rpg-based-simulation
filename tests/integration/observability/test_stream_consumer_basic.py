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
