# Compliance IDs: TOWN-113, TOWN-116, TOWN-117, TOWN-118
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
        
        from src.engine.spatial_query import SpatialQueryService
        
        # Optimization: Only process entities that moved or proposed navigation changes
        # Logic ID: PERF-006 (Dirty Entity Tracking)
        relevant_ids_raw = update.dirty_set.movement_entities | update.dirty_set.strategic_entities if update.dirty_set else state.entities.keys()
        relevant_ids = sorted(list(relevant_ids_raw))
        
        for e_id in relevant_ids:
            entity = state.entities.get(e_id)
            if not entity or not entity.lifecycle.active:
                continue
            
            ent_upd = refined_entity_updates.get(e_id)
            target_pos = entity.navigation.target
            if ent_upd and ent_upd.navigation and ent_upd.navigation.target_set:
                target_pos = ent_upd.navigation.target_set
            
            if target_pos:
                # Use optimized spatial lookups
                # Logic ID: PERF-007 (Spatial Query Service)
                target_node = SpatialQueryService.get_node_at(state, target_pos)
                target_ground = SpatialQueryService.get_ground_item_at(state, target_pos)
                target_corpse = SpatialQueryService.get_corpse_at(state, target_pos)
                
                final_target_id = None
                if target_node:
                    final_target_id = target_node.id
                elif target_ground:
                    final_target_id = target_ground.id
                elif target_corpse:
                    final_target_id = target_corpse.id
                
                if final_target_id is not None:
                    ent_upd = ent_upd or EntityUpdate(entity_id=e_id)
                    current_int = ent_upd.interaction or InteractionUpdate()
                    if not current_int.reset:
                        p_delta = current_int.progress_delta if current_int.progress_delta > 0 else 1
                        refined_entity_updates[e_id] = replace(ent_upd,
                            interaction=replace(current_int, target_node_id=final_target_id, progress_delta=p_delta)
                        )
        
        return replace(update, entity_updates=refined_entity_updates)
