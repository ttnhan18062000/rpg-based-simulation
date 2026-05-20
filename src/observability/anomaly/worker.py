from __future__ import annotations
import os
import json
import uuid
import logging
import time
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import psutil

from src.observability.reporting.artifact_repository import RunArtifactRepository
from src.observability.anomaly.pipeline import AnalysisPipeline, AnalysisResult
from src.observability.events import SimulationEvent
from src.observability.anomaly.rules import (
    Anomaly,
    RollingEventWindow,
    LiveAnomalyRule,
    HardLawViolationLive,
    NavigationStuckLive,
    EventDropRateHigh,
    GovernorDegradedLive,
    CriticalEventObserved
)
from src.observability.live.event_publisher import LiveEventSubscriber, SubscriptionFilter, LiveEventPublisher
from src.observability.stream.consumer import RedisStreamConsumer

logger = logging.getLogger(__name__)


class WorkerStatus(BaseModel):
    """
    Tracks state and diagnostics of the standalone anomaly worker process.
    Provides visibility into processing throughput and heartbeat logs.
    """
    worker_id: str
    mode: str = "artifact"  # "artifact" or "stream"
    status: str = "PENDING"  # "PENDING" | "RUNNING" | "COMPLETED" | "FAILED" | "DEGRADED" | "STOPPED"
    current_run_id: Optional[str] = None
    processed_events: int = 0
    anomaly_count: int = 0
    last_heartbeat_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_error: Optional[str] = None
    last_event_tick: Optional[int] = None
    stream_lag: Optional[int] = None
    memory_estimate: Optional[float] = None


