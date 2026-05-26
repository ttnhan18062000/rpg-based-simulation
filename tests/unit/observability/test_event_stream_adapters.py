from __future__ import annotations
import sys
import pytest
from unittest.mock import MagicMock, patch
from src.observability.stream.adapters import (
    NullEventStreamAdapter,
    InProcessEventStreamAdapter,
    RedisStreamAdapter
)
from src.observability.stream.factory import get_event_stream_adapter, reset_event_stream_adapter
from src.observability.config import ObservabilityConfig


def test_null_adapter():
    adapter = NullEventStreamAdapter()
    assert adapter.health()["status"] == "healthy"
    
    event = MagicMock()
    # Should not raise any exception
    adapter.publish(event)
    adapter.close()


def test_in_process_adapter():
    mock_publisher = MagicMock()
    mock_publisher.subscribers = []
    mock_publisher.total_published = 0
    mock_publisher.total_dropped = 0
    with patch("src.observability.live.event_publisher.LiveEventPublisher.get_instance", return_value=mock_publisher):
        adapter = InProcessEventStreamAdapter()
        assert adapter.health()["status"] == "healthy"
        
        event = MagicMock()
        adapter.publish(event)
        mock_publisher.publish.assert_called_once_with(event)
        adapter.close()


def test_redis_adapter_resilient_missing_library():
    """Ensures RedisStreamAdapter handles the absence of redis library gracefully."""
    # Temporarily remove redis module from sys.modules if it exists
    original_redis = sys.modules.get("redis")
    if "redis" in sys.modules:
        del sys.modules["redis"]
        
    try:
        adapter = RedisStreamAdapter("redis://localhost:6379/0", "test:events", 100)
        assert adapter.health()["status"] == "degraded"
        # Should gracefully drop events rather than crashing
        adapter.publish(MagicMock())
        adapter.close()
    finally:
        if original_redis is not None:
            sys.modules["redis"] = original_redis


def test_redis_adapter_publish_resilience():
    """Ensures RedisStreamAdapter handles connection drops gracefully without loop stalling."""
    mock_redis_client = MagicMock()
    mock_redis_client.ping.return_value = True
    mock_redis_client.xadd.side_effect = Exception("Connection lost")
    
    mock_redis_lib = MagicMock()
    mock_redis_lib.from_url.return_value = mock_redis_client
    
    with patch.dict("sys.modules", {"redis": mock_redis_lib}):
        adapter = RedisStreamAdapter("redis://localhost:6379/0", "test:events", 100)
        assert adapter.health()["status"] == "healthy"
        
        # Publish should catch and log exception internally, without throwing to stalling the loop
        adapter.publish(MagicMock())
        adapter.close()


def test_factory_resolutions(monkeypatch):
    monkeypatch.setenv("SIM_STREAM_BACKEND", "null")
    reset_event_stream_adapter()
    try:
        adapter = get_event_stream_adapter()
        assert isinstance(adapter, NullEventStreamAdapter)
        
        # Singleton check
        adapter2 = get_event_stream_adapter()
        assert adapter is adapter2
    finally:
        reset_event_stream_adapter()
