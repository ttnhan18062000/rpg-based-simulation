"""EatAction — entity consumes a food item to reduce hunger.

Design Note:
- Entities must have a CONSUMABLE item in their inventory.
- Consumption reduces hunger_level based on the item's hunger_reduction property.
- If no item is specified in metadata, the first available consumable with hunger_reduction is used.
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src_legacy.actions.base import ActionProposal, RoutineUpdate, ProgressionUpdate, IntentUpdate
from src_legacy.core.models.enums import ActionType

from src_legacy.core.gameplay.items.item_registry import ITEM_REGISTRY
from src_legacy.core.models.world_state import WorldState

logger = logging.getLogger(__name__)

class EatAction:
    """Stateless handler for EAT proposals."""

    @staticmethod
    def validate(proposal: ActionProposal, world: WorldState) -> bool:
        if proposal.verb != ActionType.EAT:
            return False
            
        entity = world.entities.get(proposal.actor_id)
        if not entity or not entity.combat.alive:
            return False
            
        # Optimization: Validate that they have at least one consumable item
        # if none is explicitly targeted.
        if not entity.inventory.items:
            return False
            
        return True

    @staticmethod
    def get_updates(proposal: ActionProposal, world: WorldState) -> list[IntentUpdate]:
        """Generate updates for food consumption."""
        updates: list[IntentUpdate] = []
        entity = world.entities.get(proposal.actor_id)
        if not entity:
            return updates

        item_id = proposal.metadata.get("item_id")
        
        # 1. Authoritative Item Validation
        if not item_id or item_id not in entity.inventory.items:
            # Fallback: Find any food item in inventory
            food_item = None
            for iid in entity.inventory.items:
                template = ITEM_REGISTRY.get(iid)
                if template and template.hunger_reduction > 0:
                    food_item = iid
                    break
            
            if not food_item:
                logger.warning(f"Entity {entity.id} attempted to eat but has no food.")
                return updates
            item_id = food_item

        # 2. Process Consumption
        template = ITEM_REGISTRY.get(item_id)
        hunger_reduction = template.hunger_reduction if template else 0.2
        
        # 3. Emit Updates
        # Hunger reduction
        updates.append(RoutineUpdate(
            hunger_delta=-hunger_reduction
        ))
        
        # Persistence: Remove item from inventory
        updates.append(ProgressionUpdate(
            inventory_remove=[item_id]
        ))
        
        # 4. Optional: HP Recovery for high quality food
        if hunger_reduction > 0.4:
            updates.append(ProgressionUpdate(
                hp_delta=5
            ))

        # Note: delay calculation moved into ActionSystem's act_duration for consistency
        
        logger.debug(f"Entity {entity.id} ate {template.name if template else item_id}, reducing hunger by {hunger_reduction}.")
        return updates
