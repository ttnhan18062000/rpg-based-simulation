"""SleepAction — entity transitions to sleeping state.

Design Note:
- Sets is_sleeping = True.
- Recovery is handled authoritatively by ActionSystem._apply_biological_decay.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src_legacy.actions.base import ActionProposal, RoutineUpdate
from src_legacy.core.models.enums import ActionType, AIState

if TYPE_CHECKING:
    from src_legacy.core.models.world_state import WorldState

logger = logging.getLogger(__name__)

class SleepAction:
    """Stateless handler for SLEEP proposals."""

    @staticmethod
    def validate(proposal: ActionProposal, world: WorldState) -> bool:
        if proposal.verb != ActionType.SLEEP:
            return False
        entity = world.entities.get(proposal.actor_id)
        return entity is not None and entity.combat.alive

    @staticmethod
    def get_updates(proposal: ActionProposal, world: WorldState) -> list[IntentUpdate]:
        """Generate updates for sleeping."""
        updates = []
        entity = world.entities.get(proposal.actor_id)
        if not entity:
            return updates

        # 1. State Transition
        updates.append(RoutineUpdate(
            is_sleeping=True
        ))
        
        # 2. Synchronize AI state
        # Sleeping is a specialized AI state that bypasses normal goal scoring
        proposal.new_ai_state = AIState.SLEEPING
        
        logger.debug(f"Entity {entity.id} began sleeping.")
        return updates
