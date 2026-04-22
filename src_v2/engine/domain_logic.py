# src_v2/engine/domain_logic.py
from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, Dict, Any, Optional

from src_v2.core.updates import EntityUpdate

if TYPE_CHECKING:
    from src_v2.core.state import EntityState

class SimulationDomainLogic:
    """
    Law: Absolute semantic truth for RPG domain operations.
    Isolated from networking, concurrency, or worker protocols.
    """

    @staticmethod
    def execute_move(
        state: AuthoritativeState,
        entity: EntityState, 
        target_pos: Tuple[float, float]
    ) -> EntityUpdate:
        """GRID-BASED AUTHORITATIVE MOVEMENT."""
        from src_v2.engine.movement import MovementSystem
        return MovementSystem.resolve_move(state, entity, target_pos)

    @staticmethod
    def execute_action(
        entity: EntityState, 
        payload: Optional[Dict[str, Any]] = None
    ) -> EntityUpdate:
        """Standard action cost."""
        return EntityUpdate(
            entity_id=entity.id,
            readiness_delta=-100.0
        )

    @staticmethod
    def drain_debt(owner_id: str, profile) -> int:
        """
        Milestone C Law: Authoritative Drain Logic.
        Determines how much work debt is cleared in a single execution unit.
        """
        # owner_id is the subsystem name (e.g. "REPLAY", "KERNEL")
        return -profile.max_worker_count

    @staticmethod
    def get_neighbor_view(
        state: AuthoritativeState,
        subject: EntityState, 
        radius: float
    ) -> List[tuple[int, EntityState]]:
        """
        Produce a deterministic, ID-sorted view of nearby entities.
        Milestone D Law: Views must be bit-identical across parallel executions.
        """
        neighbors = []
        sx, sy = subject.position
        for e_id, ent in state.entities.items():
            if e_id == subject.id:
                continue
            
            ex, ey = ent.position
            dist = ((ex - sx)**2 + (ey - sy)**2)**0.5
            if dist <= radius:
                neighbors.append((e_id, ent))
        
        # Sort by Entity ID for absolute determinism
        neighbors.sort(key=lambda x: x[0])
        return neighbors
