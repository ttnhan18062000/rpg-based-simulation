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
    M7 Law: Only include Primary Pressure Inputs here.
    """
    tick_compute_ms: float = 0.0
    tick_compute_ms_avg: float = 0.0  # Trending signal
    
    work_debt_total: int = 0
    
    worker_utilization: float = 0.0   # Ratio of concurrent workers used
    queue_utilization: float = 0.0    # Ratio of work-queue depth used
    
    memory_estimate_mb: float = 0.0
    memory_trend_mb_per_tick: float = 0.0  # Trending signal
    
    replay_backlog_kb: int = 0       # Current in-memory staging size
    active_workers: int = 0           # Current concurrent worker count
    dropped_work_delta: int = 0       # Work dropped in the current tick


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
