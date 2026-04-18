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
    """
    tick_compute_ms: float = 0.0
    work_debt_total: int = 0
    queue_utilization: float = 0.0  # 0.0 to 1.0
    memory_estimate_mb: float = 0.0
