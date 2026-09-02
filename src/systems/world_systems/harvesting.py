# Compliance IDs: TOWN-073
from __future__ import annotations
from src.core.state import AuthoritativeState, ItemStack
from src.core.updates import StateUpdate, EntityUpdate, InteractionUpdate, InventoryUpdate, ResourceNodeUpdate

class HarvestSystem:
    """Processes harvesting progress, yields, and node depletion."""

    @staticmethod
    def update(state: AuthoritativeState) -> StateUpdate:
        entity_updates = {}
        node_updates = {}
        
        # 1. Process Harvesting Entities
        for entity in state.entities.values():
            if not entity.interaction or entity.interaction.target_node_id is None:
                continue
                
            if entity.interaction.kind != "harvest":
                continue
                
            node_id = entity.interaction.target_node_id
            node = state.resource_nodes.get(node_id)
            
            # Proximity Validation
            if not node or node.remaining_charges <= 0:
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(reset=True)
                )
                continue
                
            dist = abs(entity.navigation.position[0] - node.position[0]) + abs(entity.navigation.position[1] - node.position[1])
            if dist > 1.5:
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(reset=True)
                )
                continue
                
            # Progress
            new_progress = entity.interaction.progress + 1.0
            required = entity.identity.properties.get("harvest_duration", 10.0)
            
            if new_progress >= required:
                # COMPLETION (Proposed intent for refinement)
                from src.core.updates import ResourceTransferIntent
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(reset=True),
                    resource_transfers=[ResourceTransferIntent(
                        source_id=node_id,
                        source_kind="NODE",
                        items_add=[ItemStack(item_id=node.yields_item, quantity=1)],
                        transfer_kind="HARVEST"
                    )]
                )
            else:
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(progress_delta=1.0)
                )
                
        # 2. Process Node Cooldowns
        for node in state.resource_nodes.values():
            if node.cooldown_remaining > 0:
                # Decrement cooldown
                current_upd = node_updates.get(node.id)
                if current_upd:
                    node_updates[node.id] = ResourceNodeUpdate(
                        node_id=node.id,
                        charges_delta=current_upd.charges_delta,
                        cooldown_set=max(0, node.cooldown_remaining - 1)
                    )
                else:
                    node_updates[node.id] = ResourceNodeUpdate(
                        node_id=node.id,
                        cooldown_set=max(0, node.cooldown_remaining - 1)
                    )
                    
        return StateUpdate(
            entity_updates=entity_updates,
            node_updates=node_updates
        )
