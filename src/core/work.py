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
    work_id: str          # Unique work identifier (e.g. tick:entity:kind)
    work_class: WorkClass
    
    # Payload for execution (system-specific)
    work_kind: str
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


def packet_work_id(tick: int, owner_id: int | str, work_kind: str) -> str:
    """The work id a worker packet and its result carry. The executor builds it for the packet and for the look-up that carries ``WorkItem.priority`` onto the result,
    so both sides use this one function (they used two different formats before, and the look-up never matched, TCK-20261021-WORK-ITEM-PRIORITY-LOOKUP-KEY-MISMATCH).
    It is not ``WorkItem.work_id`` (the scheduler's own ``{tick}:{kind}:{id}``), which no packet or result carries."""
    return f"{tick}:{owner_id}:{work_kind}"
