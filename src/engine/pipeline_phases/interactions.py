from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate

class InteractionPhase:
    """
    Pipeline phase responsible for routing interaction intents based on entity position and targets.
    """
    @staticmethod
    def route_interaction_intent(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        from src.core.updates import InteractionUpdate, EntityUpdate
        refined_entity_updates = dict(update.entity_updates)
        
        for e_id, entity in state.entities.items():
            if not entity.lifecycle.active:
                continue
            
            # Identify if entity is at a location that triggers automatic interaction
            # Or if they have an explicit target set
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            target_pos = entity.navigation.target
            if ent_upd.navigation and ent_upd.navigation.target_set:
                target_pos = ent_upd.navigation.target_set
            
            if target_pos:
                # Find if any node is at the target
                target_node = next((n for n in state.resource_nodes.values() if n.position == target_pos), None)
                target_ground = next((g for g in state.ground_items.values() if g.position == target_pos), None)
                target_corpse = next((c for c in state.corpses.values() if c.position == target_pos), None)
                
                final_target_id = None
                if target_node:
                    final_target_id = target_node.id
                elif target_ground:
                    final_target_id = target_ground.id
                elif target_corpse:
                    final_target_id = target_corpse.id
                
                if final_target_id is not None:
                    current_int = ent_upd.interaction or InteractionUpdate()
                    if not current_int.reset:
                        p_delta = current_int.progress_delta if current_int.progress_delta > 0 else 1
                        refined_entity_updates[e_id] = replace(ent_upd,
                            interaction=replace(current_int, target_node_id=final_target_id, progress_delta=p_delta)
                        )
        
        return replace(update, entity_updates=refined_entity_updates)
