from __future__ import annotations
from typing import Dict, List, Optional
from src_v2.core.state import EntityState
from src_v2.core.updates import StrategicUpdate, InventoryUpdate
from src_v2.core.strategic import BlockerState, LeadState

class StrategicIntelligenceSystem:
    """
    Analyzes character outcomes to generate or resolve strategic markers.
    FROZEN (Resource Phase 5 Milestone 3)
    """

    @staticmethod
    def generate_crafting_blockers(
        entity: EntityState,
        recipe_mats: Dict[str, int],
        gold_cost: int
    ) -> StrategicUpdate:
        """
        Produce a StrategicUpdate containing blockers for missing requirements.
        """
        blockers = []
        inv = entity.inventory
        
        # 1. Look for missing materials
        for mat_id, needed in recipe_mats.items():
            have = inv.items.count(mat_id)
            if have < needed:
                blockers.append(BlockerState(
                    id=f"blocker_mat_{mat_id}",
                    kind="material",
                    subject=mat_id,
                    severity=min(1.0, (needed - have) / needed)
                ))
        
        # 2. Look for missing gold
        if inv.gold < gold_cost:
            blockers.append(BlockerState(
                id="blocker_gold",
                kind="material",
                subject="gold",
                severity=min(1.0, (gold_cost - inv.gold) / gold_cost)
            ))
            
        return StrategicUpdate(blockers_add_or_update=blockers)

    @staticmethod
    def resolve_blockers(
        state: AuthoritativeState,
        update: StateUpdate
    ) -> StateUpdate:
        """
        State-wide resolution of material blockers based on inventory additions.
        Called by the Kernel in Phase 4 (Resolution).
        """
        from dataclasses import replace
        from src_v2.core.updates import EntityUpdate, StrategicUpdate
        
        refined_entity_updates = dict(update.entity_updates)
        
        for e_id, ent_upd in update.entity_updates.items():
            if e_id not in state.entities:
                continue
                
            entity = state.entities[e_id]
            
            # Identify added items
            items_added = []
            if ent_upd.inventory:
                items_added.extend(ent_upd.inventory.items_added)
                
            if not items_added:
                continue
                
            # Scan for material blockers matching added items
            resolved_ids = []
            for item in items_added:
                blocker_id = f"blocker_mat_{item}"
                if blocker_id in entity.strategic.blockers:
                    resolved_ids.append(blocker_id)
            
            if resolved_ids:
                # Merge into existing entity update
                strat_up = ent_upd.strategic or StrategicUpdate()
                
                # Filter out newly added blockers if they match resolved_ids
                new_additions = [
                    b for b in strat_up.blockers_add_or_update 
                    if b.id not in resolved_ids
                ]
                
                new_strat_up = replace(
                    strat_up,
                    blockers_add_or_update=new_additions,
                    blockers_remove=list(set(strat_up.blockers_remove + resolved_ids))
                )
                refined_entity_updates[e_id] = replace(ent_upd, strategic=new_strat_up)
                
        return replace(update, entity_updates=refined_entity_updates)
