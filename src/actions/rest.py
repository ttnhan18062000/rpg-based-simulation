"""RestAction — entity idles and recovers slightly."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.actions.base import ActionProposal
from src.core.models.enums import AIState, ActionType

if TYPE_CHECKING:
    from src.core.models.world_state import WorldState

logger = logging.getLogger(__name__)


class RestAction:
    """Stateless handler for REST proposals."""

    @staticmethod
    def validate(proposal: ActionProposal, world: WorldState) -> bool:
        if proposal.verb != ActionType.REST:
            return False
        entity = world.entities.get(proposal.actor_id)
        return entity is not None and entity.combat.alive

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
        if entity.stats.combat.hp < entity.stats.combat.max_hp:
            entity.stats.combat.hp = min(entity.stats.combat.hp + 1, entity.stats.combat.max_hp)
        from src.core.gameplay.attributes import speed_delay
        action_type = "building" if entity.mind.ai_state in RestAction._BUILDING_STATES else "rest"
        entity.next_act_at += speed_delay(entity.stats.combat.spd, action_type, entity.stats.interaction_speed)
