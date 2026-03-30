"""RestAction — entity idles and recovers slightly.

Refactored for AOA Stabilization:
- Direct aspect access (combat, mind, progression).
- Removed legacy property shims and StatsProxy dependencies.
- Standardized action delay and HP recovery.
"""

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
        if proposal.verb != ActionType.REST: return False
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
        if not entity: return
        
        # Minor HP recovery on rest
        if entity.combat.hp < entity.combat.max_hp:
            entity.combat.hp = min(entity.combat.hp + 1.0, entity.combat.max_hp)
            
        from src.core.gameplay.attributes import speed_delay
        # Check current AI state from mind.decision aspect
        current_state = entity.mind.decision.ai_state
        action_type = "building" if current_state in RestAction._BUILDING_STATES else "rest"
        
        delay = speed_delay(entity.combat.spd, action_type, entity.interaction.interaction_speed)
        entity.next_act_at += delay
        
        # Recovery (Stamina)
        entity.progression.stamina = min(entity.progression.stamina + 2.0, entity.progression.max_stamina)
        
        # Attribute training
        from src.core.gameplay.attributes import train_attributes
        train_attributes(entity, "rest")
