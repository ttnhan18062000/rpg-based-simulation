from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, List, Dict

if TYPE_CHECKING:
    from src_legacy.core.state import AuthoritativeState
    from src_legacy.core.updates import StateUpdate

class WorldLifecycleSystem:
    """
    Authoritative logic for environment evolution: Resource recharge and Cleanup.
    Law: The world must evolve deterministically via passive tick rules.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Handle resource node regeneration and cleanup of dead entities/corpses.
        """
        refined_node_updates = dict(update.node_updates)
        corpses_remove = list(update.corpses_remove)
        entities_remove = list(update.entities_remove)
        
        # 1. Resource Regeneration
        # HarvestSystem handles the countdown, WorldLifecycleSystem handles the RECHARGE.
        for node in state.resource_nodes.values():
            n_id = node.id
            node_upd = refined_node_updates.get(n_id)
            
            current_cooldown = node.cooldown_remaining
            if node_upd and node_upd.cooldown_set is not None:
                current_cooldown = node_upd.cooldown_set
                
            # If cooldown reaches zero and charges are depleted, recharge
            if current_cooldown == 0 and node.remaining_charges < node.max_charges:
                from src_legacy.core.updates import ResourceNodeUpdate
                if node_upd:
                    # Increment charges delta to reach max
                    refined_node_updates[n_id] = replace(node_upd,
                        charges_delta=node_upd.charges_delta + (node.max_charges - node.remaining_charges)
                    )
                else:
                    refined_node_updates[n_id] = ResourceNodeUpdate(
                        node_id=n_id,
                        charges_delta=node.max_charges - node.remaining_charges
                    )
        
        # 2. Corpse Decay
        for corpse_id, corpse in state.corpses.items():
            if state.tick >= corpse.decay_tick:
                corpses_remove.append(corpse_id)
                
        refined_entity_updates = dict(update.entity_updates)
        ground_items_remove = list(update.ground_items_remove)
        
        # 3. Inactive Entity Cleanup
        # Entities marked active=False by LifecycleSystem should be reaped.
        for e_id, entity in state.entities.items():
            if not entity.active and e_id not in entities_remove:
                entities_remove.append(e_id)
            
            # 4. Stat Decay (Inactivity Penalty)
            # Law: Entities that idle for too long (1000+ ticks) suffer attribute decay.
            if entity.active and entity.lifecycle.age_ticks % 1000 == 0 and entity.lifecycle.age_ticks > 0:
                # Check if entity is actually idling (no project or project is 'idling')
                if not entity.strategic.current_project_id:
                    from src_legacy.core.updates import AttributeUpdate, EntityUpdate
                    ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                    attr_upd = ent_upd.attributes or AttributeUpdate()
                    # Decay random physical stat
                    refined_entity_updates[e_id] = replace(ent_upd,
                        attributes=replace(attr_upd, strength_delta=attr_upd.strength_delta - 1)
                    )
        
        # 5. Ground Item Decay
        # Items dropped on the ground decay after 500 ticks. We'll use a hack to track age by using state.tick - 500
        # Actually, let's just clear items that have been on the ground too long if we had a spawn tick, 
        # but since GroundItemState doesn't have a spawn_tick, we can't accurately decay them yet unless we add it.
        # For now, we will just pass.
        
        return replace(update,
            node_updates=refined_node_updates,
            corpses_remove=corpses_remove,
            entities_remove=entities_remove,
            entity_updates=refined_entity_updates
        )
