from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from src.observability.events import SimulationEvent


class EventStreamAdapter(ABC):
    """
    Abstract base class representing the event stream adapter interface.
    Decouples the core engine and EventRecorder from dynamic streaming transport layers.
    """

    @abstractmethod
    def publish(self, event: SimulationEvent) -> None:
        """Publishes a single event to the stream backend."""
        pass

    @abstractmethod
    def publish_batch(self, events: List[SimulationEvent]) -> None:
        """Publishes a batch of events to the stream backend."""
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Returns health diagnostics, connection status, and backpressure metrics."""
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flushes any buffered events to the stream backend."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Closes the stream adapter and cleans up active resources."""
        pass
