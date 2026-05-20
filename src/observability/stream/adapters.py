from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Optional
from src.observability.events import SimulationEvent
from src.observability.stream.base import EventStreamAdapter

logger = logging.getLogger(__name__)


class NullEventStreamAdapter(EventStreamAdapter):
    """
    Event stream adapter that drops all events silently with zero overhead.
    Recommended for fast execution or test profiles with no observability requirements.
    """
    def __init__(self, **kwargs: Any) -> None:
        self.dropped_count = 0

    def publish(self, event: SimulationEvent) -> None:
        self.dropped_count += 1

    def publish_batch(self, events: List[SimulationEvent]) -> None:
        self.dropped_count += len(events)

    def health(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "backend": "null",
            "dropped_events": self.dropped_count
        }

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


class InProcessEventStreamAdapter(EventStreamAdapter):
    """
    Routes events in-process directly to the LiveEventPublisher broker.
    Maintains compatibility with Phase 5 WebSocket push infrastructure.
    """
    def __init__(self, **kwargs: Any) -> None:
        pass

    def publish(self, event: SimulationEvent) -> None:
        try:
            from src.observability.live.event_publisher import LiveEventPublisher
            LiveEventPublisher.get_instance().publish(event)
        except Exception as e:
            logger.error(f"InProcessEventStreamAdapter isolated publish error: {e}")

    def publish_batch(self, events: List[SimulationEvent]) -> None:
        for event in events:
            self.publish(event)

    def health(self) -> Dict[str, Any]:
        try:
            from src.observability.live.event_publisher import LiveEventPublisher
            pub = LiveEventPublisher.get_instance()
            return {
                "status": "healthy",
                "backend": "in_process",
                "total_published": pub.total_published,
                "total_dropped": pub.total_dropped,
                "active_subscribers": len(pub.subscribers)
            }
        except Exception as e:
            return {
                "status": "degraded",
                "backend": "in_process",
                "error": str(e)
            }

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


class RedisStreamAdapter(EventStreamAdapter):
    """
    Adapter that publishes events directly to an external Redis Stream (xadd).
    Features high-resilience safety, allowing the simulation to proceed normally
    without crashing if the Redis server is unreachable or the dependency is missing.
    """
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        stream_name: str = "simulation:events",
        max_queue_size: int = 1000,
        **kwargs: Any
    ) -> None:
        self.redis_url = redis_url
        self.stream_name = stream_name
        self.max_queue_size = max_queue_size
        self.client = None
        self._connected = False
        self.dropped_count = 0
        self.published_count = 0
        self.last_error: Optional[str] = None

        try:
            import redis
            self.client = redis.from_url(
                self.redis_url,
                socket_connect_timeout=1.0,
                decode_responses=True
            )
            # Safe connection ping verification
            self.client.ping()
            self._connected = True
        except ImportError:
            self.last_error = "redis package not installed"
            logger.warning("redis library missing. RedisStreamAdapter running in degraded mode.")
        except Exception as e:
            self.last_error = f"Connection failed: {e}"
            logger.warning(f"Redis offline or unreachable: {e}. RedisStreamAdapter running in degraded mode.")

    def publish(self, event: SimulationEvent) -> None:
        if not self._connected or self.client is None:
            self.dropped_count += 1
            return

        try:
            payload = {
                "event_type": event.event_type,
                "event_category": event.event_category,
                "severity": event.severity,
                "tick": str(event.tick),
                "message": event.message,
                "payload": event.model_dump_json()
            }
            # Limit the stream size (approximate capping)
            self.client.xadd(self.stream_name, payload, maxlen=self.max_queue_size, approximate=True)
            self.published_count += 1
            self.last_error = None
        except Exception as e:
            self.dropped_count += 1
            self.last_error = f"Publish failed: {e}"
            logger.error(f"RedisStreamAdapter failed to publish event: {e}")

    def publish_batch(self, events: List[SimulationEvent]) -> None:
        for event in events:
            self.publish(event)

    def health(self) -> Dict[str, Any]:
        # Validate dynamic ping status
        if self.client and not self.last_error:
            try:
                self.client.ping()
                self._connected = True
            except Exception as e:
                self._connected = False
                self.last_error = f"Ping failed: {e}"

        return {
            "status": "healthy" if self._connected else "degraded",
            "backend": "redis",
            "connected": self._connected,
            "published_events": self.published_count,
            "dropped_events": self.dropped_count,
            "last_error": self.last_error
        }

    def flush(self) -> None:
        pass

    def close(self) -> None:
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
            self._connected = False
