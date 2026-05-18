from __future__ import annotations
from typing import Optional
from src_legacy.core.state import EntityState, InteractionComponent, AuthoritativeState
from src_legacy.core.updates import EntityUpdate, InteractionUpdate

class LootAction:
    """Action to start looting a ground item or corpse."""

    @staticmethod
    def start_loot(
        entity: EntityState, 
        target_id: int, 
        target_kind: str,
        state: AuthoritativeState
    ) -> Optional[EntityUpdate]:
        """
        Initialize a looting interaction if within proximity.
        target_kind: 'ground_item' or 'corpse'
        """
        # 1. Proximity Check
        target_pos = None
        if target_kind == "ground_item":
            target = state.ground_items.get(target_id)
            if target: target_pos = target.position
        elif target_kind == "corpse":
            target = state.corpses.get(target_id)
            if target: target_pos = target.position
            
        if not target_pos:
            return None
            
        dist = abs(entity.position[0] - target_pos[0]) + abs(entity.position[1] - target_pos[1])
        if dist > 1.5:
            return None
            
        # 2. Start Channel
        # Default loot time is 10 ticks (0.5s)
        return EntityUpdate(
            entity_id=entity.id,
            interaction=InteractionUpdate(
                target_node_id=target_id,
                progress_delta=0.0, # Will be incremented by LootSystem
                reset=False
            ),
            property_updates={"interaction_kind": target_kind}
        )
