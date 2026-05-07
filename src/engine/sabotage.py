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
        """
        refined_building_updates = dict(update.building_updates)
        
        for e_id, entity in state.entities.items():
            if not entity.lifecycle.active: continue
            
            ent_upd = update.entity_updates.get(e_id)
            if not ent_upd or not ent_upd.task: continue
            
            # Check for Sabotage Intent (Standardized ENTITY_ACT or Legacy SABOTAGE)
            task_upd = ent_upd.task
            is_sabotage = (task_upd.work_kind_set == "SABOTAGE") or \
                         (task_upd.work_kind_set == "ENTITY_ACT" and task_upd.payload_set.get("action") == "SABOTAGE")
            
            if is_sabotage:
                target_pos = task_upd.payload_set.get("target_pos")
                if not target_pos: continue
                
                # Verify Proximity (Adjacency required for sabotage)
                dx = abs(entity.navigation.position[0] - target_pos[0])
                dy = abs(entity.navigation.position[1] - target_pos[1])
                if dx > 1 or dy > 1:
                    continue # Too far
                
                # Identify Building at target position
                building = next((b for b in state.buildings.values() if b.position == target_pos), None)
                if not building:
                    continue
                
                # Apply Authoritative Damage
                # Standard sabotage tick deals 50 damage
                damage = 50
                build_upd = refined_building_updates.get(building.id, BuildingUpdate(building_id=building.id))
                
                # Calculate resulting state for functionality check
                current_hp_in_tick = building.hp + build_upd.hp_delta
                new_hp = max(0, current_hp_in_tick - damage)
                is_functional = new_hp > 0
                
                refined_building_updates[building.id] = replace(
                    build_upd,
                    hp_delta=build_upd.hp_delta - damage,
                    functional_set=is_functional,
                )
        
        return replace(update, building_updates=refined_building_updates)
