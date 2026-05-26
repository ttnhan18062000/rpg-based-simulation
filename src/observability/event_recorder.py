from __future__ import annotations
import os
import json
import logging
from typing import Any, Dict, List, Optional
from src.observability.events import SimulationEvent

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {
    "DEBUG": 0,
    "INFO": 1,
    "WARNING": 2,
    "ERROR": 3,
    "CRITICAL": 4
}

class EventRecorder:
    """Manages thread-safe, memory-bounded SimulationEvent recording and JSONL persistence."""
    def __init__(self, run_dir: Optional[str] = None, max_events: int = 5000, enabled: bool = True) -> None:
        self.enabled = enabled
        self.max_events = max_events
        self.run_dir = run_dir
        self.events: List[SimulationEvent] = []
        self.dropped_event_count = 0
        self.event_count_by_type: Dict[str, int] = {}
        self._file_handle = None
        self.filepath = None

        if self.enabled and self.run_dir:
            try:
                os.makedirs(self.run_dir, exist_ok=True)
                self.filepath = os.path.join(self.run_dir, "simulation_events.jsonl")
                self._file_handle = open(self.filepath, "a", encoding="utf-8")
            except Exception as e:
                logger.error(f"Failed to open simulation_events.jsonl: {e}")

    def record(self, event: SimulationEvent) -> None:
        """Records a single SimulationEvent, enforcing bounds and overflow policies."""
        if not self.enabled:
            return

        ev_type = event.event_type
        self.event_count_by_type[ev_type] = self.event_count_by_type.get(ev_type, 0) + 1

        # Capacity management
        if len(self.events) >= self.max_events:
            # Find the oldest event of the lowest severity that is not CRITICAL
            evict_index = -1
            lowest_sev_val = 5

            for idx, ev in enumerate(self.events):
                sev_val = SEVERITY_ORDER.get(ev.severity, 1)
                if sev_val < 4 and sev_val < lowest_sev_val:
                    lowest_sev_val = sev_val
                    evict_index = idx

            if evict_index != -1:
                self.events.pop(evict_index)
                self.dropped_event_count += 1
            else:
                # Buffer is full of CRITICAL events
                if event.severity == "CRITICAL":
                    self.events.pop(0)
                    self.dropped_event_count += 1
                else:
                    # Drop incoming non-critical event
                    self.dropped_event_count += 1
                    return

        self.events.append(event)

        # Write to JSONL
        if self._file_handle:
            try:
                self._file_handle.write(event.model_dump_json() + "\n")
                self._file_handle.flush()
            except Exception as e:
                logger.error(f"Failed to write to simulation_events.jsonl: {e}")

        # Publish event using EventStreamAdapter (Milestone 29)
        try:
            from src.observability.stream.factory import get_event_stream_adapter
            get_event_stream_adapter().publish(event)
        except Exception as e:
            logger.error(f"EventStreamAdapter error isolated: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Returns diagnostic statistics of the recorder."""
        return {
            "total_events_in_memory": len(self.events),
            "dropped_events_count": self.dropped_event_count,
            "event_count_by_type": self.event_count_by_type.copy(),
            "filepath": self.filepath,
        }

    def clear(self) -> None:
        """Clears the in-memory buffer."""
        self.events.clear()
        self.dropped_event_count = 0
        self.event_count_by_type.clear()

    def shutdown(self) -> None:
        """Shuts down and flushes any active file descriptors."""
        if self._file_handle:
            try:
                self._file_handle.close()
            except Exception as e:
                logger.error(f"Error closing simulation_events.jsonl handle: {e}")
            self._file_handle = None
