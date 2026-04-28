from __future__ import annotations
from typing import Dict, List
from src.core.state import AuthoritativeState, EntityState, ChestState, ItemStack
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate, InventoryUpdate, ChestUpdate

class ChestSystem:
    """Processes treasure chest interactions and respawn logic."""

    @staticmethod
    def update(state: AuthoritativeState) -> StateUpdate:
        entity_updates = {}
        chest_updates = {}
        
        # 1. Handle Interactions
        for entity in state.entities.values():
            if not entity.interaction or entity.interaction.target_node_id is None:
                continue
                
            if entity.properties.get("interaction_kind") != "chest":
                continue
                
            chest_id = entity.interaction.target_node_id
            chest = state.chests.get(chest_id)
            
            if not chest or chest.cooldown_remaining > 0:
                # Chest gone or empty/cooldown
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(reset=True)
                )
                continue
                
            # Proximity
            dist = abs(entity.position[0] - chest.position[0]) + abs(entity.position[1] - chest.position[1])
            if dist > 1.5:
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(reset=True)
                )
                continue
                
            # Progress
            new_progress = entity.interaction.progress + 1.0
            if new_progress >= 10.0: # 10 ticks to open
                # SUCCESS
                chest_updates[chest_id] = ChestUpdate(
                    chest_id=chest_id,
                    items_set=[], # Empty it
                    cooldown_set=chest.respawn_tick
                )
                
                from src.core.updates import ResourceTransferIntent
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(reset=True),
                    resource_transfers=[ResourceTransferIntent(
                        source_id=chest_id,
                        source_kind="CHEST",
                        items_add=chest.items,
                        transfer_kind="LOOT"
                    )]
                )
            else:
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(progress_delta=1.0)
                )
                
        # 2. Handle Cooldowns
        for chest in state.chests.values():
            if chest.cooldown_remaining > 0 and chest.id not in chest_updates:
                chest_updates[chest.id] = ChestUpdate(
                    chest_id=chest.id,
                    cooldown_set=chest.cooldown_remaining - 1
                )
                
        return StateUpdate(
            entity_updates=entity_updates,
            chest_updates=chest_updates
        )
