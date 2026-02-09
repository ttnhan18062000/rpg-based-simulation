"""MoveAction — validates and applies movement proposals.

Territory tiles (TOWN, CAMP) are now passable for all factions.
The consequence of entering enemy territory (debuff + alert) is handled
by the WorldLoop after the move is applied.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.core.enums import ActionType
from src.core.models import Vector2

if TYPE_CHECKING:
    from src.core.world_state import WorldState

logger = logging.getLogger(__name__)


class MoveAction:
    """Stateless handler for MOVE proposals."""

    @staticmethod
    def validate(proposal: ActionProposal, world: WorldState, occupied: set[tuple[int, int]]) -> bool:
        if proposal.verb != ActionType.MOVE:
            return False

        entity = world.entities.get(proposal.actor_id)
        if entity is None or not entity.alive:
            return False

        target: Vector2 = proposal.target
        if not world.grid.is_walkable(target):
            logger.debug("Entity %d blocked by terrain at %s", proposal.actor_id, target)
            return False

        if (target.x, target.y) in occupied:
            logger.debug("Entity %d blocked by occupant at %s", proposal.actor_id, target)
            return False

        return True

    @staticmethod
    def apply(proposal: ActionProposal, world: WorldState) -> None:
        target: Vector2 = proposal.target
        old_pos = world.entities[proposal.actor_id].pos if proposal.actor_id in world.entities else None
        world.move_entity(proposal.actor_id, target)
        entity = world.entities.get(proposal.actor_id)
        if entity is not None:
            from src.core.attributes import speed_delay
            spd = entity.effective_spd()
            # Road tiles grant a speed bonus
            if world.grid.is_road(target) or world.grid.is_bridge(target):
                spd = max(spd, int(spd * 1.3))
            delay = speed_delay(spd, "move", entity.stats.interaction_speed)
            # Engagement Lock: fleeing from adjacent hostiles costs double delay
            if entity.engaged_ticks >= 2:
                delay *= 2.0
                entity.engaged_ticks = 0  # reset after paying the penalty
            entity.next_act_at += delay
            # Stamina cost for moving
            entity.stats.stamina = max(0, entity.stats.stamina - 1)
            # Attribute training from movement
            if entity.attributes and entity.attribute_caps:
                from src.core.attributes import train_attributes
                train_attributes(entity.attributes, entity.attribute_caps, "move", stats=entity.stats)
