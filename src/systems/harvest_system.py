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
                
            if entity.properties.get("interaction_kind") != "harvest":
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
                
            dist = abs(entity.position[0] - node.position[0]) + abs(entity.position[1] - node.position[1])
            if dist > 1.5:
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    interaction=InteractionUpdate(reset=True)
                )
                continue
                
            # Progress
            new_progress = entity.interaction.progress + 1.0
            required = entity.properties.get("harvest_duration", 10.0)
            
            if new_progress >= required:
                # COMPLETION
                yield_item = node.yields_item
                    
                entity_updates[entity.id] = EntityUpdate(
                    entity_id=entity.id,
                    inventory=InventoryUpdate(items_add=[ItemStack(yield_item, 1)]),
                    interaction=InteractionUpdate(reset=True)
                )
                
                # Deplete node
                new_charges = node.remaining_charges - 1
                node_upd = ResourceNodeUpdate(
                    node_id=node_id,
                    charges_delta=-1
                )
                if new_charges <= 0:
                    node_upd = ResourceNodeUpdate(
                        node_id=node_id,
                        charges_delta=-1,
                        cooldown_set=node.respawn_cooldown
                    )
                node_updates[node_id] = node_upd
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
