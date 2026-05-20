from __future__ import annotations
import logging
import collections
import threading
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SubscriptionFilter(BaseModel):
    model_config = {"extra": "forbid"}

    event_type: Optional[str] = None
    event_category: Optional[str] = None
    severity_min: Optional[str] = None
    entity_id: Optional[int] = None
    region_id: Optional[str] = None
    quest_id: Optional[str] = None

    def matches(self, event: Any) -> bool:
        """Determines if the SimulationEvent matches the active filter criteria."""
        if self.event_type and event.event_type != self.event_type:
            return False
        if self.event_category and event.event_category != self.event_category:
            return False
        if self.severity_min:
            order = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
            req_val = order.get(self.severity_min.upper(), 0)
            ev_val = order.get(event.severity.upper(), 1)
            if ev_val < req_val:
                return False
        if self.entity_id is not None and getattr(event, "entity_id", None) != self.entity_id:
            return False
        if self.region_id and getattr(event, "region_id", None) != self.region_id:
            return False
        if self.quest_id and getattr(event, "quest_id", None) != self.quest_id:
            return False
        return True

class LiveEventSubscriber:
    """Thread-safe bounded event queue subscriber with backpressure policies."""
    def __init__(self, filter_obj: SubscriptionFilter, capacity: int = 500) -> None:
        self.filter = filter_obj
        self.capacity = capacity
        self.queue: collections.deque[Any] = collections.deque()
        self._lock = threading.Lock()
        self.dropped_count = 0
        self.disconnect_flag = False

    def push(self, event: Any) -> bool:
        """Pushes an event onto the subscriber's queue, applying backpressure logic."""
        with self._lock:
            if self.disconnect_flag:
                return False

            if len(self.queue) < self.capacity:
                self.queue.append(event)
                return True

            # Bounded capacity exceeded: apply backpressure policy.
            # Evict the oldest of the lowest severity among DEBUG/INFO first.
            order = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
            evict_idx = -1
            lowest_val = 5
            for idx, ev in enumerate(self.queue):
                sev_val = order.get(ev.severity.upper(), 1)
                if sev_val <= 1 and sev_val < lowest_val:
                    lowest_val = sev_val
                    evict_idx = idx

            if evict_idx != -1:
                lst = list(self.queue)
                lst.pop(evict_idx)
                self.queue = collections.deque(lst)
                self.queue.append(event)
                self.dropped_count += 1
                if self.dropped_count >= 50:
                    self.disconnect_flag = True
                return True

            # No low-severity events found. Evict the oldest event in the queue.
            self.queue.popleft()
            self.queue.append(event)
            self.dropped_count += 1

            # Disconnect subscriber if too slow (dropped count exceeds threshold)
            if self.dropped_count >= 50:
                self.disconnect_flag = True

            return True

    def get_events(self) -> List[Any]:
        """Consumes and returns all currently queued events."""
        with self._lock:
            events = list(self.queue)
            self.queue.clear()
            return events

class LiveEventPublisher:
    """In-process thread-safe event publishing broker."""
    _instance: Optional[LiveEventPublisher] = None
    _instance_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> LiveEventPublisher:
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Resets the singleton instance (useful for unit tests)."""
        with cls._instance_lock:
            cls._instance = None

    def __init__(self) -> None:
        self.subscribers: List[LiveEventSubscriber] = []
        self._lock = threading.Lock()
        self.enabled = True
        self.total_published = 0
        self.total_dropped = 0

    def register(self, subscriber: LiveEventSubscriber) -> None:
        with self._lock:
            if subscriber not in self.subscribers:
                self.subscribers.append(subscriber)

    def unregister(self, subscriber: LiveEventSubscriber) -> None:
        with self._lock:
            if subscriber in self.subscribers:
                self.subscribers.remove(subscriber)

    def publish(self, event: Any) -> None:
        """Publishes an event to matching subscribers."""
        if not self.enabled:
            return

        self.total_published += 1
        disconnected_subs = []

        with self._lock:
            for sub in self.subscribers:
                if sub.disconnect_flag:
                    disconnected_subs.append(sub)
                    continue

                try:
                    if sub.filter.matches(event):
                        sub.push(event)
                        if sub.disconnect_flag:
                            disconnected_subs.append(sub)
                except Exception as e:
                    logger.error(f"Error publishing event to subscriber: {e}")

            # Clean up disconnected subscribers
            for sub in disconnected_subs:
                if sub in self.subscribers:
                    self.subscribers.remove(sub)
                    self.total_dropped += sub.dropped_count
