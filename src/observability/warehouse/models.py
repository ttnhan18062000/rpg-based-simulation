from __future__ import annotations
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class RunRecord(BaseModel):
    """Database representation of a simulation run."""
    run_id: str
    scenario_name: str
    scenario_type: str
    seed: int
    status: str
    ticks_completed: int
    health_score: float
    started_at: str
    ended_at: Optional[str] = None
    schema_version: str = "warehouse_schema_v1"
    manifest_json: str  # Full original manifest raw copy

class SweepRecord(BaseModel):
    """Database representation of a scenario sweep."""
    sweep_id: str
    scenario_name: str
    scenario_type: str
    total_runs: int
    completed_runs: int
    failed_runs: int
    average_health_score: float
    created_at: str
    schema_version: str = "warehouse_schema_v1"
    summary_json: str  # Full original sweep summary raw copy

class EventRecord(BaseModel):
    """Database representation of a single simulation event."""
    run_id: str
    tick: int
    event_type: str
    event_category: str
    severity: str
    entity_id: Optional[str] = None
    region_id: Optional[str] = None
    quest_id: Optional[str] = None
    faction_id: Optional[str] = None
    message: str
    payload_json: str  # Serialized event payload attributes
    created_at: str

class MetricWindowRecord(BaseModel):
    """Database representation of a performance/simulation metric window."""
    run_id: str
    window_start_tick: int
    window_end_tick: int
    tick_compute_ms_avg: float
    tick_compute_ms_p95: float
    memory_rss_bytes_avg: float
    memory_rss_bytes_max: float
    alive_entities_avg: float
    gold_total_avg: float
    event_count: int
    hard_law_violation_count: int
    metrics_json: str  # Full metrics dictionary dump

class AnomalyRecord(BaseModel):
    """Database representation of a post-run detected anomaly."""
    run_id: str
    rule_id: str
    severity: str
    domain: str
    tick_start: int
    tick_end: int
    affected_entity_count: int
    message: str
    evidence_json: str  # Full evidence/context raw copy

class HardLawViolationRecord(BaseModel):
    """Database representation of a physics or hard law infraction."""
    run_id: str
    tick: int
    violation_type: str
    severity: str
    actor_id: Optional[str] = None
    target_id: Optional[str] = None
    message: str
    evidence_json: str  # Original evidence copy

class BaselineRecord(BaseModel):
    """Database representation of a golden baseline parameter set."""
    scenario_name: str
    created_at: str
    health_score_threshold: float
    tps_threshold: float
    baseline_json: str

class ComparisonRecord(BaseModel):
    """Database representation of a baseline comparison result."""
    run_id: str
    baseline_run_id: str
    health_score_delta: float
    status: str
    comparison_json: str

class WarehouseIngestionResult(BaseModel):
    """Standard payload summarizing an ingestion execution job."""
    ingestion_id: str
    run_id: Optional[str] = None
    sweep_id: Optional[str] = None
    status: str  # COMPLETED, FAILED, DRY_RUN
    records_ingested: Dict[str, int] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    duration_ms: float
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WarehouseHealthStatus(BaseModel):
    """Structured warehouse connection state."""
    connected: bool
    latency_ms: float
    error: Optional[str] = None
