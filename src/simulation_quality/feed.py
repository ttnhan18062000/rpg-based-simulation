from __future__ import annotations
import os
import threading
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional


if TYPE_CHECKING:
    pass


class QualityFeedMode(str, Enum):
    INPROCESS = "inprocess"
    BROKER = "broker"


class QualityFeedAdapter(ABC):
    @abstractmethod
    def start(self, hub: Any) -> None:
        """Begin delivering ObservabilityEventEnvelope instances to hub.on_envelope()."""

    @abstractmethod
    def stop(self) -> None:
        """Gracefully shut down the feed."""

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """Return status, lag, and dropped_count."""


class InProcessQualityFeed(QualityFeedAdapter):
    """Lifecycle manager for in-process quality scoring.

    quality_fn=hub.on_envelope is injected into EventRecorder's QueueDrainWorker at
    kernel init time (G1 fix). This class holds the hub reference for health/stop
    reporting only — it does not create a second QueueDrainWorker (G3 fix).
    """

    def __init__(self) -> None:
        self._hub: Optional[Any] = None

    def start(self, hub: Any) -> None:
        self._hub = hub

    def stop(self) -> None:
        self._hub = None

    def health(self) -> dict[str, Any]:
        if self._hub is None:
            return {"status": "STOPPED", "dropped_count": 0, "mode": "inprocess"}
        return {"status": "HEALTHY", "dropped_count": 0, "mode": "inprocess"}


class BrokerQualityFeed(QualityFeedAdapter):
    """Delivers envelopes to QualityHub via a RedisStreamConsumer in a background thread."""

    def __init__(
        self,
        broker_url: Optional[str] = None,
        stream_name: Optional[str] = None,
        consumer_group: str = "quality_scoring",
    ) -> None:
        from src.observability.config import ObservabilityConfig

        self._broker_url = broker_url if broker_url is not None else ObservabilityConfig.get_redis_url()
        self._stream_name = stream_name if stream_name is not None else ObservabilityConfig.get_stream_name()
        self._consumer_group = consumer_group
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._health_status: str = "STOPPED"
        self._consumer: Optional[Any] = None
        self.events_consumed_count: int = 0

    def start(self, hub: Any) -> None:
        from src.observability.events import ObservabilityEventEnvelope
        from src.observability.stream.consumer import RedisStreamConsumer

        consumer = RedisStreamConsumer(
            redis_url=self._broker_url,
            stream_name=self._stream_name,
            group_name=self._consumer_group,
        )
        if not consumer.connect():
            import logging
            logging.getLogger(__name__).warning(
                "BrokerQualityFeed: Redis unavailable at %s — quality scoring in broker mode disabled",
                self._broker_url,
            )
            self._health_status = "unavailable"
            return

        self._consumer = consumer
        self._running = True
        self._health_status = "HEALTHY"

        def _callback(sim_event: Any) -> None:
            envelope = ObservabilityEventEnvelope.from_simulation_event(sim_event)
            hub.on_envelope(envelope)
            self.events_consumed_count += 1

        def _consume_loop() -> None:
            while self._running:
                try:
                    consumer.read_and_process(_callback, block_ms=500)
                except Exception as exc:
                    import logging
                    logging.getLogger(__name__).warning("BrokerQualityFeed: consumer error: %s", exc)
                    self._health_status = "DEGRADED"

        self._thread = threading.Thread(target=_consume_loop, daemon=True, name="broker-quality-feed")
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._consumer is not None:
            self._consumer.close()
            self._consumer = None
        self._health_status = "STOPPED"

    def health(self) -> dict[str, Any]:
        return {"status": self._health_status, "mode": "broker"}


def build_feed_from_env() -> Optional[QualityFeedAdapter]:
    if os.environ.get("QUALITY_SCORING_DISABLED") == "1":
        return None
    mode = os.environ.get("QUALITY_FEED_MODE", "inprocess").lower()
    if mode == "inprocess":
        return InProcessQualityFeed()
    if mode == "broker":
        return BrokerQualityFeed(
            broker_url=os.environ.get("QUALITY_BROKER_URL"),
            stream_name=os.environ.get("QUALITY_STREAM_NAME"),
            consumer_group=os.environ.get("QUALITY_CONSUMER_GROUP", "quality_scoring"),
        )
    raise ValueError(
        f"Unknown QUALITY_FEED_MODE: {mode!r}. Expected 'inprocess' or 'broker'."
    )
