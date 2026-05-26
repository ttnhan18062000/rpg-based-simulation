from __future__ import annotations
import threading
from typing import Optional
from src.observability.config import ObservabilityConfig
from src.observability.stream.base import EventStreamAdapter
from src.observability.stream.adapters import (
    NullEventStreamAdapter,
    InProcessEventStreamAdapter,
    RedisStreamAdapter
)

_adapter: Optional[EventStreamAdapter] = None
_lock = threading.Lock()


def get_event_stream_adapter() -> EventStreamAdapter:
    """
    Thread-safe factory resolving and returning the singleton EventStreamAdapter instance.
    Caching the instance avoids redundant connection establishment overhead.
    """
    global _adapter
    with _lock:
        if _adapter is not None:
            return _adapter

        backend = ObservabilityConfig.get_stream_backend().lower().strip()

        if backend == "redis":
            _adapter = RedisStreamAdapter(
                redis_url=ObservabilityConfig.get_redis_url(),
                stream_name=ObservabilityConfig.get_stream_name(),
                max_queue_size=ObservabilityConfig.get_max_queue_size()
            )
        elif backend == "null":
            _adapter = NullEventStreamAdapter()
        else:
            _adapter = InProcessEventStreamAdapter()

        return _adapter


def reset_event_stream_adapter() -> None:
    """
    Closes the current active adapter and resets the singleton reference.
    Essential for unit testing isolated adapter behaviors.
    """
    global _adapter
    with _lock:
        if _adapter is not None:
            try:
                _adapter.close()
            except Exception:
                pass
            _adapter = None
