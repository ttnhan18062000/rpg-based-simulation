from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Set, Tuple
from dataclasses import replace

from src_v2.core.updates import EntityUpdate, InventoryUpdate, IdentityUpdate, CombatUpdate

if TYPE_CHECKING:
    from src_v2.core.state import AuthoritativeState, EntityState
    from src_v2.core.updates import StateUpdate


class TownResolutionSystem:
    """
    Authoritative handler for town territory resolution.
    """

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Detect entities in town and apply general passive laws (Healing).
        """
        refined_entity_updates = dict(update.entity_updates)
        
        # Town Configuration Constants (Parity with config.py)
        PASSIVE_HEAL_AMT = 1 # town_passive_heal
        
        for e_id, entity in state.entities.items():
            pos = entity.position
            ent_upd = refined_entity_updates.get(e_id)
            if ent_upd and ent_upd.new_position:
                pos = ent_upd.new_position
            
            tile_pos = (int(pos[0]), int(pos[1]))
            
            if tile_pos in state.town_tiles:
                # 1. Passive Healing Law (Hardened CombatComponent)
                current_hp = entity.combat.hp
                max_hp = entity.combat.max_hp
                
                if current_hp < max_hp:
                    existing_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                    
                    combat_upd = existing_upd.combat or CombatUpdate()
                    new_combat_upd = replace(combat_upd, hp_delta=combat_upd.hp_delta + PASSIVE_HEAL_AMT)
                    
                    refined_entity_updates[e_id] = replace(
                        existing_upd,
                        combat=new_combat_upd
                    )

        return replace(update, entity_updates=refined_entity_updates)
