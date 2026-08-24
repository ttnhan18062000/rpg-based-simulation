from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from src.engine.cadence import SystemCadence


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

    # Cadence (Scheduling)
    cadence: SystemCadence = Field(default_factory=SystemCadence, description="System execution frequencies")

    # Optimization (Milestone 7)
    lod_enabled: bool = Field(True, description="Enable adaptive Level of Detail for entity simulation")

    # Security (HTTP API-key auth, TCK-20260823-HTTP-API-KEY-AUTH)
    api_key_hashes: str = Field(
        default="",
        description=(
            "Comma-separated 'client_id:sha256hex' pairs. Must stay a plain str -- "
            "ConfigLoader's env-var loop (src/config/loader.py:54-70) only handles "
            "scalar field types and raises an uncaught TypeError on List/Dict "
            "annotations. Parsed into a {hash: client_id} mapping by "
            "src/api/auth.py::configure_api_keys(), never on this model (frozen). "
            "Empty string means no keys configured -- every protected route then "
            "401s for every caller (fail-closed default)."
        ),
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Profile name cannot be empty")
        return v


# Milestone 10: Formal Production Profiles
PROD_SMALL = RuntimeProfile(
    name="PROD_SMALL",
    hardware_class=HardwareClass.CLASS_C,
    max_ram_mb=1024,
    max_cpu_percent=70.0,
    max_worker_count=2,
    max_queue_depth=2000,
    max_replay_buffer_kb=16384,
    max_observability_budget_percent=2.0,
    max_tick_budget_ms=100.0,
    max_work_debt=1000,
    lod_enabled=True,
    cadence=SystemCadence(
        strategic_intelligence=20,
        world_dynamics=100,
        town_resolution=10
    )
)

PROD_DEFAULT = RuntimeProfile(
    name="PROD_DEFAULT",
    hardware_class=HardwareClass.CLASS_B,
    max_ram_mb=2048,
    max_cpu_percent=85.0,
    max_worker_count=4,
    max_queue_depth=5000,
    max_replay_buffer_kb=65536,
    max_observability_budget_percent=5.0,
    max_tick_budget_ms=50.0,
    max_work_debt=5000,
    lod_enabled=True,
    cadence=SystemCadence(
        strategic_intelligence=10,
        world_dynamics=50,
        town_resolution=5
    )
)

PROD_LARGE = RuntimeProfile(
    name="PROD_LARGE",
    hardware_class=HardwareClass.CLASS_A,
    max_ram_mb=4096,
    max_cpu_percent=95.0,
    max_worker_count=8,
    max_queue_depth=10000,
    max_replay_buffer_kb=131072,
    max_observability_budget_percent=10.0,
    max_tick_budget_ms=100.0, # 10 FPS target for 5,000 entities
    max_work_debt=10000,
    lod_enabled=True,
    cadence=SystemCadence(
        strategic_intelligence=10,
        world_dynamics=50,
        town_resolution=5
    )
)

PROD_STRESS = RuntimeProfile(
    name="PROD_STRESS",
    hardware_class=HardwareClass.CLASS_A,
    max_ram_mb=8192,
    max_cpu_percent=100.0,
    max_worker_count=16,
    max_queue_depth=50000,
    max_replay_buffer_kb=524288,
    max_observability_budget_percent=15.0,
    max_tick_budget_ms=500.0, # 2 FPS target for 10,000 entities
    max_work_debt=50000,
    lod_enabled=True,
    cadence=SystemCadence(
        strategic_intelligence=5,
        world_dynamics=20,
        town_resolution=2
    )
)
