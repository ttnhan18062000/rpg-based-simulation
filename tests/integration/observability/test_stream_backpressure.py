from __future__ import annotations
import os
import time
import pytest
from src.observability.events import SimulationEvent
from src.observability.stream.adapters import RedisStreamAdapter

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


def make_event(severity: str, message: str) -> SimulationEvent:
    return SimulationEvent(
        event_type="integration_test",
        event_category="combat",
        severity=severity,
        source_system="integration",
        message=message,
        tick=10
    )


def test_live_backpressure_and_eviction_integration():
    """
    Stand up a stream adapter with capacity 5.
    We saturate it with low severity events, verify dropping,
    then enqueue high severity and assert eviction under actual load.
    """
    adapter = RedisStreamAdapter(
        redis_url="redis://localhost:6379/0",
        stream_name="integration:test:events",
        max_queue_size=5
    )
    
    # Temporarily pause background worker processing to force backlog accumulation
    adapter._running = False
    with adapter._queue_lock:
        adapter._queue_cond.notify_all()
    if adapter._worker_thread:
        adapter._worker_thread.join(timeout=1.0)
        
    # Queue is empty. Fill with 5 low priority events.
    for i in range(5):
        adapter.publish(make_event("INFO", f"info {i}"))
        
    assert len(adapter._queue) == 5
    assert adapter.dropped_count == 0
    
    # 6th low priority event must be dropped.
    adapter.publish(make_event("DEBUG", "dropped debug"))
    assert len(adapter._queue) == 5
    assert adapter.dropped_count == 1
    
    # 7th event is high priority (ERROR). It evicts the first INFO event in the queue.
    adapter.publish(make_event("ERROR", "important error"))
    assert len(adapter._queue) == 5
    assert adapter.dropped_count == 2
    
    messages = [ev.message for ev in adapter._queue]
    assert "important error" in messages
    assert "info 0" not in messages  # evicted
    
    adapter.close()
