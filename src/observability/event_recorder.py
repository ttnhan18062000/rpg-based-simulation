from __future__ import annotations
import os
import json
import logging
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from src.observability.events import SimulationEvent
from src.config.optimization_profiles import SubsystemBudget, SubsystemPressureReport, DEFAULT_OBSERVABILITY_BUDGET

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {
    "DEBUG": 0,
    "INFO": 1,
    "WARNING": 2,
    "ERROR": 3,
    "CRITICAL": 4
}

_WARNING_SEVERITY = SEVERITY_ORDER["WARNING"]


class ObservabilityMode(str, Enum):
    NORMAL = "NORMAL"
    PRESSURE = "PRESSURE"
    DEGRADED = "DEGRADED"
    SURVIVAL = "SURVIVAL"


class ObservabilityController:
    """Pure-function mode advisor for the observability subsystem.

    Thresholds (queue fill ratio):
      PRESSURE  >= 0.70
      DEGRADED  >= 0.90
      SURVIVAL  >= 1.00 (queue at capacity)
    """

    PRESSURE_THRESHOLD: float = 0.70
    DEGRADED_THRESHOLD: float = 0.90
    SURVIVAL_THRESHOLD: float = 1.00

    def evaluate(
        self,
        queue_fill_ratio: float,
        event_rate_per_tick: float = 0.0,
    ) -> ObservabilityMode:
        if queue_fill_ratio >= self.SURVIVAL_THRESHOLD:
            return ObservabilityMode.SURVIVAL
        if queue_fill_ratio >= self.DEGRADED_THRESHOLD:
            return ObservabilityMode.DEGRADED
        if queue_fill_ratio >= self.PRESSURE_THRESHOLD:
            return ObservabilityMode.PRESSURE
        return ObservabilityMode.NORMAL

