from __future__ import annotations
import logging
import threading
from collections import deque
from typing import Any, Dict, List, Optional
from src.observability.events import SimulationEvent
from src.observability.config import ObservabilityMode

logger = logging.getLogger(__name__)

MODE_RETENTION_LIMITS = {
    ObservabilityMode.OFF: 0,
    ObservabilityMode.LIGHT: 20,
    ObservabilityMode.DEBUG: 500,
    ObservabilityMode.CERTIFICATION: 200,
    ObservabilityMode.LONG_RUN: 100
}

class EntityTimelineStore:
    """Thread-safe, external, mode-bounded repository of entity simulation event timelines."""
    def __init__(self, mode: ObservabilityMode = ObservabilityMode.LIGHT) -> None:
        self.mode = mode
        self.max_len = MODE_RETENTION_LIMITS.get(mode, 20)
        self._timelines: Dict[int, deque[SimulationEvent]] = {}
        self._lock = threading.Lock()
        self.dropped_event_count = 0

    def record(self, event: SimulationEvent) -> None:
        """Indexes a SimulationEvent to the primary and related entity timelines."""
        if self.mode == ObservabilityMode.OFF or self.max_len <= 0:
            return

        with self._lock:
            # Record under main entity_id
            if event.entity_id is not None:
                self._append_to_timeline(event.entity_id, event)

            # Record under related entity_ids
            if event.related_entity_ids:
                for reid in event.related_entity_ids:
                    if reid != event.entity_id:
                        self._append_to_timeline(reid, event)

    def _append_to_timeline(self, entity_id: int, event: SimulationEvent) -> None:
        """Internal helper to append event, creating deque if needed."""
        if entity_id not in self._timelines:
            self._timelines[entity_id] = deque(maxlen=self.max_len)

        timeline = self._timelines[entity_id]
        if len(timeline) >= self.max_len:
            self.dropped_event_count += 1
        timeline.append(event)

    def get_entity_timeline(self, entity_id: int) -> List[SimulationEvent]:
        """Retrieves a copy of the timeline of the specified entity."""
        with self._lock:
            if entity_id not in self._timelines:
                return []
            return list(self._timelines[entity_id])

    def get_flagged_timelines(self, flagged_entity_ids: List[int]) -> Dict[int, List[Dict[str, Any]]]:
        """Exports timelines for specified/flagged entity IDs for report generation."""
        export = {}
        with self._lock:
            for eid in flagged_entity_ids:
                if eid in self._timelines:
                    export[eid] = [ev.model_dump() for ev in self._timelines[eid]]
        return export

    def record_to_entity(self, event: SimulationEvent, entity: Any) -> None:
        """Appends event to the entity's own timeline deque if present.

        This is the authorised routing point for the legacy entity.timeline
        compatibility path — callers must not append to entity.timeline directly.
        """
        if hasattr(entity, "timeline") and entity.timeline is not None:
            entity.timeline.append(event)

    def clear(self) -> None:
        """Clears all timelines and counters."""
        with self._lock:
            self._timelines.clear()
            self.dropped_event_count = 0
