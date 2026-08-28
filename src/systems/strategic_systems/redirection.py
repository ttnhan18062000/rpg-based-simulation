from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple
from dataclasses import replace

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate, EntityUpdate, StrategicUpdate
from src.core.movement_modes import MovementMode
from src.core.strategic import ProjectStatus, ObjectiveStatus
from src.core.updates import EntityUpdate, NavigationUpdate, StrategicUpdate, InteractionUpdate
from src.engine.cadence import SystemCadence
from src.systems.strategic_systems.town_targeting import nearest_town_tile

class StrategicRedirectionSystem:
    """
    Mechanistic bridge between strategic blockers and navigation targets.
    Closes the loop for resource progression proof.
    """

    @staticmethod
    def enforce(state: AuthoritativeState, update: StateUpdate, cadence: SystemCadence = None) -> StateUpdate:
        """
        Scan entities for blockers and propose navigation targets to resolve them.
        """
        from src.engine.cadence import should_run
        cadence = cadence or SystemCadence()

        refined_entity_updates = dict(update.entity_updates)

        # Optimization: Only process entities that had strategic changes or are relevant for redirection
        # Logic ID: PERF-006 (Dirty Entity Tracking)
        from src.core.dirty import get_relevant_entity_ids
        relevant_ids = get_relevant_entity_ids(state, update, "redirection")
        
        # Sort for determinism
        entity_ids = sorted(list(relevant_ids))
        for e_id in entity_ids:
            if not should_run(state.tick, e_id, cadence.strategic_intelligence):
                continue
                
            entity = state.entities[e_id]
            if not entity.lifecycle.active:
                continue
                
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            strat_up = ent_upd.strategic or StrategicUpdate()
            has_nav_update = ent_upd.navigation and ent_upd.navigation.target_set is not None
            
            # (Noisy debug logging removed)
            
            # Check for active project
            current_project_id = strat_up.current_project_id_set if strat_up.current_project_id_set is not None else entity.strategic.current_project_id
            
            
            # Check state AND proposed additions in this tick
            removals = []
            additions = []
            if ent_upd.strategic:
                 removals = ent_upd.strategic.blockers_remove
                 additions = list(ent_upd.strategic.blockers_add_or_update)
            
            active_blockers = [
                b
                for b_id, b in entity.strategic.blockers.items()
                if b_id not in removals and not b.resolved
            ]
            active_blockers.extend(
                b
                for b in additions
                if b.id not in removals and not b.resolved
            )
            
            # 2. Case: Blocked on Materials
            mat_blockers = [
                b
                for b in active_blockers
                if b.kind == "material" and not b.resolved
            ]
            
            if mat_blockers:
                # Seek a lead for the first material blocker
                target_mat = mat_blockers[0].subject
                match_lead = None
                for lead in entity.strategic.leads.values():
                    if lead.subject == target_mat and lead.kind == 'location':
                        match_lead = lead
                        break
                
                if match_lead:
                    # Found a way to resolve! Set target.
                    try:
                        coords = tuple(map(float, match_lead.detail.split(',')))
                        has_nav_update = True
                        
                        if entity.navigation.target != coords:
                             existing_nav = ent_upd.navigation or NavigationUpdate()
                             new_nav = replace(existing_nav, target_set=coords)
                             
                             ent_upd = replace(ent_upd, 
                                 navigation=new_nav,
                                 interaction=InteractionUpdate(reset=True)
                             )
                             refined_entity_updates[e_id] = ent_upd
                    except (ValueError, AttributeError):
                        pass # Vague or invalid lead
            
            # 2.5. Case: Active Objective Target (RPG-STRAT-010)
            if not has_nav_update and current_project_id:
                project = entity.strategic.projects.get(current_project_id)
                if project and project.status == ProjectStatus.ACTIVE:
                    obj_id = strat_up.current_objective_id_set if strat_up.current_objective_id_set is not None else project.active_objective_id
                    active_obj = next((o for o in project.objectives if o.id == obj_id), None)
                    if active_obj and active_obj.status == ObjectiveStatus.ACTIVE:
                        # If the objective has a target (e.g. harvesting node)
                        target_pos = getattr(active_obj, 'target_position', None)
                        if target_pos:
                             has_nav_update = True
                             if entity.navigation.target != target_pos:
                                 existing_nav = ent_upd.navigation or NavigationUpdate()
                                 new_nav = replace(existing_nav, target_set=target_pos)
                                 ent_upd = replace(ent_upd, navigation=new_nav)
                                 refined_entity_updates[e_id] = ent_upd
            
            # 3. Case: Return to Town (Fallback if no blockers or no leads)
            # Only if no navigation target was set in this tick and we have items
            if not has_nav_update:
                has_items = len(entity.inventory.items) > 0
                if has_items and entity.navigation.position != (0.0, 0.0):
                    nearest = nearest_town_tile(state.town_tiles, entity.navigation.position)
                    target_coords = nearest if nearest is not None else state.town_center

                    if entity.navigation.target != target_coords:
                        existing_nav = ent_upd.navigation or NavigationUpdate()
                        new_nav = replace(existing_nav, 
                            target_set=target_coords,
                            movement_mode_set=MovementMode.REGROUP
                        )
                        ent_upd = replace(ent_upd, 
                            navigation=new_nav,
                            interaction=InteractionUpdate(reset=True)
                        )
                        refined_entity_updates[e_id] = ent_upd
                        has_nav_update = True

        return replace(update, entity_updates=refined_entity_updates)
