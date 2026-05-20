from __future__ import annotations
import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.observability.reporting.artifact_repository import RunArtifactRepository
from src.observability.anomaly.pipeline import AnalysisPipeline, AnalysisResult

logger = logging.getLogger(__name__)


class WorkerStatus(BaseModel):
    """
    Tracks state and diagnostics of the standalone anomaly worker process.
    Provides visibility into processing throughput and heartbeat logs.
    """
    worker_id: str
    mode: str = "artifact"  # "artifact" or "stream"
    status: str = "PENDING"  # "PENDING" | "RUNNING" | "COMPLETED" | "FAILED"
    current_run_id: Optional[str] = None
    processed_events: int = 0
    anomaly_count: int = 0
    last_heartbeat_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_error: Optional[str] = None


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
