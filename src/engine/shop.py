# Compliance IDs: TOWN-016
from __future__ import annotations
from typing import TYPE_CHECKING, Dict
from dataclasses import replace

from src.core.updates import EntityUpdate
from src.systems.economy_systems.reputation_discount import apply_reputation_discount

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
                
            tile_pos = (int(pos[0]), int(pos[1]))
            building_type = state.building_tiles.get(tile_pos)
            
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
                from src.systems.market import MarketSystem

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
                        legal_price = MarketSystem.calculate_price(state, intent_building, item_id, is_buy=True)
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