class EventRecorder:
    """Manages thread-safe, memory-bounded SimulationEvent recording and JSONL persistence."""

    _FLUSH_INTERVAL: int = 50

    def __init__(
        self,
        run_dir: Optional[str] = None,
        max_events: int = 5000,
        enabled: bool = True,
        budget: SubsystemBudget | None = None,
        quality_fn: Optional[Callable] = None,
    ) -> None:
        self.enabled = enabled
        self.max_events = max_events
        self.run_dir = run_dir
        self.events: List[SimulationEvent] = []
        self.dropped_event_count = 0
        self.event_count_by_type: Dict[str, int] = {}
        self._file_handle = None
        self.filepath = None
        self._pending_envelope_writes: int = 0
        # Subsystem budget for advisory pressure reporting (INFRA-194).
        # Independent of max_events — budget.max_queue_items is checked against
        # the queue size, not the in-memory buffer.
        self._subsystem_budget: SubsystemBudget = budget or DEFAULT_OBSERVABILITY_BUDGET

        # Dynamic mode controller (OBS-BACKPRESSURE)
        self._obs_controller = ObservabilityController()
        self._obs_mode: ObservabilityMode = ObservabilityMode.NORMAL
        self._press_sample_rate: int = 5
        self._press_event_counter: int = 0
        self._survival_event_counts: Dict[str, int] = {}
        self._events_dropped_by_mode: int = 0

        if self.enabled and self.run_dir:
            try:
                os.makedirs(self.run_dir, exist_ok=True)
                self.filepath = os.path.join(self.run_dir, "simulation_events.jsonl")
                self._file_handle = open(self.filepath, "a", encoding="utf-8")
            except Exception as e:
                logger.error(f"Failed to open simulation_events.jsonl: {e}")

        # Initialize Phase 21 non-blocking queue and async drain worker
        from src.observability.queue import BoundedObservabilityQueue, QueueDrainWorker
        from src.observability.events import ObservabilityEventEnvelope
        
        self.queue = BoundedObservabilityQueue(max_size=self.max_events)
        self._worker = QueueDrainWorker(
            queue=self.queue,
            file_write_fn=self._write_envelope_to_file,
            stream_publish_fn=self._publish_envelope_to_stream,
            quality_fn=quality_fn,
        )
        if self.enabled:
            self._worker.start()

    def _write_envelope_to_file(self, envelope: ObservabilityEventEnvelope) -> None:
        if self._file_handle:
            # Reconstruct compact serialized JSON from envelope
            import json
            data = {
                "event_id": envelope.event_id,
                "run_id": envelope.run_id,
                "tick": envelope.tick,
                "entity_id": envelope.entity_id,
                "event_type": envelope.event_type,
                "event_category": envelope.event_category,
                "severity": envelope.severity,
                "source_system": envelope.source_system,
                "message": envelope.message,
                "payload": envelope.payload,
                "related_entity_ids": list(envelope.related_entity_ids)
            }
            self._file_handle.write(json.dumps(data) + "\n")
            self._pending_envelope_writes += 1
            if self._pending_envelope_writes >= self._FLUSH_INTERVAL:
                self._file_handle.flush()
                self._pending_envelope_writes = 0

    def _publish_envelope_to_stream(self, envelope: ObservabilityEventEnvelope) -> None:
        try:
            from src.observability.stream.factory import get_event_stream_adapter
            # EventStreamAdapter requires SimulationEvent, convert back or publish
            # We reconstruct a mock or original SimulationEvent object for compatibility
            event = SimulationEvent(
                event_id=envelope.event_id,
                run_id=envelope.run_id,
                tick=envelope.tick,
                entity_id=envelope.entity_id,
                event_type=envelope.event_type,
                event_category=envelope.event_category,
                severity=envelope.severity,
                source_system=envelope.source_system,
                message=envelope.message,
                payload=dict(envelope.payload),
                related_entity_ids=list(envelope.related_entity_ids)
            )
            get_event_stream_adapter().publish(event)
        except Exception as e:
            logger.error(f"EventStreamAdapter error isolated: {e}")

    def record(self, event: SimulationEvent) -> None:
        """Records a single SimulationEvent, enforcing bounds and overflow policies."""
        if not self.enabled:
            return

        ev_type = event.event_type
        self.event_count_by_type[ev_type] = self.event_count_by_type.get(ev_type, 0) + 1

        # Evaluate observability mode from current queue fill ratio.
        max_q = self.queue.max_size
        fill = self.queue.get_size() / max_q if max_q > 0 else 0.0
        new_mode = self._obs_controller.evaluate(fill)
        if new_mode is not self._obs_mode:
            logger.info(
                "ObservabilityMode transition: %s -> %s (fill=%.2f)",
                self._obs_mode.value, new_mode.value, fill,
            )
            self._obs_mode = new_mode

        # SURVIVAL: counter-only path — no queue, no file, no buffer append.
        if self._obs_mode is ObservabilityMode.SURVIVAL:
            self._survival_event_counts[ev_type] = self._survival_event_counts.get(ev_type, 0) + 1
            self._events_dropped_by_mode += 1
            return

        severity_val = SEVERITY_ORDER.get(event.severity, 1)

        # DEGRADED: drop INFO/DEBUG events entirely; WARNING+ pass through.
        if self._obs_mode is ObservabilityMode.DEGRADED and severity_val < _WARNING_SEVERITY:
            self._events_dropped_by_mode += 1
            return

        # PRESSURE: sample INFO/DEBUG events at 1-in-N; WARNING+ always pass.
        if self._obs_mode is ObservabilityMode.PRESSURE and severity_val < _WARNING_SEVERITY:
            self._press_event_counter += 1
            if self._press_event_counter % self._press_sample_rate != 0:
                self._events_dropped_by_mode += 1
                return

        # NORMAL or passed mode filter — apply capacity management then record.
        # Capacity management for in-memory buffer
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

        # Push to the non-blocking observability queue
        from src.observability.events import ObservabilityEventEnvelope
        envelope = ObservabilityEventEnvelope.from_simulation_event(event)
        
        # Pushing into BoundedObservabilityQueue is thread-safe and non-blocking
        self.queue.try_push(envelope)

    def pressure_report(self) -> SubsystemPressureReport:
        """
        Advisory pressure snapshot for the observability subsystem (INFRA-194).

        Non-blocking and read-only.  Checks the current queue occupancy against
        max_queue_items.  This is independent of max_events (in-memory buffer).

        Returns:
            WARN  when queue occupancy >= 80% of max_queue_items.
            DEGRADED when queue occupancy >= 100% of max_queue_items.
            OK    otherwise, or when budget.max_queue_items is None (unlimited).
        """
        current = self.queue.get_size()
        max_q = self._subsystem_budget.max_queue_items
        if max_q is None:
            return SubsystemPressureReport(
                subsystem="observability",
                current_usage=float(current),
                budget=None,
                pressure_state="OK",
                degradation_action=None,
            )
        cap = max(max_q, 1)  # guard against zero-division
        pct = current / cap
        if pct < 0.8:
            state, action = "OK", None
        elif pct < 1.0:
            state, action = "WARN", "increase_sampling_interval"
        else:
            state, action = "DEGRADED", "drop_low_priority_events"
        return SubsystemPressureReport(
            subsystem="observability",
            current_usage=float(current),
            budget=float(max_q),
            pressure_state=state,
            degradation_action=action,
        )

    def observability_status(self) -> Dict[str, Any]:
        """Return current dynamic mode state (OBS-BACKPRESSURE)."""
        max_q = self.queue.max_size
        fill = self.queue.get_size() / max_q if max_q > 0 else 0.0
        return {
            "mode": self._obs_mode.value,
            "queue_fill_ratio": fill,
            "events_dropped": self._events_dropped_by_mode,
            "survival_counts": dict(self._survival_event_counts),
        }

    def reset_mode(self) -> None:
        """Reset dynamic mode to NORMAL and clear mode-related counters. Test-only."""
        self._obs_mode = ObservabilityMode.NORMAL
        self._press_event_counter = 0
        self._survival_event_counts.clear()
        self._events_dropped_by_mode = 0

    def get_stats(self) -> Dict[str, Any]:
        """Returns diagnostic statistics of the recorder."""
        return {
            "total_events_in_memory": len(self.events),
            "dropped_events_count": self.dropped_event_count,
            "event_count_by_type": self.event_count_by_type.copy(),
            "filepath": self.filepath,
            "queue_size": self.queue.get_size(),
            "queue_dropped_count": self.queue.dropped_count,
            "worker_health": self._worker.health_status,
            "worker_failures": self._worker.failure_count
        }

    def clear(self) -> None:
        """Clears the in-memory buffer and queue."""
        self.events.clear()
        self.dropped_event_count = 0
        self.event_count_by_type.clear()
        self.queue.drain()

    def shutdown(self) -> None:
        """Shuts down and flushes any active file descriptors."""
        # 1. Stop background drain worker
        if self._worker:
            self._worker.stop()
            
        # 2. Final synchronous flush of any remaining queue elements
        try:
            remaining = self.queue.drain()
            for env in remaining:
                self._write_envelope_to_file(env)
                self._publish_envelope_to_stream(env)
        except Exception as e:
            logger.error(f"Error during final queue flush on shutdown: {e}")

        # 3. Close file handle
        if self._file_handle:
            try:
                self._file_handle.flush()
                self._file_handle.close()
            except Exception as e:
                logger.error(f"Error closing simulation_events.jsonl handle: {e}")
            self._file_handle = None

