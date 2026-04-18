from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, TYPE_CHECKING
from src_v2.core.updates import EntityUpdate

if TYPE_CHECKING:
    from src_v2.core.state import EntityState


@dataclass(frozen=True, slots=True)
class WorkerPacket:
    """
    Law: A worker must receive a compact, bounded context.
    M8 Core contract for thread-safe work distribution.
    """
    tick: int
    world_time: int
    seed: int
    
    # Target Information
    subject: EntityState
    
    # Restricted View (Neighbors context)
    # M8 Recommendation: Direct interaction neighborhood only.
    neighbor_view: Dict[int, EntityState]
    
    # Work Type details (copied from WorkItem for convenience)
    action_type: str
    payload: Dict[str, Any]


@dataclass(frozen=True, slots=True)
class WorkerResult:
    """
    Law: Workers return compact authoritative deltas, not world modifications.
    """
    entity_id: int
    update: EntityUpdate
    
    # Metadata for verification/replay
    compute_time_ns: int = 0
