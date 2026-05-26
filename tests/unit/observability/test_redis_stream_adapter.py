from __future__ import annotations
import sys
import time
import pytest
from unittest.mock import MagicMock, patch
from src.observability.events import SimulationEvent
from src.observability.stream.adapters import RedisStreamAdapter


def make_mock_event(severity: str = "INFO", message: str = "test message") -> SimulationEvent:
    return SimulationEvent(
        event_type="test",
        event_category="movement",
        severity=severity,
        source_system="test_system",
        message=message,
        tick=1
    )


def test_redis_adapter_async_non_blocking():
    """Verify that event publishing is asynchronous, returns immediately, and eventually publishes to Redis."""
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    
    mock_redis = MagicMock()
    mock_redis.from_url.return_value = mock_client
    
    with patch.dict("sys.modules", {"redis": mock_redis}):
        adapter = RedisStreamAdapter(
            redis_url="redis://localhost:6379/0",
            stream_name="test:events",
            max_queue_size=10
        )
        
        event = make_mock_event(severity="INFO", message="Async testing")
        
        # Publish should return immediately
        adapter.publish(event)
        
        # Wait a short duration for the background thread to pick up the event and publish it
        adapter.flush()
        
        assert mock_client.xadd.call_count == 1
        call_args = mock_client.xadd.call_args[0]
        assert call_args[0] == "test:events"
        payload = call_args[1]
        assert payload["severity"] == "INFO"
        assert payload["message"] == "Async testing"
        
        # Check health metrics
        health = adapter.health()
        assert health["status"] == "healthy"
        assert health["published_events"] == 1
        assert health["dropped_events"] == 0
        assert health["queue_size"] == 0
        
        adapter.close()


def test_redis_adapter_backpressure_eviction_and_dropping():
    """Verify that backpressure selectively drops DEBUG/INFO and prioritizes high-severity events."""
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    
    # We will block the background worker from completing or just not start a fast publisher thread.
    # To easily simulate a full queue, we can temporarily disable the worker thread from consuming
    # or just configure the adapter queue capacity very low (e.g. max_queue_size = 3).
    mock_redis = MagicMock()
    mock_redis.from_url.return_value = mock_client
    
    with patch.dict("sys.modules", {"redis": mock_redis}):
        adapter = RedisStreamAdapter(
            redis_url="redis://localhost:6379/0",
            stream_name="test:events",
            max_queue_size=3
        )
        
        # Stop background worker immediately to keep items in queue
        adapter._running = False
        adapter._queue_cond.acquire()
        adapter._queue_cond.notify_all()
        adapter._queue_cond.release()
        if adapter._worker_thread:
            adapter._worker_thread.join(timeout=1.0)
        
        # Now enqueue 3 low-severity events
        ev_info1 = make_mock_event(severity="INFO", message="info 1")
        ev_info2 = make_mock_event(severity="DEBUG", message="debug 2")
        ev_info3 = make_mock_event(severity="INFO", message="info 3")
        
        adapter.publish(ev_info1)
        adapter.publish(ev_info2)
        adapter.publish(ev_info3)
        
        assert len(adapter._queue) == 3
        assert adapter.dropped_count == 0
        
        # 4. Enqueue a fourth low-severity event. It should be dropped immediately.
        ev_info4 = make_mock_event(severity="INFO", message="info 4")
        adapter.publish(ev_info4)
        
        assert len(adapter._queue) == 3
        assert adapter.dropped_count == 1
        assert adapter.backpressure_active is True
        
        # 5. Enqueue a high-severity event (WARNING). It should evict a low-severity event (e.g. ev_info1)
        ev_warn = make_mock_event(severity="WARNING", message="warn high")
        adapter.publish(ev_warn)
        
        # Queue should still be at capacity
        assert len(adapter._queue) == 3
        assert adapter.dropped_count == 2  # Incremented due to eviction
        
        # Verify that WARNING is in the queue, and ev_info1 (the first low severity item found) was removed
        queue_messages = [item.message for item in adapter._queue]
        assert "warn high" in queue_messages
        assert "info 1" not in queue_messages
        
        # 6. If the queue is saturated with only high-severity events, a new high-severity event should be dropped.
        # Clear the queue first
        adapter._queue.clear()
        adapter.dropped_count = 0
        
        ev_err1 = make_mock_event(severity="ERROR", message="err 1")
        ev_crit2 = make_mock_event(severity="CRITICAL", message="crit 2")
        ev_warn3 = make_mock_event(severity="WARNING", message="warn 3")
        
        adapter.publish(ev_err1)
        adapter.publish(ev_crit2)
        adapter.publish(ev_warn3)
        
        assert len(adapter._queue) == 3
        
        # Publish an ERROR event. No low-severity items exist, so it should be dropped.
        ev_err4 = make_mock_event(severity="ERROR", message="err 4")
        adapter.publish(ev_err4)
        
        assert len(adapter._queue) == 3
        assert adapter.dropped_count == 1
        assert "err 4" not in [item.message for item in adapter._queue]
        
        adapter.close()


def test_redis_adapter_degraded_fallback():
    """Verify that RedisStreamAdapter remains degraded but safe when connection ping fails."""
    mock_client = MagicMock()
    mock_client.ping.side_effect = Exception("Redis unreachable")
    
    mock_redis = MagicMock()
    mock_redis.from_url.return_value = mock_client
    
    with patch.dict("sys.modules", {"redis": mock_redis}):
        adapter = RedisStreamAdapter(
            redis_url="redis://invalid-host:6379/0",
            stream_name="test:events",
            max_queue_size=5
        )
        
        health = adapter.health()
        assert health["status"] == "degraded"
        assert health["connected"] is False
        assert "Connection failed" in health["last_publish_error"]
        
        # Enqueuing should drop the event gracefully rather than blocking or throwing
        adapter.publish(make_mock_event())
        adapter.flush()
        assert adapter.dropped_count == 1
        
        adapter.close()
