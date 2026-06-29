from __future__ import annotations
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from src.observability.queue import QueueDrainWorker, get_observability_queue

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
    """Delivers envelopes to QualityHub via a dedicated QueueDrainWorker on the global queue."""

    def __init__(self) -> None:
        self._worker: Optional[QueueDrainWorker] = None

    def start(self, hub: Any) -> None:
        queue = get_observability_queue()
        self._worker = QueueDrainWorker(
            queue=queue,
            quality_fn=hub.on_envelope,
        )
        self._worker.start()

    def stop(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self._worker = None

    def health(self) -> dict[str, Any]:
        if self._worker is None:
            return {"status": "STOPPED", "dropped_count": 0, "mode": "inprocess"}
        status = self._worker.health_status
        return {
            "status": status,
            "dropped_count": self._worker.failure_count,
            "mode": "inprocess",
        }


class BrokerQualityFeed(QualityFeedAdapter):
    """Stub for broker-mode feed — full implementation in TCK-20260628-SIMQ-E2-HUB-CORE."""

    def __init__(
        self,
        broker_url: str = "redis://localhost:6379",
        stream_name: str = "sim:events",
        consumer_group: str = "quality_scoring",
    ) -> None:
        self._broker_url = broker_url
        self._stream_name = stream_name
        self._consumer_group = consumer_group

    def start(self, hub: Any) -> None:
        raise NotImplementedError(
            "BrokerQualityFeed.start() is not implemented in E1-FOUNDATION. "
            "Full broker wiring is delivered in TCK-20260628-SIMQ-E2-HUB-CORE."
        )

    def stop(self) -> None:
        pass

    def health(self) -> dict[str, Any]:
        return {"status": "NOT_IMPLEMENTED", "mode": "broker"}


def build_feed_from_env() -> Optional[QualityFeedAdapter]:
    if os.environ.get("QUALITY_SCORING_DISABLED") == "1":
        return None
    mode = os.environ.get("QUALITY_FEED_MODE", "inprocess").lower()
    if mode == "inprocess":
        return InProcessQualityFeed()
    if mode == "broker":
        return BrokerQualityFeed(
            broker_url=os.environ.get("QUALITY_BROKER_URL", "redis://localhost:6379"),
            stream_name=os.environ.get("QUALITY_STREAM_NAME", "sim:events"),
            consumer_group=os.environ.get("QUALITY_CONSUMER_GROUP", "quality_scoring"),
        )
    raise ValueError(
        f"Unknown QUALITY_FEED_MODE: {mode!r}. Expected 'inprocess' or 'broker'."
    )
