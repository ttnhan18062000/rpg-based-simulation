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
        entity: EntityState, 
        target_pos: Tuple[float, float]
    ) -> EntityUpdate:
        """Clamped step movement towards target."""
        pos = entity.position
        
        # Calculate vector
        dx = target_pos[0] - pos[0]
        dy = target_pos[1] - pos[1]
        dist = (dx**2 + dy**2)**0.5
        
        max_step = 1.0 # Law: Static max step in baseline
        if dist > max_step:
            fx = dx / dist * max_step
            fy = dy / dist * max_step
            new_pos = (pos[0] + fx, pos[1] + fy)
        else:
            new_pos = (target_pos[0], target_pos[1])
            
        return EntityUpdate(
            entity_id=entity.id,
            new_position=new_pos,
            readiness_delta=-50.0 # Movement Cost Law
        )

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
