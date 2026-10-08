from __future__ import annotations

from enum import IntEnum, auto
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


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
    metrics: Dict[str, float] = field(default_factory=dict)

    # 8. Cost inputs the governors compare with the profile (PERF-D1 signal contract). None means "use the measured
    # value", so a Live run and every caller that sets only ``tick_compute_ms`` behave exactly as before. The Canonical
    # contract sets these from deterministic work counts (reference-milliseconds) instead of a clock.
    tick_cost: Optional[float] = None
    tick_budget: Optional[float] = None
    phase_cost: Optional[Dict[str, float]] = None

    @property
    def effective_tick_cost(self) -> float:
        """The tick cost the governors compare with the budget: ``tick_cost`` when set, else the measured ``tick_compute_ms``."""
        return self.tick_compute_ms if self.tick_cost is None else self.tick_cost

    def effective_tick_budget(self, profile_budget_ms: float) -> float:
        """The budget the cost is compared with: ``tick_budget`` when set, else the profile's ``max_tick_budget_ms``."""
        return profile_budget_ms if self.tick_budget is None else self.tick_budget

    @property
    def effective_phase_cost(self) -> Dict[str, float]:
        """Per-bucket cost: ``phase_cost`` when set, else the measured ``phase_costs_ms``."""
        return self.phase_costs_ms if self.phase_cost is None else self.phase_cost


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
