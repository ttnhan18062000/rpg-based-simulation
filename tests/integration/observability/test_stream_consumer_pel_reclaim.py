from __future__ import annotations
import time
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
        event_type="pel_reclaim_test",
        event_category="economy",
        severity="INFO",
        source_system="integration",
        message=message,
        tick=1
    )


def test_orphaned_pel_message_reclaimed_via_xclaim():
    """
    Simulates a process dying after the handler succeeded but before XACK ran: the message
    stays in the consumer group's PEL. A fresh consumer's reclaim sweep must eventually
    redeliver it exactly once via XCLAIM, not lose it and not redeliver it forever.
    """
    stream_name = "integration:test:pel_reclaim_stream"
    group_name = "integration:test:pel_reclaim_group"

    rc = redis.from_url("redis://localhost:6379/0")
    rc.delete(stream_name)

    adapter = RedisStreamAdapter(
        redis_url="redis://localhost:6379/0",
        stream_name=stream_name,
        max_queue_size=10
    )
    adapter.publish(make_event("orphaned message"))
    adapter.flush()

    # "Dead" consumer: reads the message (advancing delivery/PEL state) but never acks it,
    # simulating a process death between handler success and the XACK call.
    dead_consumer = RedisStreamConsumer(
        redis_url="redis://localhost:6379/0",
        stream_name=stream_name,
        group_name=group_name,
        consumer_name="dead_worker"
    )
    dead_consumer.connect()
    raw = dead_consumer.client.xreadgroup(
        groupname=group_name,
        consumername="dead_worker",
        streams={stream_name: ">"},
        count=10,
        block=200
    )
    assert raw and raw[0][1], "expected the published message to be delivered"
    dead_consumer.close()

    # A fresh consumer's reclaim sweep should pick up the orphaned entry once it's idle
    # past RECLAIM_IDLE_MS.
    live_consumer = RedisStreamConsumer(
        redis_url="redis://localhost:6379/0",
        stream_name=stream_name,
        group_name=group_name,
        consumer_name="live_worker"
    )
    live_consumer.connect()
    live_consumer.RECLAIM_IDLE_MS = 50

    received = []

    def handler(event: SimulationEvent):
        received.append(event.message)

    time.sleep(0.1)
    live_consumer.read_and_process(handler, block_ms=100)

    assert received == ["orphaned message"]

    pending = rc.xpending(stream_name, group_name)
    assert pending["pending"] == 0

    # A second sweep must not redeliver the already-acked message.
    received.clear()
    live_consumer.read_and_process(handler, block_ms=100)
    assert received == []

    adapter.close()
    live_consumer.close()
    rc.delete(stream_name)
    rc.close()
