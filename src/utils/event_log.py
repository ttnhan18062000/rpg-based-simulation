"""Thread-safe ring buffer for simulation events exposed via the API."""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimEvent:
    """A single simulation event for the API event feed."""

    tick: int
    category: str
    message: str


class EventLog:
    """Fixed-size ring buffer. Writers append; readers snapshot a slice.

    Thread-safe via a simple lock — writes are rare (once per tick batch)
    and reads are non-blocking copies.
    """

    __slots__ = ("_buffer", "_lock", "_max_size")

    def __init__(self, max_size: int = 500) -> None:
        self._buffer: deque[SimEvent] = deque(maxlen=max_size)
        self._lock = threading.Lock()
        self._max_size = max_size

    def append(self, event: SimEvent) -> None:
        with self._lock:
            self._buffer.append(event)

    def append_many(self, events: list[SimEvent]) -> None:
        with self._lock:
            self._buffer.extend(events)

    def since_tick(self, tick: int) -> list[SimEvent]:
        """Return all events with tick >= *tick*."""
        with self._lock:
            return [e for e in self._buffer if e.tick >= tick]

    def latest(self, count: int = 50) -> list[SimEvent]:
        """Return the *count* most recent events."""
        with self._lock:
            items = list(self._buffer)
        return items[-count:]

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()
