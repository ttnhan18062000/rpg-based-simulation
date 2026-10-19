from __future__ import annotations
import os
import json
import logging
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from src.core.state import AuthoritativeState
from src.observability.config import ObservabilityMode as _RunObservabilityMode
from src.observability.event_extractor import EventExtractor
from src.observability.event_shapers import FactionShaper, ProgressionShaper, SocialShaper, StrategyShaper
from src.observability.events import SimulationEvent
from src.observability.death_ledger import DeathLedger
from src.observability.run_ledger import RunLedger
from src.observability.starvation_record import StarvationRecorder
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

    # Channels that close a run with one last event (registered once at import by the channel's owner; each is given this recorder's per-type event counts and returns None when this recorder saw nothing of its channel).
    closing_event_sources: List[Callable[[Dict[str, int]], Optional[SimulationEvent]]] = []

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
        self.buffer_evicted_count = 0  # in-memory buffer evictions only (never a loss to the file); mode drops and queue drops have their own counters
        self._sev_counts: Dict[str, int] = {}
        self.event_count_by_type: Dict[str, int] = {}
        self._file_handle = None
        self.filepath = None
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
            flush_fn=self._flush_file,
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

    def _flush_file(self) -> None:
        """Flush the file handle. Called once per non-empty QueueDrainWorker drain cycle
        (not per-record) — batches disk I/O within a cycle's writes while keeping newly
        drained records visible on the next cycle (~_worker.interval_sec later), rather than
        deferring visibility until an arbitrary record-count threshold or shutdown."""
        if self._file_handle:
            self._file_handle.flush()

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

        # NORMAL or passed mode filter: bound the in-memory buffer, then ALWAYS push to the queue (file, stream, SimQ). The buffer is a diagnostic
        # view; nothing that happens to it may stop an event that passed the mode filter from reaching the file.
        self._bound_buffer(event)

        # Push to the non-blocking observability queue
        from src.observability.events import ObservabilityEventEnvelope
        envelope = ObservabilityEventEnvelope.from_simulation_event(event)
        
        # Pushing into BoundedObservabilityQueue is thread-safe and non-blocking
        self.queue.try_push(envelope)

    def _bound_buffer(self, event: SimulationEvent) -> None:
        """Keep the in-memory ``events`` buffer within ``max_events`` and store ``event`` in it.

        The buffer is a diagnostic view only: whatever happens here, the caller still pushes the event to the queue (file, stream, SimQ). When the
        buffer is full the oldest event of the lowest severity below CRITICAL is evicted; when it holds only CRITICAL events an incoming CRITICAL
        evicts the oldest, and an incoming non-critical event is simply not stored. Each eviction (or not-stored event) is counted in
        ``buffer_evicted_count`` (``dropped_event_count`` is kept equal for existing readers); it is never a loss to the file.
        """
        if len(self.events) >= self.max_events:
            evict_index = self._eviction_index()
            if evict_index != -1:
                self._forget(self.events.pop(evict_index))
            elif event.severity == "CRITICAL":
                self._forget(self.events.pop(0))
            else:
                self._count_buffer_eviction()
                return
            self._count_buffer_eviction()
        self.events.append(event)
        self._sev_counts[event.severity] = self._sev_counts.get(event.severity, 0) + 1

    def _count_buffer_eviction(self) -> None:
        self.buffer_evicted_count += 1
        self.dropped_event_count += 1

    def _forget(self, event: SimulationEvent) -> None:
        self._sev_counts[event.severity] = self._sev_counts.get(event.severity, 1) - 1

    def _eviction_index(self) -> int:
        """Index of the oldest event of the lowest severity below CRITICAL, or -1 when the buffer holds only CRITICAL events.

        Per-severity counts say which severity that is, so the scan stops at its first (oldest) event instead of reading the whole buffer on every
        record(). The counts are rebuilt when they no longer add up to the buffer (something replaced ``events`` from outside).
        """
        if sum(self._sev_counts.values()) != len(self.events):
            self._sev_counts = {}
            for ev in self.events:
                self._sev_counts[ev.severity] = self._sev_counts.get(ev.severity, 0) + 1
        present = [sev for sev in self._sev_counts if self._sev_counts[sev] > 0 and SEVERITY_ORDER.get(sev, 1) < 4]
        if not present:
            return -1
        lowest = min(present, key=lambda sev: SEVERITY_ORDER.get(sev, 1))
        lowest_val = SEVERITY_ORDER.get(lowest, 1)
        for idx, ev in enumerate(self.events):
            if SEVERITY_ORDER.get(ev.severity, 1) == lowest_val:
                return idx
        return -1

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
            "buffer_evicted_count": self.buffer_evicted_count,
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
        self._sev_counts = {}
        self.dropped_event_count = 0
        self.buffer_evicted_count = 0
        self.event_count_by_type.clear()
        self.queue.drain()

    def shutdown(self) -> None:
        """Shuts down and flushes any active file descriptors."""
        # 0. Close any channel that writes a closing event (e.g. the starvation-record tally) while the queue still accepts events.
        for closing_event in EventRecorder.closing_event_sources:
            event = closing_event(self.event_count_by_type)
            if event is not None:
                self.record(event)

        # 1. Stop background drain worker. This blocks (joins, timeout=1.0s) until the
        # worker's thread has exited, so no further _run() loop iteration can race the
        # final drain below or QualityPersistence.shutdown() in Kernel.shutdown() (which
        # must run strictly after this method returns — see
        # TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD).
        if self._worker:
            self._worker.stop()

        # 2. Final synchronous drain of any remaining queue elements — events pushed
        # after the worker's last loop iteration but before .stop() took effect. Mirrors
        # QueueDrainWorker._run()'s per-envelope dispatch (file write, stream publish,
        # quality_fn) so nothing queued in this final window is silently dropped from
        # quality scoring/persistence either; each callback's exception is isolated so a
        # bad quality_fn record can't skip file/stream writes for the rest.
        try:
            remaining = self.queue.drain()
            quality_fn = self._worker.quality_fn if self._worker else None
            for env in remaining:
                self._write_envelope_to_file(env)
                self._publish_envelope_to_stream(env)
                if quality_fn:
                    try:
                        quality_fn(env)
                    except Exception as e:
                        logger.error(f"Error calling quality_fn during final shutdown drain: {e}")
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


