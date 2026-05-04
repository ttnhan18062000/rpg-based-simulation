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
        # VERIFIED v2: shop_visit_semantics
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
                
                # Phase E5.6: Price Hardening (Law of Value)
                # Ensure proposed buy prices are not lower than dynamic Truth
                from src.systems.economy import DynamicPriceService
                from src.core.items import ItemRegistry
                
                sanitized_transfers = []
                existing_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
                for intent in existing_upd.resource_transfers:
                    if intent.source_kind == "SHOP_BUY":
                        if not intent.items_add:
                            continue
                        item_id = intent.items_add[0].item_id
                        item_def = ItemRegistry.get(item_id)
                        if not item_def:
                            continue # Invalid item
                            
                        # Re-calculate Truth
                        legal_price = DynamicPriceService.calculate_buy_price(item_def.value, state)
                        quantity = sum(s.quantity for s in intent.items_add)
                        legal_total = legal_price * quantity
                        
                        if intent.gold_cost < legal_total:
                            # Price too low! Possible exploit or stale simulation.
                            # We "harden" it by correcting the price instead of rejecting?
                            # No, rejection is safer for determinism.
                            from src.core.enums import ReasonCode
                            from src.core.updates import RejectionEvent
                            update = replace(update, rejection_events=update.rejection_events + [RejectionEvent(
                                tick=state.tick, actor_id=e_id, action_kind="BUY", reason=ReasonCode.ILLEGAL_ACTION, target_id=item_id
                            )])
                            continue 
                    sanitized_transfers.append(intent)
                
                existing_upd = replace(existing_upd, resource_transfers=sanitized_transfers)
                
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
                
                if gold_delta > 0:
                    # Phase 3 Law: Resource Conservation (Atomic Shop)
                    from src.core.updates import ResourceTransferIntent
                    auto_sell_intent = ResourceTransferIntent(
                        source_id=building.id if building else "AUTO_SELL",
                        source_kind="SHOP_SELL",
                        items_remove=items_to_remove,
                        gold_delta=gold_delta,
                        price_multiplier=1.0,
                        transfer_kind="SELL"
                    )
                    existing_upd = replace(
                        existing_upd,
                        resource_transfers=list(existing_upd.resource_transfers) + [auto_sell_intent]
                    )
                
                refined_entity_updates[e_id] = existing_upd
                
        return replace(update, entity_updates=refined_entity_updates)

    @staticmethod
    def get_sell_price(item_kind: str, region_trauma: float = 0.0) -> int:
        base = ShopSystem.ITEM_VALUES.get(item_kind, ShopSystem.ITEM_VALUES["__DEFAULT__"])
        # Pillar 1.3: Economy & Scarcity
        # Regional trauma increases prices (Supply chain disruption / Risk premium)
        modifier = 1.0 + (region_trauma / 10.0)
        return int(base * modifier)
