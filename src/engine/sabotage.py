# src/engine/sabotage.py
# Phase 8 Implementation: Handles Infrastructure Damage and Service Disruption (LEG-RPG-001/006).
from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING
from src.core.updates import BuildingUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate

class BuildingSabotageSystem:
    """
    Law: Entities can damage town infrastructure (LEG-RPG-001/006).
    Sabotaged buildings lose functionality, impacting regional services.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Handle SABOTAGE intents directed at buildings.
        Optimized: Iterate over entity updates only.
        """
        refined_building_updates = dict(update.building_updates)
        from src.engine.spatial_query import SpatialQueryService
        
        for e_id, ent_upd in update.entity_updates.items():
            if not ent_upd.task: continue
            
            entity = state.entities.get(e_id)
            if not entity or not entity.lifecycle.active: continue
            
            # Check for Sabotage Intent
            task_upd = ent_upd.task
            is_sabotage = (task_upd.work_kind_set == "SABOTAGE") or \
                         (task_upd.work_kind_set == "ENTITY_ACT" and task_upd.payload_set.get("action") == "SABOTAGE")
            
            if is_sabotage:
                target_pos = task_upd.payload_set.get("target_pos")
                if not target_pos: continue
                
                # Verify Proximity
                dx = abs(entity.navigation.position[0] - target_pos[0])
                dy = abs(entity.navigation.position[1] - target_pos[1])
                if dx > 1 or dy > 1:
                    reason = "SABOTAGE_OUT_OF_RANGE"
                    new_rejections_delta = dict(update.rejections_delta)
                    new_rejections_delta[reason] = new_rejections_delta.get(reason, 0) + 1
                    update = replace(update, rejections_delta=new_rejections_delta)
                    continue
                
                # Identify Building via lookup
                building = SpatialQueryService.get_building_at(state, target_pos)
                if not building:
                    reason = "SABOTAGE_NO_TARGET"
                    new_rejections_delta = dict(update.rejections_delta)
                    new_rejections_delta[reason] = new_rejections_delta.get(reason, 0) + 1
                    update = replace(update, rejections_delta=new_rejections_delta)
                    continue
                
                damage = 50
                build_upd = refined_building_updates.get(building.id, BuildingUpdate(building_id=building.id))
                
                new_hp = max(0, building.hp + build_upd.hp_delta - damage)
                refined_building_updates[building.id] = replace(
                    build_upd,
                    hp_delta=build_upd.hp_delta - damage,
                    functional_set=(new_hp > 0),
                )
        
        return replace(update, building_updates=refined_building_updates)