class ExternalAnomalyWorker:
    """
    Standalone process worker managing off-loop anomaly parsing and artifact auditing.
    Decouples computation-heavy diagnostics entirely from the core simulation loop.
    """
    def __init__(self, worker_id: Optional[str] = None, mode: str = "artifact") -> None:
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.mode = mode
        self.status_record = WorkerStatus(
            worker_id=self.worker_id,
            mode=self.mode,
            status="PENDING"
        )
        self.repo = RunArtifactRepository()

    def update_status(
        self,
        status: str,
        current_run_id: Optional[str] = None,
        processed_events: int = 0,
        anomaly_count: int = 0,
        last_error: Optional[str] = None
    ) -> None:
        """Updates worker state records and flushes a status file under data/runs/workers."""
        self.status_record.status = status
        self.status_record.current_run_id = current_run_id
        self.status_record.processed_events = processed_events
        self.status_record.anomaly_count = anomaly_count
        self.status_record.last_error = last_error
        self.status_record.last_heartbeat_at = datetime.now(timezone.utc).isoformat()

        status_dir = os.path.join(self.repo.base_dir, "workers")
        os.makedirs(status_dir, exist_ok=True)
        status_path = os.path.join(status_dir, f"{self.worker_id}.json")
        try:
            with open(status_path, "w", encoding="utf-8") as f:
                f.write(self.status_record.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Failed to write worker status file: {e}")

    def analyze_run(self, run_id: str, allow_partial: bool = True) -> AnalysisResult:
        """Loads and processes the artifacts for the specified completed/partial run."""
        self.update_status("RUNNING", current_run_id=run_id)

        try:
            pipeline = AnalysisPipeline(repo=self.repo)

            # Count the loaded raw events to update status metrics accurately
            events_path = self.repo.resolve_path(run_id, "events")
            event_count = 0
            if os.path.exists(events_path):
                with open(events_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            event_count += 1

            result = pipeline.run(run_id, allow_partial=allow_partial)

            if result.status == "FAILED":
                self.update_status(
                    "FAILED",
                    current_run_id=run_id,
                    processed_events=event_count,
                    last_error=result.errors[0] if result.errors else "Analysis pipeline failed"
                )
            else:
                self.update_status(
                    "COMPLETED",
                    current_run_id=run_id,
                    processed_events=event_count,
                    anomaly_count=result.anomaly_count
                )
            return result

        except Exception as e:
            err_msg = str(e)
            logger.error(f"ExternalAnomalyWorker encountered fatal exception: {e}")
            self.update_status("FAILED", current_run_id=run_id, last_error=err_msg)
            return AnalysisResult(
                run_id=run_id,
                status="FAILED",
                errors=[err_msg]
            )


class LiveWorkerConfig(BaseModel):
    """
    Configuration model schema for the live stream anomaly worker service.
    Defines connection backends, enabled live rules, window tick constraints, and threshold limits.
    """
    worker_id: str = Field(default_factory=lambda: f"live-worker-{uuid.uuid4().hex[:8]}")
    stream_backend: str = "in_process"  # "redis" | "in_process" | "null"
    stream_name: str = "simulation:events"
    consumer_group: str = "observatory:consumers"
    window_ticks: int = 100
    max_memory_mb: float = 512.0
    enabled_rules: List[str] = Field(default_factory=lambda: [
        "HardLawViolationLive",
        "NavigationStuckLive",
        "EventDropRateHigh",
        "GovernorDegradedLive",
        "CriticalEventObserved"
    ])
    output_mode: str = "file"  # "file" | "redis" | "metric"
    redis_url: str = "redis://localhost:6379/0"


class LiveAnomalyWorker:
    """
    Stand-alone live streaming worker consuming simulation events, managing a sliding
    tick window, executing lightweight live rules, and publishing anomaly alerts.
    """
    def __init__(self, config: Optional[LiveWorkerConfig] = None) -> None:
        self.config = config or LiveWorkerConfig()
        self.worker_id = self.config.worker_id

        self.status_record = WorkerStatus(
            worker_id=self.worker_id,
            mode="stream",
            status="PENDING",
            last_event_tick=0,
            stream_lag=0,
            memory_estimate=0.0
        )

        self.repo = RunArtifactRepository()
        self.window = RollingEventWindow(window_ticks=self.config.window_ticks)

        # Load rules
        self.rules: List[LiveAnomalyRule] = []
        for rname in self.config.enabled_rules:
            if rname == "HardLawViolationLive":
                self.rules.append(HardLawViolationLive())
            elif rname == "NavigationStuckLive":
                self.rules.append(NavigationStuckLive())
            elif rname == "EventDropRateHigh":
                self.rules.append(EventDropRateHigh())
            elif rname == "GovernorDegradedLive":
                self.rules.append(GovernorDegradedLive())
            elif rname == "CriticalEventObserved":
                self.rules.append(CriticalEventObserved())
            else:
                logger.warning(f"Unknown live rule name: {rname}")

        self._dedup_cache: Dict[str, float] = {}

        self.processed_count = 0
        self.anomaly_count = 0
        self.last_event_tick = 0

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self.redis_consumer: Optional[RedisStreamConsumer] = None
        self.in_process_subscriber: Optional[LiveEventSubscriber] = None

    def start(self) -> None:
        """Starts the background worker thread."""
        self._stop_event.clear()
        self.status_record.status = "RUNNING"
        self.update_status("RUNNING")

        if self.config.stream_backend == "redis":
            self.redis_consumer = RedisStreamConsumer(
                redis_url=self.config.redis_url,
                stream_name=self.config.stream_name,
                group_name=self.config.consumer_group,
                consumer_name=self.worker_id
            )
            self.redis_consumer.connect()
        elif self.config.stream_backend == "in_process":
            self.in_process_subscriber = LiveEventSubscriber(SubscriptionFilter(), capacity=2000)
            LiveEventPublisher.get_instance().register(self.in_process_subscriber)

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"LiveAnomalyWorker {self.worker_id} started successfully with backend {self.config.stream_backend}.")

    def stop(self) -> None:
        """Stops the background worker thread cleanly."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        if self.config.stream_backend == "in_process" and self.in_process_subscriber:
            LiveEventPublisher.get_instance().unregister(self.in_process_subscriber)

        if self.redis_consumer:
            self.redis_consumer.close()

        self.update_status("STOPPED")
        logger.info(f"LiveAnomalyWorker {self.worker_id} stopped.")

    def _run_loop(self) -> None:
        """Main polling run loop of the worker service."""
        last_flush_time = 0.0
        while not self._stop_event.is_set():
            processed_any = False

            try:
                if self.config.stream_backend == "redis" and self.redis_consumer:
                    count = self.redis_consumer.read_and_process(self.process_event, block_ms=500)
                    if count > 0:
                        processed_any = True
                elif self.config.stream_backend == "in_process" and self.in_process_subscriber:
                    events = self.in_process_subscriber.get_events()
                    if events:
                        processed_any = True
                        for ev in events:
                            self.process_event(ev)
                else:
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"LiveAnomalyWorker run loop exception: {e}")
                self.status_record.last_error = str(e)
                # Route worker failure as a critical alert
                try:
                    from src.observability.alerts.manager import AlertsManager
                    from src.observability.alerts.models import AlertEvent
                    router = AlertsManager.get_router()
                    event = AlertEvent.create_critical_anomaly(
                        run_id=self.status_record.current_run_id or "unknown",
                        tick=self.last_event_tick or None,
                        message=f"LiveAnomalyWorker run loop exception: {e}",
                        details={"worker_id": self.worker_id, "rule_id": "WorkerLoopFailure", "error": str(e)}
                    )
                    router.route(event)
                except Exception:
                    pass  # Never let alert routing break the worker loop

            now = time.time()
            if now - last_flush_time >= 1.0 or processed_any:
                self.flush_diagnostics()
                last_flush_time = now

            if not processed_any:
                time.sleep(0.1)

    def process_event(self, event: SimulationEvent) -> None:
        """Processes a single event from the stream."""
        self.processed_count += 1
        self.last_event_tick = max(self.last_event_tick, event.tick)
        self.status_record.current_run_id = event.run_id

        self.window.push(event)

        for rule in self.rules:
            try:
                anomalies = rule.evaluate_event(event, self.window)
                for anomaly in anomalies:
                    self.emit_anomaly(anomaly, event)
            except Exception as ex:
                logger.error(f"Error evaluating rule {rule.__class__.__name__}: {ex}")

    def emit_anomaly(self, anomaly: Anomaly, cause_event: SimulationEvent) -> None:
        """Publishes a detected anomaly, enforcing deduplication cooldown gates."""
        dedup_key = f"{anomaly.rule_name}:{anomaly.entity_id or 'global'}:{cause_event.event_category}"
        if dedup_key in self._dedup_cache:
            if cause_event.tick - self._dedup_cache[dedup_key] < 20:
                return

        self._dedup_cache[dedup_key] = cause_event.tick
        self.anomaly_count += 1

        if "file" in self.config.output_mode:
            self._write_anomaly_to_file(anomaly)

        logger.warning(f"[{anomaly.severity}] LIVE ANOMALY: {anomaly.rule_name} on {anomaly.entity_id or 'system'}: {anomaly.message}")

        # Route critical/error anomalies through the alert system
        if anomaly.severity in ("CRITICAL", "ERROR", "HIGH"):
            try:
                from src.observability.alerts.manager import AlertsManager
                from src.observability.alerts.models import AlertEvent
                router = AlertsManager.get_router()
                event = AlertEvent.create_critical_anomaly(
                    run_id=cause_event.run_id,
                    tick=cause_event.tick,
                    message=f"Live anomaly: {anomaly.rule_name} on {anomaly.entity_id or 'system'}: {anomaly.message}",
                    details={
                        "rule_id": anomaly.rule_name,
                        "entity_id": anomaly.entity_id,
                        "severity": anomaly.severity,
                        "evidence": anomaly.evidence if hasattr(anomaly, 'evidence') else {}
                    }
                )
                router.route(event)
            except Exception:
                pass  # Never let alert routing break the anomaly worker

    def _write_anomaly_to_file(self, anomaly: Anomaly) -> None:
        """Appends the serialized anomaly JSON record to anomaly_events.jsonl."""
        run_id = self.status_record.current_run_id or "default"
        run_dir = os.path.join(self.repo.base_dir, run_id)
        os.makedirs(run_dir, exist_ok=True)

        file_path = os.path.join(run_dir, "anomaly_events.jsonl")
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(anomaly.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to append anomaly event to file: {e}")

    def flush_diagnostics(self) -> None:
        """Polls resources and flushes updated status to JSON files."""
        try:
            process = psutil.Process(os.getpid())
            rss_mb = process.memory_info().rss / (1024 * 1024)
        except Exception:
            rss_mb = 0.0

        self.status_record.memory_estimate = rss_mb
        self.status_record.processed_events = self.processed_count
        self.status_record.anomaly_count = self.anomaly_count
        self.status_record.last_event_tick = self.last_event_tick
        self.status_record.last_heartbeat_at = datetime.now(timezone.utc).isoformat()

        if rss_mb > self.config.max_memory_mb:
            logger.warning(f"LiveAnomalyWorker {self.worker_id} memory {rss_mb:.1f}MB exceeds limit {self.config.max_memory_mb}MB. Degrading status.")
            self.status_record.status = "DEGRADED"
            self.status_record.last_error = f"Memory threshold exceeded: {rss_mb:.1f}MB"
        elif self.status_record.status == "DEGRADED":
            self.status_record.status = "RUNNING"
            self.status_record.last_error = None

        self.update_status(
            status=self.status_record.status,
            current_run_id=self.status_record.current_run_id,
            processed_events=self.processed_count,
            anomaly_count=self.anomaly_count,
            last_error=self.status_record.last_error
        )

    def update_status(
        self,
        status: str,
        current_run_id: Optional[str] = None,
        processed_events: int = 0,
        anomaly_count: int = 0,
        last_error: Optional[str] = None
    ) -> None:
        """Writes worker status to workers/ directory."""
        self.status_record.status = status
        self.status_record.current_run_id = current_run_id
        self.status_record.processed_events = processed_events
        self.status_record.anomaly_count = anomaly_count
        self.status_record.last_error = last_error
        self.status_record.last_heartbeat_at = datetime.now(timezone.utc).isoformat()

        status_dir = os.path.join(self.repo.base_dir, "workers")
        os.makedirs(status_dir, exist_ok=True)
        status_path = os.path.join(status_dir, f"{self.worker_id}.json")
        try:
            with open(status_path, "w", encoding="utf-8") as f:
                f.write(self.status_record.model_dump_json(indent=2))
        except Exception as e:
            logger.error(f"Failed to write worker status file: {e}")
