# Compliance IDs: TOWN-016
from __future__ import annotations
from typing import TYPE_CHECKING, Any
from dataclasses import replace

from src.core.updates import EntityUpdate
from src.engine.service_reach import service_at
from src.systems.economy_systems.reputation_discount import apply_reputation_discount

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState
    from src.core.updates import StateUpdate

def shop_price(state: Any, shop: Any, item_id: str, is_buy: bool) -> int:
    """The one price law at a shop (Bible 03 section 4): `MarketSystem.calculate_price`. The engine reaches it through this door, the one place
    it is pinned to the market (a layer exception), so a sale (`shop_sale.py`) and the enforced buy floor read the same law."""
    from src.systems.market import MarketSystem
    return MarketSystem.calculate_price(state, shop, item_id, is_buy=is_buy)


class ShopSystem:
    """
    Authoritative handler for explicit shop interactions.
    Law of Value: Prices must match the registry truth.
    """

    @staticmethod
    def enforce(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Produce authoritative item-to-gold conversions for entities at a shop.
        Law of Profit: Only junk and materials are auto-sold to prevent gear loss.
        # VERIFIED v2: shop_visit_semantics
        Logic ID: TOWN-016 (Shop visits resolve bounded buy/sell behavior)
        """
        from src.engine.spatial_query import SpatialQueryService
        refined_entity_updates = dict(update.entity_updates)
        
        # Optimization: Only process entities that moved or had inventory changes
        # Logic ID: PERF-006 (Dirty Entity Tracking)
        from src.core.dirty import get_relevant_entity_ids
        relevant_ids = get_relevant_entity_ids(state, update, "shop")
        
        for e_id in relevant_ids:
            entity = state.entities.get(e_id)
            if not entity: continue
            
            pos = entity.navigation.position
            existing_upd = refined_entity_updates.get(e_id, EntityUpdate(entity_id=e_id))
            if existing_upd and existing_upd.new_position:
                pos = existing_upd.new_position
                
            # `building_tiles` is empty in compiled worlds, so the shop is found through `service_reach` (on or beside a shop tile).
            tile_pos, building_type = service_at(state, (int(pos[0]), int(pos[1])), {"shop"})
            
            if building_type == "shop":
                # Check functionality (LEG-RPG-001/006)
                building = SpatialQueryService.get_building_at(state, tile_pos)
                if building and not building.functional:
                    continue # Shop is sabotaged and non-functional
                
                # Phase E5.6: Price Hardening (Law of Value)
                # Ensure proposed buy prices are not lower than dynamic Truth.
                # Use MarketSystem.calculate_price so the enforced floor matches what
                # clients compute — DynamicPriceService uses item_def.value which diverges
                # from MarketSystem's hardcoded base table after catalog bootstrap.

                sanitized_transfers = []
                for intent in existing_upd.resource_transfers:
                    if intent.source_kind == "SHOP_BUY":
                        if not intent.items_add:
                            continue
                        item_id = intent.items_add[0].item_id
                        intent_building = state.buildings.get(intent.source_id) or building
                        if not intent_building:
                            continue

                        # Re-calculate Truth using the same pricing path clients use
                        quantity = sum(s.quantity for s in intent.items_add)
                        legal_price = shop_price(state, intent_building, item_id, is_buy=True)
                        legal_total = apply_reputation_discount(legal_price * quantity, entity.social.public_reputation)

                        if intent.gold_cost < legal_total:
                            # Price too low! Possible exploit or stale simulation.
                            from src.core.enums import ReasonCode
                            from src.core.updates import RejectionEvent
                            update = replace(update, rejection_events=update.rejection_events + [RejectionEvent(
                                tick=state.tick, actor_id=e_id, action_kind="BUY", reason=ReasonCode.ILLEGAL_ACTION, target_id=item_id
                            )])
                            continue 
                    sanitized_transfers.append(intent)
                
                existing_upd = replace(existing_upd, resource_transfers=sanitized_transfers)
                
                # Selling is a chosen act (the SELL action, `shop_sale.py`), not something that happens to whoever stands here.
                refined_entity_updates[e_id] = existing_upd
                
        return replace(update, entity_updates=refined_entity_updates)
