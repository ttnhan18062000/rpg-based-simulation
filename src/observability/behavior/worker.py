"""
BehaviorWorker — Phase 22 async behavior normalization worker.

Processes raw events into behavior events either:
1. Post-run: reading from a simulation_events.jsonl file.
2. In-process: draining from a BoundedObservabilityQueue.

Key design rules (from Phase 22 spec):
- Worker failure does not affect the simulation engine.
- Worker can be disabled by flag.
- Worker has bounded memory.
- Worker records lag/backlog.
- Output: behavior_events.jsonl artifact.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Callable, Iterator, Optional

from src.observability.behavior.behavior_event import BehaviorEvent
from src.observability.behavior.normalizer import BehaviorEventNormalizer
from src.observability.behavior.normalization_context import BehaviorNormalizationContext
from src.observability.events import SimulationEvent, ObservabilityEventEnvelope
from src.observability.queue import BoundedObservabilityQueue

log = logging.getLogger(__name__)


class WorkerHealth:
    """Thread-safe health tracker for BehaviorWorker."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    STOPPED = "STOPPED"

    def __init__(self) -> None:
        self._status = self.HEALTHY
        self._lock = threading.Lock()
        self.failure_count = 0
        self.processed_count = 0
        self.skipped_count = 0

    @property
    def status(self) -> str:
        with self._lock:
            return self._status

    def record_failure(self) -> None:
        with self._lock:
            self.failure_count += 1
            self._status = self.DEGRADED

    def record_processed(self, n: int = 1) -> None:
        with self._lock:
            self.processed_count += n

    def record_skipped(self, n: int = 1) -> None:
        with self._lock:
            self.skipped_count += n

    def mark_stopped(self) -> None:
        with self._lock:
            self._status = self.STOPPED


class BehaviorWorker:
    """
    Async behavior normalization worker.

    Supports two operation modes:
    - Post-run JSONL mode: process a simulation_events.jsonl file.
    - In-process queue mode: continuously drain a BoundedObservabilityQueue.

    Neither mode should be called from within the simulation tick loop.
    """

    def __init__(
        self,
        normalizer: Optional[BehaviorEventNormalizer] = None,
        context: Optional[BehaviorNormalizationContext] = None,
        output_fn: Optional[Callable[[BehaviorEvent], None]] = None,
        max_events_per_batch: int = 500,
        interval_sec: float = 0.05,
    ) -> None:
        self._normalizer = normalizer or BehaviorEventNormalizer()
        self._context = context or BehaviorNormalizationContext.minimal("unknown_run")
        self._output_fn = output_fn
        self._max_events_per_batch = max_events_per_batch
        self._interval_sec = interval_sec

        self.health = WorkerHealth()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Post-run JSONL mode
    # ------------------------------------------------------------------

    def process_jsonl(
        self,
        jsonl_path: Path,
        output_path: Optional[Path] = None,
    ) -> tuple[BehaviorEvent, ...]:
        """
        Process a simulation_events.jsonl file post-run.

        Returns all produced BehaviorEvents.
        If output_path is provided, also writes behavior_events.jsonl.
        """
        behavior_events: list[BehaviorEvent] = []
        writer = None

        try:
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                writer = open(output_path, "w", encoding="utf-8")

            for raw_event in self._read_jsonl_events(jsonl_path):
                batch = self._normalizer.normalize_event(raw_event, self._context)
                behavior_events.extend(batch)
                self.health.record_processed(len(batch))

                if writer:
                    for be in batch:
                        writer.write(json.dumps(be.to_dict()) + "\n")

                if self._output_fn:
                    for be in batch:
                        self._output_fn(be)

        except Exception:
            self.health.record_failure()
            log.error("BehaviorWorker: error processing JSONL %s", jsonl_path, exc_info=True)
        finally:
            if writer:
                writer.close()

        return tuple(behavior_events)

    def _read_jsonl_events(
        self, jsonl_path: Path
    ) -> Iterator[SimulationEvent | ObservabilityEventEnvelope]:
        """
        Yield SimulationEvent objects read from a JSONL file.

        Lines that fail to parse are skipped; the worker logs a warning
        but continues — partial artifact tolerance is required.
        """
        try:
            with open(jsonl_path, "r", encoding="utf-8") as fh:
                for line_no, line in enumerate(fh, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        # Try to reconstruct a SimulationEvent
                        event = _parse_simulation_event(data)
                        if event is not None:
                            yield event
                        else:
                            self.health.record_skipped()
                    except Exception:
                        log.warning(
                            "BehaviorWorker: skipping unparseable line %d in %s",
                            line_no,
                            jsonl_path,
                        )
                        self.health.record_skipped()
        except FileNotFoundError:
            log.warning("BehaviorWorker: JSONL file not found: %s", jsonl_path)
        except Exception:
            self.health.record_failure()
            log.error("BehaviorWorker: error opening %s", jsonl_path, exc_info=True)

    # ------------------------------------------------------------------
    # In-process queue drain mode (sidecar)
    # ------------------------------------------------------------------

    def start_queue_worker(self, queue: BoundedObservabilityQueue) -> None:
        """
        Start an async daemon thread to drain events from a BoundedObservabilityQueue.

        Worker failure does not affect the engine.
        """
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._drain_loop,
            args=(queue,),
            daemon=True,
            name="behavior-normalization-worker",
        )
        self._thread.start()

    def stop_queue_worker(self, timeout_sec: float = 2.0) -> None:
        """Stop the async drain worker gracefully."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=timeout_sec)
            self._thread = None
        self.health.mark_stopped()

    def _drain_loop(self, queue: BoundedObservabilityQueue) -> None:
        """Internal loop for queue drain mode."""
        while self._running:
            try:
                envelopes = queue.drain()
                if envelopes:
                    batch = self._normalizer.normalize_batch(envelopes, self._context)
                    self.health.record_processed(len(batch))
                    if self._output_fn:
                        for be in batch:
                            try:
                                self._output_fn(be)
                            except Exception:
                                self.health.record_failure()
                time.sleep(self._interval_sec)
            except Exception:
                self.health.record_failure()
                log.error("BehaviorWorker: drain loop error", exc_info=True)
                time.sleep(self._interval_sec)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def health_status(self) -> str:
        return self.health.status


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_simulation_event(
    data: dict,
) -> Optional[SimulationEvent | ObservabilityEventEnvelope]:
    """
    Attempt to parse a dict as a SimulationEvent.

    Returns None if the data does not look like a known event type.
    Prefers SimulationEvent (Pydantic) but falls back to a minimal
    ObservabilityEventEnvelope if only envelope fields are available.
    """
    try:
        # Required fields for any simulation event
        if "event_type" not in data or "tick" not in data:
            return None

        # Attempt full SimulationEvent parse
        return SimulationEvent(**data)
    except Exception:
        pass

    # Fall back to envelope if it has the minimal required fields
    try:
        if all(
            k in data
            for k in ("event_id", "run_id", "tick", "event_type", "event_category", "severity", "source_system", "message")
        ):
            return ObservabilityEventEnvelope(
                event_id=data["event_id"],
                run_id=data["run_id"],
                tick=data["tick"],
                entity_id=data.get("entity_id"),
                event_type=data["event_type"],
                event_category=data["event_category"],
                severity=data["severity"],
                source_system=data["source_system"],
                message=data["message"],
                payload=data.get("payload") or {},
                related_entity_ids=tuple(data.get("related_entity_ids") or []),
            )
    except Exception:
        pass

    return None
