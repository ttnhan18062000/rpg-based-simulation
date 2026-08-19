from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional

class LifecycleOutcome(str, Enum):
    """
    Standardized taxonomy for simulation lifecycle finalization.
    M7 Law: Used to communicate the truth about startup and shutdown.
    """
    SUCCESS = "SUCCESS"
    TIMEOUT = "TIMEOUT"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"

@dataclass(frozen=True, slots=True)
class ShutdownResult:
    """
    M10 Law: Truthful representation of the engine's final state.
    """
    final_tick: int
    final_hash: str
    replay_outcome: LifecycleOutcome
    overall_outcome: LifecycleOutcome
    failure_reason: Optional[str] = None
    verification_level: str = "FULL"


@dataclass
class ShutdownReport:
    """
    Machine-readable lifecycle supervisor report produced by Kernel.shutdown().

    Consumers: dashboard, tests, post-mortem tooling.
    Access via kernel.shutdown_report() after shutdown() returns.
    """
    workers_started: int = 0
    workers_stopped: int = 0
    open_file_handles: int = -1
    pending_replay_flushes: int = 0
    survival_event_counts: Dict[str, int] = field(default_factory=dict)
    outcome: str = "SUCCESS"
    warnings: List[str] = field(default_factory=list)
