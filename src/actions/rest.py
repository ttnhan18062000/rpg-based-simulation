"""RestAction — entity idles and recovers slightly."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.core.enums import AIState, ActionType

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

    # AI states that represent building interactions (higher delay)
    _BUILDING_STATES = frozenset({
        AIState.VISIT_SHOP, AIState.VISIT_BLACKSMITH, AIState.VISIT_GUILD,
        AIState.VISIT_CLASS_HALL, AIState.VISIT_INN, AIState.VISIT_HOME,
    })

    @staticmethod
    def apply(proposal: ActionProposal, world: WorldState) -> None:
        entity = world.entities.get(proposal.actor_id)
        if entity is None:
            return
        # Minor HP recovery on rest
        if entity.stats.hp < entity.stats.max_hp:
            entity.stats.hp = min(entity.stats.hp + 1, entity.stats.max_hp)
        from src.core.attributes import speed_delay
        action_type = "building" if entity.ai_state in RestAction._BUILDING_STATES else "rest"
        entity.next_act_at += speed_delay(entity.stats.spd, action_type, entity.stats.interaction_speed)
