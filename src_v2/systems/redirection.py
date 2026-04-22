from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple
from dataclasses import replace

if TYPE_CHECKING:
    from src_v2.core.state import AuthoritativeState, EntityState
    from src_v2.core.updates import StateUpdate, EntityUpdate

class StrategicRedirectionSystem:
    """
    Mechanistic bridge between strategic blockers and navigation targets.
    Closes the loop for resource progression proof.
    """

    @staticmethod
    def enforce(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Scan entities for blockers and propose navigation targets to resolve them.
        """
        from src_v2.core.updates import EntityUpdate, NavigationUpdate
        
        refined_entity_updates = dict(update.entity_updates)
        
        for e_id, entity in state.entities.items():
            if not entity.active:
                continue
                
            ent_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            
            # 1. Identify active blockers
            # Logic: If item added this tick, the blocker might be removed by StrategicIntelligenceSystem.
            # However, we are running in the SAME resolution phase. 
            # StrategicIntelligenceSystem.resolve_blockers runs before us in the Kernel.
            
            # Check state AND proposed additions in this tick
            additions = []
            removals = []
            if ent_upd.strategic:
                 removals = ent_upd.strategic.blockers_remove
                 additions = list(ent_upd.strategic.blockers_add_or_update)
            
            active_blockers = [b for bId, b in entity.strategic.blockers.items() if bId not in removals]
            active_blockers.extend(additions)
            
            # 2. Case: Blocked on Materials
            mat_blockers = [b for b in active_blockers if b.kind == 'material']
            
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
                    # Detail usually contains "x,y" for location leads in Milestone 3/4
                    try:
                        coords = tuple(map(float, match_lead.detail.split(',')))
                        
                        existing_nav = ent_upd.navigation or NavigationUpdate()
                        if entity.navigation.target != coords:
                             new_nav = replace(existing_nav, target_set=coords)
                             refined_entity_updates[e_id] = replace(ent_upd, navigation=new_nav)
                    except (ValueError, AttributeError):
                        pass # Vague or invalid lead
            
            # 3. Case: No blockers but has items (Return to Town)
            else:
                has_items = bool(entity.inventory.items)
                if ent_upd.inventory:
                     if ent_upd.inventory.items_added or entity.inventory.items:
                          has_items = True
                
                if has_items:
                    # If not already at town
                    tile_pos = (int(entity.position[0]), int(entity.position[1]))
                    if tile_pos not in state.town_tiles:
                        # Redirection to town
                        # We pick any town tile for simplicity in proof
                        if state.town_tiles:
                            town_pos = list(state.town_tiles)[0]
                            town_coords = (float(town_pos[0]), float(town_pos[1]))
                            
                            existing_nav = ent_upd.navigation or NavigationUpdate()
                            if entity.navigation.target != town_coords:
                                 new_nav = replace(existing_nav, target_set=town_coords)
                                 refined_entity_updates[e_id] = replace(ent_upd, navigation=new_nav)

        return replace(update, entity_updates=refined_entity_updates)
