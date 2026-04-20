from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Set, Tuple
from dataclasses import replace

from src_v2.core.updates import EntityUpdate, InventoryUpdate

if TYPE_CHECKING:
    from src_v2.core.state import AuthoritativeState, EntityState
    from src_v2.core.updates import StateUpdate


class TownResolutionSystem:
    """
    Authoritative handler for town territory resolution:
    1. Sell-on-Entry Law: Materials converted to GOLD when in town.
    """

    # Parity with legacy SELL_PRICES and Item Registry
    ITEM_SELL_PRICES: Dict[str, int] = {
        "WOOD": 5,
        "ORE": 5,
        "IRON_ORE": 5,
        "FISH": 5,
        "LEATHER": 5,
        "FIBER": 5,
        "HERB": 5,
        "GOLD": 1, 
        "__DEFAULT__": 3
    }

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Detect entities in town and apply resource conversions.
        """
        refined_entity_updates = dict(update.entity_updates)
        
        for e_id, entity in state.entities.items():
            # Check if entity is in town
            pos = entity.position
            ent_upd = refined_entity_updates.get(e_id)
            if ent_upd and ent_upd.new_position:
                pos = ent_upd.new_position
            
            tile_pos = (int(pos[0]), int(pos[1]))
            
            if tile_pos in state.town_tiles:
                if not entity.inventory.items:
                    continue
                
                total_value = 0
                items_to_remove = []
                for item in entity.inventory.items:
                    if item == "GOLD": continue
                    price = TownResolutionSystem.ITEM_SELL_PRICES.get(item, TownResolutionSystem.ITEM_SELL_PRICES["__DEFAULT__"])
                    total_value += price
                    items_to_remove.append(item)
                
                if not items_to_remove:
                    continue
                
                # Merge with existing update if any
                existing_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                
                # Prepare inventory changes
                existing_added = existing_upd.inventory.items_added if existing_upd.inventory else []
                existing_removed = existing_upd.inventory.items_removed if existing_upd.inventory else []
                
                new_removed = list(existing_removed)
                new_removed.extend(items_to_remove)
                
                new_added = list(existing_added)
                for _ in range(total_value):
                    new_added.append("GOLD")
                
                refined_entity_updates[e_id] = replace(
                    existing_upd,
                    inventory=InventoryUpdate(
                        items_added=new_added,
                        items_removed=new_removed
                    )
                )

        return replace(update, entity_updates=refined_entity_updates)
