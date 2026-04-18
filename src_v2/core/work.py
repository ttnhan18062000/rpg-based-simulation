from __future__ import annotations

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class WorkClass(Enum):
    """
    Semantic categories for simulation work.
    Used for scheduling boundaries and budgeting.
    """
    CRITICAL = auto()     # Authoritative, non-deferrable (actions)
    PERIODIC = auto()     # Authoritative, cadence-based (up-keep)
    OPPORTUNISTIC = auto()# Non-authoritative, optional (traces, visuals)
    DEFERRED = auto()      # Postponed critical/periodic work


@dataclass(frozen=True, slots=True)
class WorkItem:
    """
    A discrete unit of work requested from the kernel.
    """
    owner_id: int | str   # Entity ID or Subsystem Name
    work_class: WorkClass
    
    # Payload for execution (system-specific)
    action_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Ordering hints
    priority: int = 0     # Class-local priority
    due_tick: int = 0     # For periodic / deferred work
    readiness: float = 0.0# For critical entity actions
    cadence: int = 0      # For periodic work rescheduling
    
    @property
    def is_deferrable(self) -> bool:
        """Law: Critical work is never deferrable."""
        return self.work_class != WorkClass.CRITICAL
