from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
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
    
    # Priority Metadata (M8 Law: Determinism requires sorting by priority)
    class_priority: int = 0
    local_priority: int = 0
    
    regions: Dict[str, Any] = field(default_factory=dict)
    resource_nodes: Dict[int, Any] = field(default_factory=dict)
    buildings: Dict[int, Any] = field(default_factory=dict)
    groups: Dict[int, Any] = field(default_factory=dict)
    corpses: Dict[int, Any] = field(default_factory=dict)
    ground_items: Dict[int, Any] = field(default_factory=dict)
    all_entities: Dict[int, EntityState] = field(default_factory=dict)
    spatial_grid: Optional[Any] = None
    occupancy_map: Optional[Dict[Tuple[int, int], int]] = None
    region_list: Optional[List[Any]] = None
    building_map: Optional[Dict[Tuple[int, int], Any]] = None
    _region_index_cache: Optional[Any] = field(default=None, repr=False, compare=False)
    _regions_global_bounds: Optional[Any] = field(default=None, repr=False, compare=False)
    _building_region_map_cache: Optional[Any] = field(default=None, repr=False, compare=False)
    _node_map_cache: Optional[Any] = field(default=None, repr=False, compare=False)
    _corpse_map_cache: Optional[Any] = field(default=None, repr=False, compare=False)
    _ground_item_map_cache: Optional[Any] = field(default=None, repr=False, compare=False)

    # Deterministic Context (Defaulted for backwards compatibility/optional inclusion)
    blocked_tiles: List[Tuple[int, int]] = field(default_factory=list) # Spatial Law
    transient_claims: List[Tuple[int, int]] = field(default_factory=list) # Multi-agent conflict truth
    terrain: Dict[Tuple[int, int], str] = field(default_factory=dict) # Tile terrain types

    @property
    def entities(self) -> Dict[int, EntityState]:
        """Milestone D Law: Property-based access to the canonical neighbor view."""
        if self.all_entities:
            return self.all_entities
        return {eid: ent for eid, ent in self.neighbor_view}

    def to_readonly(self) -> WorkerPacket:
        """
        Milestone D Law:Parity with AuthoritativeState for decision logic.
        Since WorkerPacket is already frozen, this returns self.
        """
        return self


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
    
    # System Updates (Milestone C: De-simulation)
    # Allows workers/executors to update global state components
    work_debt_update: Optional[int] = None
    subsystem_id: Optional[str] = None
