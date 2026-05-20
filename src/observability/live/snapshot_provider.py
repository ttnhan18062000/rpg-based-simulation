from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from src.observability.config import ObservabilityConfig

class LiveRunStatus(BaseModel):
    run_id: Optional[str] = None
    scenario_name: str = "default"
    scenario_type: str = "default"
    status: str = "IDLE"
    current_tick: int = 0
    ticks_requested: Optional[int] = None
    started_at: Optional[str] = None
    elapsed_seconds: float = 0.0
    observability_mode: str = "DISABLED"
    governor_mode: str = "NORMAL"
    health_state: str = "UNKNOWN"
    last_error: Optional[str] = None
    last_hard_law_violation_tick: int = -1

class LiveRunSnapshot(BaseModel):
    run_status: LiveRunStatus
    latest_world_metrics: Dict[str, Any] = Field(default_factory=dict)
    latest_runtime_status: Dict[str, Any] = Field(default_factory=dict)
    latest_metric_window_summary: Dict[str, Any] = Field(default_factory=dict)
    recent_event_counts: Dict[str, int] = Field(default_factory=dict)
    recent_anomaly_counts: Dict[str, int] = Field(default_factory=dict)
    hard_law_violation_count: int = 0

class LiveSnapshotProvider:
    """Provides thread-safe read-only status and metrics snapshots of the running simulation."""
    
    @staticmethod
    def get_status(manager: Optional[Any]) -> LiveRunStatus:
        """Resolves the current LiveRunStatus of the engine manager."""
        if manager is None:
            return LiveRunStatus(
                status="IDLE",
                observability_mode=ObservabilityConfig.get_mode().name,
                health_state="UNKNOWN"
            )
            
        # Determine status string
        if manager.is_stopping:
            status_str = "STOPPING"
        elif manager.is_paused:
            status_str = "PAUSED"
        elif manager.is_running:
            status_str = "RUNNING"
        else:
            status_str = "IDLE"
            
        kernel = manager.kernel
        run_id = kernel.run_id if kernel else None
        current_tick = manager.tick
        
        # Started at & elapsed seconds
        started_at_str = None
        elapsed = 0.0
        if manager.started_at is not None:
            started_at_str = datetime.fromtimestamp(manager.started_at, tz=timezone.utc).isoformat()
            if manager.is_running or manager.is_paused:
                elapsed = time.time() - manager.started_at
                
        # Governor mode
        gov_mode_str = "NORMAL"
        last_error = None
        last_violation_tick = -1
        violations_count = 0
        
        if kernel:
            kernel_status = kernel.status
            if kernel_status:
                gov_mode_str = kernel_status.current_mode.name
                last_violation_tick = getattr(kernel_status, "last_hard_law_violation_tick", -1)
                violations_dict = getattr(kernel_status, "cumulative_violations", {})
                violations_count = sum(violations_dict.values()) if violations_dict else 0
                
        # Calculate simple health state
        if violations_count > 0 or last_violation_tick >= 0:
            health = "CRITICAL"
        elif gov_mode_str in ("DEGRADED", "CRITICAL"):
            health = "DEGRADED"
        elif manager.errors_total > 0:
            health = "WARNING"
        elif status_str in ("RUNNING", "PAUSED"):
            health = "HEALTHY"
        else:
            health = "UNKNOWN"
            
        if manager.errors_total > 0:
            last_error = f"Encountered {manager.errors_total} tick loop error(s)"
            
        return LiveRunStatus(
            run_id=run_id,
            scenario_name="default",
            scenario_type="default",
            status=status_str,
            current_tick=current_tick,
            ticks_requested=None,
            started_at=started_at_str,
            elapsed_seconds=elapsed,
            observability_mode=ObservabilityConfig.get_mode().name,
            governor_mode=gov_mode_str,
            health_state=health,
            last_error=last_error,
            last_hard_law_violation_tick=last_violation_tick
        )

    @staticmethod
    def get_snapshot(manager: Optional[Any]) -> LiveRunSnapshot:
        """Resolves the complete LiveRunSnapshot of the engine manager."""
        run_status = LiveSnapshotProvider.get_status(manager)
        if manager is None or run_status.status == "IDLE":
            return LiveRunSnapshot(run_status=run_status)
            
        metrics_snapshot = manager.get_metrics_snapshot()
        
        # Split world metrics vs runtime status
        world_metrics = {
            "active_entities": metrics_snapshot.get("active_entities", 0),
            "gold_circulation_total": metrics_snapshot.get("gold_circulation_total", 0.0),
            "rejection_counts": metrics_snapshot.get("rejection_counts", {}),
            "quest_status_counts": metrics_snapshot.get("quest_status_counts", {}),
        }
        
        runtime_status = {
            "tps": metrics_snapshot.get("tps", 0.0),
            "tick_compute_ms": metrics_snapshot.get("tick_compute_ms", 0.0),
            "worker_utilization": metrics_snapshot.get("worker_utilization", 0.0),
            "queue_utilization": metrics_snapshot.get("queue_utilization", 0.0),
            "memory_rss_bytes": metrics_snapshot.get("memory_rss_bytes", 0.0),
            "work_debt_total": metrics_snapshot.get("work_debt_total", 0),
            "dropped_work_delta": metrics_snapshot.get("dropped_work_delta", 0),
            "errors_total": metrics_snapshot.get("errors_total", 0),
            "phase_costs_ms": metrics_snapshot.get("phase_costs_ms", {}),
        }
        
        # Event type counts from EventRecorder
        event_counts = {}
        kernel = manager.kernel
        if kernel and getattr(kernel, "event_recorder", None):
            event_counts = kernel.event_recorder.event_count_by_type.copy()
            
        # Extract violation counts
        violations_dict = metrics_snapshot.get("hard_law_violations_cumulative", {})
        violation_count = sum(violations_dict.values()) if violations_dict else 0
        
        # Summary metrics windows
        window_summary = {
            "tick_compute_ms_p95": metrics_snapshot.get("tick_compute_ms", 0.0),
        }
        
        return LiveRunSnapshot(
            run_status=run_status,
            latest_world_metrics=world_metrics,
            latest_runtime_status=runtime_status,
            latest_metric_window_summary=window_summary,
            recent_event_counts=event_counts,
            recent_anomaly_counts=violations_dict,
            hard_law_violation_count=violation_count
        )
