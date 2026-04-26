from __future__ import annotations
from typing import Optional
from src.core.state import EntityState, AuthoritativeState
from src.core.updates import EntityUpdate, InteractionUpdate

class HarvestAction:
    """Action to start harvesting a resource node."""

    @staticmethod
    def start_harvest(
        entity: EntityState, 
        target_node_id: int, 
        state: AuthoritativeState
    ) -> Optional[EntityUpdate]:
        """
        Initialize a harvesting interaction if within proximity and node is active.
        """
        # 1. Proximity and State Check
        node = state.resource_nodes.get(target_node_id)
        if not node:
            return None
            
        if node.remaining_charges <= 0 or node.cooldown_remaining > 0:
            return None
            
        dist = abs(entity.position[0] - node.position[0]) + abs(entity.position[1] - node.position[1])
        if dist > 1.5:
            return None
            
        # 2. Start Channel
        return EntityUpdate(
            entity_id=entity.id,
            interaction=InteractionUpdate(
                target_node_id=target_node_id,
                progress_delta=0.0,
                reset=False
            ),
            property_updates={
                "interaction_kind": "harvest",
                "harvest_duration": float(node.required_ticks)
            }
        )
