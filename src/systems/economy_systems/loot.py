# Compliance IDs: TOWN-009
from __future__ import annotations
from typing import List
from src.core.state import AuthoritativeState, EntityState, ItemStack
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate, InventoryUpdate

class LootSystem:
    """Processes looting progress and performs authoritative item handoffs."""

    @staticmethod
    def update(state: AuthoritativeState) -> StateUpdate:
        entity_updates = {}
        ground_items_remove = []
        corpses_remove = []
        
        for entity in state.entities.values():
            if not entity.interaction or entity.interaction.target_node_id is None:
                continue
                
            interaction_kind = entity.identity.properties.get("interaction_kind")
            if interaction_kind not in ["ground_item", "corpse"]:
                continue
                
            target_id = entity.interaction.target_node_id
            
            # 1. Proximity Validation (Continuous)
            target_pos = None
            if interaction_kind == "ground_item":
                target = state.ground_items.get(target_id)
                if target: target_pos = target.position
            else:
                target = state.corpses.get(target_id)
                if target: target_pos = target.position
                
            if not target_pos:
                # Target gone
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(reset=True)
                )
                continue
                
            dist = abs(entity.navigation.position[0] - target_pos[0]) + abs(entity.navigation.position[1] - target_pos[1])
            if dist > 1.5:
                # Interrupted by distance
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(reset=True)
                )
                continue
                
            # 2. Progress Increment
            # Logic ID: TOWN-009 (Looting progress is authoritative)
            new_progress = entity.interaction.progress + 1.0
            
            # 3. Completion Check (required_ticks default to 10 if not set)
            required = 10.0
            if new_progress >= required:
                # Logic ID: TOWN-009 (Looting completion triggers intent)
                # AUTHORITATIVE HANDOFF (Proposed intent for refinement)
                items_to_add = []
                source_kind = ""
                if interaction_kind == "ground_item":
                    items_to_add = [ItemStack(target.item_id, target.quantity)]
                    source_kind = "GROUND_ITEM"
                else:
                    items_to_add = target.items
                    source_kind = "CORPSE"
                
                from src.core.updates import ResourceTransferIntent
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(reset=True),
                    resource_transfers=[ResourceTransferIntent(
                        source_id=target_id,
                        source_kind=source_kind,
                        items_add=items_to_add,
                        transfer_kind="LOOT"
                    )]
                )
            else:
                # Continue progress
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(progress_delta=1.0)
                )
                
        return StateUpdate(
            entity_updates=entity_updates,
            ground_items_remove=ground_items_remove,
            corpses_remove=corpses_remove
        )
