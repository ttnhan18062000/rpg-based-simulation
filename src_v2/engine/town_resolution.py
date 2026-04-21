from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Set, Tuple
from dataclasses import replace

from src_v2.core.updates import EntityUpdate, InventoryUpdate, IdentityUpdate

if TYPE_CHECKING:
    from src_v2.core.state import AuthoritativeState, EntityState
    from src_v2.core.updates import StateUpdate


class TownResolutionSystem:
    """
    Authoritative handler for town territory resolution:
    1. Sell-on-Entry Law: Materials converted to GOLD when in town.
    """

    # Parity with legacy SELL_PRICES and Item Registry
    ITEM_VALUES: Dict[str, int] = {
        "wood": 5,
        "iron_ore": 5,
        "iron_sword": 5,
        "steel_sword": 15,
        "herbal_remedy": 10,
        "__DEFAULT__": 3
    }

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
                # 1. Passive Healing Law (Property-based HP)
                current_hp = entity.properties.get("hp", 100)
                max_hp = entity.properties.get("max_hp", 100)
                
                property_updates = {}
                if current_hp < max_hp:
                    property_updates["hp"] = min(max_hp, current_hp + PASSIVE_HEAL_AMT)
                
                if not property_updates:
                    continue
                
                # Merge with existing update
                existing_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                
                # Properties merge
                new_prop_updates = dict(existing_upd.property_updates)
                new_prop_updates.update(property_updates)
                
                refined_entity_updates[e_id] = replace(
                    existing_upd,
                    property_updates=new_prop_updates
                )

        return replace(update, entity_updates=refined_entity_updates)
