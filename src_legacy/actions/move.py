"""MoveAction — validates and applies movement proposals.

Refactored for AOA Stabilization:
- Direct aspect access (spatial, combat, progression).
- Removed legacy property shims and StatsProxy dependencies.
- Standardized action delay and stamina costs.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src_legacy.actions.base import ActionProposal
from src_legacy.core.models.enums import ActionType
from src_legacy.core.models import Vector2

if TYPE_CHECKING:
    from src_legacy.core.models.world_state import WorldState

logger = logging.getLogger(__name__)

class MoveAction:
    """Stateless handler for MOVE proposals."""

    @staticmethod
    def validate(proposal: ActionProposal, world: WorldState, occupied: set[tuple[int, int]]) -> bool:
        if proposal.verb != ActionType.MOVE: return False
        entity = world.entities.get(proposal.actor_id)
        if not entity or not entity.combat.alive: return False
        
        target: Vector2 = proposal.target
        from src_legacy.core.models.reason_codes import ActionReason, ReasonCode
        
        if not world.grid.is_walkable(target): 
            proposal.reason = ActionReason(code=ReasonCode.PATH_NOT_FOUND, metadata={"detail": "Terrain blocked"}, is_rejection=True)
            return False
        
        # O(1) Check: Is anyone already there? (AOA Phase 6)
        from src_legacy.core.logic.legality_service import LegalityService
        success, reason = LegalityService.verify_occupancy(target, world)
        if not success: 
            proposal.reason = reason
            return False
        
        # Set Check: Did anyone ELSE move there this tick?
        if (target.x, target.y) in occupied: 
            proposal.reason = ActionReason(code=ReasonCode.OCCUPANCY_VIOLATION, metadata={"detail": "Position claimed this tick"}, is_rejection=True)
            return False
        
        return True

    @staticmethod
    def apply(proposal: ActionProposal, world: WorldState) -> None:
        """AOA Stabilization: Emit NavigationUpdate for authoritative application."""
        entity = world.entities.get(proposal.actor_id)
        if not entity: return
        
        target: Vector2 = proposal.target
        # world.move_entity(proposal.actor_id, target) # DEPRECATED: Direct Mutation
        
        from src_legacy.actions.base import NavigationUpdate, SpatialUpdate
        proposal.updates.append(NavigationUpdate(target_pos=target))
        proposal.updates.append(SpatialUpdate(new_pos=target, moved_this_tick=True))
