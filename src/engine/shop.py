from __future__ import annotations
from typing import TYPE_CHECKING, Dict
from dataclasses import replace

from src.core.updates import EntityUpdate

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate

class ShopSystem:
    """
    Authoritative handler for explicit shop interactions.
    Law of Value: Prices must match the registry truth.
    """

    # Parity with V1 ITEM_REGISTRY values/rarity
    # In V2 we might eventually pull this from a registry component
    ITEM_VALUES: Dict[str, int] = {
        "wood": 5,
        "iron_ore": 10,
        "iron_sword": 5,
        "steel_sword": 15,
        "herbal_remedy": 10,
        "__DEFAULT__": 5
    }

    @staticmethod
    def enforce(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Produce authoritative item-to-gold conversions for entities at a shop.
        Law of Profit: Only junk and materials are auto-sold to prevent gear loss.
        """
        refined_entity_updates = dict(update.entity_updates)
        
        for e_id, entity in state.entities.items():
            pos = entity.position
            ent_upd = refined_entity_updates.get(e_id)
            if ent_upd and ent_upd.new_position:
                pos = ent_upd.new_position
                
            tile_pos = (int(pos[0]), int(pos[1]))
            building_type = state.building_tiles.get(tile_pos)
            
            if building_type == "shop":
                # Check functionality (LEG-RPG-001/006)
                building = next((b for b in state.buildings.values() if b.position == tile_pos and b.kind == "shop"), None)
                if building and not building.functional:
                    continue # Shop is sabotaged and non-functional
                
                # Pillar 4.2 Dread Bias: Regional trauma increases prices
                from src.engine.domain_logic import SimulationDomainLogic
                region_trauma = SimulationDomainLogic.get_region_trauma(state, pos)
                
                # Sell items based on V1 logic (Materials + Junk)
                gold_delta = 0
                items_to_remove = []
                
                for item in entity.inventory.items:
                    item_id = item.item_id if hasattr(item, "item_id") else item
                    item_key = item_id.lower()
                    if item_key in ("wood", "ore", "iron_ore", "fish", "leather", "fiber", "herb", "iron_sword"):
                        price = ShopSystem.get_sell_price(item_key, region_trauma)
                        gold_delta += price
                        items_to_remove.append(item)
                
                if not items_to_remove:
                    continue
                
                # Phase 3 Law: Resource Conservation (Atomic Shop)
                from src.core.updates import ResourceTransferIntent
                intent = ResourceTransferIntent(
                    source_id="AUTO_SELL",
                    source_kind="SHOP_SELL",
                    items_remove=items_to_remove,
                    gold_delta=gold_delta,
                    transfer_kind="SELL"
                )
                
                existing_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                refined_entity_updates[e_id] = replace(
                    existing_upd,
                    resource_transfers=list(existing_upd.resource_transfers) + [intent]
                )
                
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def get_sell_price(item_kind: str, region_trauma: float = 0.0) -> int:
        base = ShopSystem.ITEM_VALUES.get(item_kind, ShopSystem.ITEM_VALUES["__DEFAULT__"])
        # Pillar 1.3: Economy & Scarcity
        # Regional trauma increases prices (Supply chain disruption / Risk premium)
        modifier = 1.0 + (region_trauma / 10.0)
        return int(base * modifier)
