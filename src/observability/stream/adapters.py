from __future__ import annotations
import json
import logging
import collections
import threading
import time
from datetime import datetime, timezone
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
    Uses an internal thread-safe queue and a background daemon publisher thread
    to ensure non-blocking execution of the simulation tick loop.
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
        self.last_success_at: Optional[str] = None
        self.backpressure_active = False

        # Thread-safe queue
        self._queue = collections.deque()
        self._queue_lock = threading.Lock()
        self._queue_cond = threading.Condition(self._queue_lock)

        self._running = True
        self._worker_thread = None

        # Initial connect check (safe)
        self._connect()

        # Start worker thread
        self._worker_thread = threading.Thread(
            target=self._publish_worker,
            name="RedisStreamPublisherWorker",
            daemon=True
        )
        self._worker_thread.start()

    def _connect(self) -> None:
        try:
            import redis
            self.client = redis.from_url(
                self.redis_url,
                socket_connect_timeout=1.0,
                socket_timeout=1.0,
                decode_responses=True
            )
            # Safe connection ping verification
            self.client.ping()
            self._connected = True
            self.last_success_at = datetime.now(timezone.utc).isoformat()
            self.last_error = None
        except ImportError:
            self.last_error = "redis package not installed"
            self._connected = False
            logger.warning("redis library missing. RedisStreamAdapter running in degraded mode.")
        except Exception as e:
            self.last_error = f"Connection failed: {e}"
            self._connected = False
            logger.warning(f"Redis offline or unreachable: {e}. RedisStreamAdapter running in degraded mode.")

    def _publish_worker(self) -> None:
        while self._running:
            event = None
            with self._queue_lock:
                while len(self._queue) == 0 and self._running:
                    self._queue_cond.wait(timeout=0.1)
                if not self._running:
                    break
                if len(self._queue) > 0:
                    event = self._queue.popleft()

            if event:
                self._send_to_redis(event)

    def _send_to_redis(self, event: SimulationEvent) -> None:
        if not self._connected or self.client is None:
            self._connect()

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
            self.last_success_at = datetime.now(timezone.utc).isoformat()
            self.last_error = None
        except Exception as e:
            self.dropped_count += 1
            self.last_error = f"Publish failed: {e}"
            self._connected = False
            logger.error(f"RedisStreamAdapter failed to publish event: {e}")

    def publish(self, event: SimulationEvent) -> None:
        if self.max_queue_size <= 0:
            self.dropped_count += 1
            self.backpressure_active = True
            return

        with self._queue_lock:
            if len(self._queue) >= self.max_queue_size:
                # Queue is full, apply backpressure policy
                if event.severity in ("DEBUG", "INFO"):
                    self.dropped_count += 1
                    self.backpressure_active = True
                    return
                else:
                    # It's high severity (WARNING/ERROR/CRITICAL). Find a lower severity event to evict.
                    evicted = False
                    temp_list = list(self._queue)
                    for idx, item in enumerate(temp_list):
                        if item.severity in ("DEBUG", "INFO"):
                            del temp_list[idx]
                            evicted = True
                            self.dropped_count += 1
                            self.backpressure_active = True
                            break
                    if evicted:
                        self._queue = collections.deque(temp_list)
                    else:
                        # No low-severity event to evict, we must drop this high-severity event too
                        self.dropped_count += 1
                        self.backpressure_active = True
                        return

            self._queue.append(event)
            self._queue_cond.notify()

    def publish_batch(self, events: List[SimulationEvent]) -> None:
        for event in events:
            self.publish(event)

    def health(self) -> Dict[str, Any]:
        # Validate dynamic ping status
        if self._connected and self.client:
            try:
                self.client.ping()
            except Exception as e:
                self._connected = False
                self.last_error = f"Ping failed: {e}"

        with self._queue_lock:
            q_size = len(self._queue)

        return {
            "status": "healthy" if self._connected else "degraded",
            "backend": "redis",
            "connected": self._connected,
            "queue_size": q_size,
            "max_queue_size": self.max_queue_size,
            "published_events": self.published_count,
            "dropped_events": self.dropped_count,
            "backpressure_active": self.backpressure_active,
            "last_publish_error": self.last_error,
            "last_success_at": self.last_success_at
        }

    def flush(self) -> None:
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < 5.0:  # 5s max wait
            with self._queue_lock:
                if len(self._queue) == 0:
                    break
            time.sleep(0.01)

    def close(self) -> None:
        self._running = False
        with self._queue_lock:
            self._queue_cond.notify_all()
        if self._worker_thread:
            self._worker_thread.join(timeout=1.0)
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
            self._connected = False
