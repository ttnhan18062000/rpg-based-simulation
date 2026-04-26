from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, TYPE_CHECKING
from src.core.updates import EntityUpdate
from src.core.work import WorkClass

if TYPE_CHECKING:
    from src.core.state import EntityState


class ResultStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


@dataclass(frozen=True, slots=True)
class WorkerPacket:
    """
    Law: A worker must receive a compact, bounded, and read-only context.
    Tick-local deterministic identity: {tick}:{ordinal}
    """
    packet_id: str
    work_id: str
    tick: int
    world_time: int
    seed: int
    
    # Target Information (Read-Only Snapshot)
    # work_class included for policy-aware logic inside workers
    work_class: WorkClass
    subject: EntityState
    
    # Canonical Context (Sorted by EntityID)
    # M8 Law: Neighbor context must be deterministic regardless of dictionary hash.
    neighbor_view: List[Tuple[int, EntityState]]
    
    # Work Type details
    work_kind: str
    payload: Dict[str, Any]


@dataclass(frozen=True, slots=True)
class WorkerResult:
    """
    Law: Workers return compact authoritative deltas linked to their source packet.
    M8 Law (Option A): One result per entity per tick.
    """
    source_packet_id: str
    work_id: str
    entity_id: int
    work_class: WorkClass
    update: EntityUpdate
    status: ResultStatus = ResultStatus.SUCCESS
    
    # Sorting keys for frozen commit law
    class_priority: int = 0
    local_priority: int = 0
    
    # Metadata for verification/replay
    compute_time_ns: int = 0