EventRecorder.closing_event_sources.extend([StarvationRecorder.closing_event, RunLedger.closing_event, DeathLedger.closing_event])


def reset_run_state(strategic_cadence: int, escalated_hunger: float, cadence_gate: Callable[[int, Optional[int], int], bool], live: bool = True,
                    starving_line: float = float("inf")) -> None:
    """Clear every run-scoped observability cache at run start. The three arguments are what the kernel (engine side) tells the starvation-death
    recorder: the profile's strategic re-decision period, the hunger the pull escalates at, and the cadence's per-subject stagger (``live`` False when the profile has no observability budget)."""
    EventExtractor.reset_run_state()
    StarvationRecorder.reset_run_state()
    StarvationRecorder.configure(strategic_cadence, escalated_hunger, cadence_gate, live)
    RunLedger.reset_run_state()
    RunLedger.configure(live)
    DeathLedger.reset_run_state()
    DeathLedger.configure(starving_line, live)
    StrategyShaper.reset_run_state()
    ProgressionShaper.reset_run_state()
    SocialShaper.reset_run_state()
    FactionShaper.reset_run_state()


def extract_events(prior: AuthoritativeState, current: AuthoritativeState, update: Any, mode: _RunObservabilityMode = _RunObservabilityMode.LIGHT) -> List[SimulationEvent]:
    """One tick's curated events plus the starvation-death record channel and the run ledger (silent when observability is OFF: no header, so the channel reads as not live)."""
    events = EventExtractor.extract(prior, current, update, mode)
    if mode != _RunObservabilityMode.OFF:
        events = events + StarvationRecorder.observe(prior, current, update) + RunLedger.observe(prior, current, update) + DeathLedger.observe(prior, current, update)
    return events
