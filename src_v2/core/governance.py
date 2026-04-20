from __future__ import annotations

from enum import IntEnum, auto
from dataclasses import dataclass, field
from typing import Dict, Any


class RuntimeMode(IntEnum):
    """
    Operational modes representing the engine's pressure state.
    Ranked by severity.
    """
    NORMAL = 0
    CONSTRAINED = 1
    DEGRADED = 2
    SURVIVAL = 3


@dataclass(frozen=True, slots=True)
class PressureSignals:
    """
    Operational measurements used for governing decisions.
    Status: FROZEN (Resource Phase 4 Milestone 1)
    
    M7 Law: Only include Primary Pressure Inputs here.
    """
    # 1. Compute & Load
    tick_compute_ms: float = 0.0      # Absolute nanosecond-derived compute time
    tick_compute_ms_avg: float = 0.0  # Rolling 5-tick average
    
    # 2. Work & Debt
    work_debt_total: int = 0          # Total unhandled system debt (D1, D2, ...)
    
    # 3. Utilization (Disaggregated - Law M7.1)
    worker_utilization: float = 0.0   # Current worker usage / Max allowed
    queue_utilization: float = 0.0    # Current queue depth / Max allowed
    active_workers: int = 0           # Raw count of concurrent workers
    
    # 4. Memory & Resource
    memory_estimate_mb: float = 0.0   # RSS measurement from collector
    memory_trend_mb_per_tick: float = 0.0 # Delta vs previous tick
    
    # 5. Pipeline & Lifecycle
    replay_backlog_kb: int = 0       # In-memory staging pending persistence
    dropped_work_delta: int = 0       # Work shed in the current tick
    
    # 6. Gameplay Throughput (Milestone 2)
    movement_count: int = 0           # Successfully processed moves in current tick
    
    # 7. Performance Breakdown (Milestone 3)
    phase_costs_ms: Dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class EnvironmentCapture:
    """
    Law M10: Truthful representation of the execution context.
    Distinguishes between detected physical facts and effective logical class.
    """
    detected_cores: int
    detected_ram_gb: float
    detected_class: str
    
    effective_class: str            # Final class after profile-governance / overrides
    is_overridden: bool = False
    
    os_name: str = "linux"
    python_version: str = "3.13"
    commit_sha: str = "unknown"     # Provided by CI or build context
