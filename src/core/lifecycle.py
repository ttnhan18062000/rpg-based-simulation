from enum import Enum
from dataclasses import dataclass
from typing import Optional

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
