from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict


class HardwareClass(str, Enum):
    CLASS_A = "class_a"  # Server/High-end
    CLASS_B = "class_b"  # Workstation/Medium
    CLASS_C = "class_c"  # Legacy/Edge


class RuntimeProfile(BaseModel):
    """
    Authoritative resource-envelope contract.
    Defines hard ceilings for engine execution.
    """
    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Name of the runtime profile")
    hardware_class: HardwareClass = Field(..., description="Hardware class certification")
    
    # RAM and CPU
    max_ram_mb: int = Field(..., gt=0, description="Max Resident Set Size in MB")
    max_cpu_percent: float = Field(..., gt=0, le=100, description="Target CPU usage percentage")
    
    # Threading and Queues
    max_worker_count: int = Field(..., ge=0, description="Maximum concurrent workers")
    max_queue_depth: int = Field(..., gt=0, description="Limit for action and work queues")
    max_work_debt: int = Field(1000, gt=0, description="Limit for accumulated work debt")
    
    # Observability and Replay
    max_replay_buffer_kb: int = Field(..., ge=0, description="Memory cap for in-memory replay window")
    max_observability_budget_percent: float = Field(..., ge=0, le=100, description="Max CPU time for metrics/logging")
    
    # Latency
    max_tick_budget_ms: float = Field(..., gt=0, description="Max ms allowed per authoritative tick")
    
    # Operational Controls (Milestone B)
    sampling_interval_ticks: int = Field(10, gt=0, description="Cadence for OS signal sampling (RSS)")
    recovery_watermark: float = Field(0.8, ge=0.5, le=0.95, description="Hysteresis multiplier for recovery")
    dwell_time_ticks: int = Field(10, ge=0, description="Minimum ticks to stay in mode before recovery")
    confidence_window_ticks: int = Field(5, ge=0, description="Consecutive ticks required below watermark to recover")

    # Degradation
    degradation_threshold_ram: float = Field(0.85, ge=0.5, le=1.0, description="RAM pressure to trigger shedding")
    degradation_threshold_cpu: float = Field(0.90, ge=0.5, le=1.0, description="CPU pressure to trigger shedding")

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Profile name cannot be empty")
        return v
