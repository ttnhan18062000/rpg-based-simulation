"""RestAction — entity idles and recovers slightly."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.core.enums import ActionType

if TYPE_CHECKING:
    from src.core.world_state import WorldState

logger = logging.getLogger(__name__)


class RestAction:
    """Stateless handler for REST proposals."""

    @staticmethod
    def validate(proposal: ActionProposal, world: WorldState) -> bool:
        if proposal.verb != ActionType.REST:
            return False
        entity = world.entities.get(proposal.actor_id)
        return entity is not None and entity.alive

    @staticmethod
    def apply(proposal: ActionProposal, world: WorldState) -> None:
        entity = world.entities.get(proposal.actor_id)
        if entity is None:
            return
        # Minor HP recovery on rest
        if entity.stats.hp < entity.stats.max_hp:
            entity.stats.hp = min(entity.stats.hp + 1, entity.stats.max_hp)
        from src.core.attributes import speed_delay
        entity.next_act_at += speed_delay(entity.stats.spd, "rest", entity.stats.interaction_speed)
