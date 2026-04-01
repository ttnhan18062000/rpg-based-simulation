"""MoveAction — validates and applies movement proposals.

Refactored for AOA Stabilization:
- Direct aspect access (spatial, combat, progression).
- Removed legacy property shims and StatsProxy dependencies.
- Standardized action delay and stamina costs.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src.actions.base import ActionProposal
from src.core.models.enums import ActionType
from src.core.models import Vector2

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState

logger = logging.getLogger(__name__)

class MoveAction:
    """Stateless handler for MOVE proposals."""

    @staticmethod
    def validate(proposal: ActionProposal, world: WorldState, occupied: set[tuple[int, int]]) -> bool:
        if proposal.verb != ActionType.MOVE: return False
        entity = world.entities.get(proposal.actor_id)
        if not entity or not entity.combat.alive: return False
        
        target: Vector2 = proposal.target
        if not world.grid.is_walkable(target): return False
        
        # O(1) Check: Is anyone already there? (AOA Phase 6)
        if world.is_occupied(target): return False
        
        # Set Check: Did anyone ELSE move there this tick?
        if (target.x, target.y) in occupied: return False
        
        return True

    @staticmethod
    def apply(proposal: ActionProposal, world: WorldState) -> None:
        entity = world.entities.get(proposal.actor_id)
        if not entity: return
        
        target: Vector2 = proposal.target
        world.move_entity(proposal.actor_id, target)
