from __future__ import annotations
from typing import Optional, List, Dict
from src.core.state import AuthoritativeState, EntityState, BuildingState, ItemStack
from src.core.updates import StateUpdate, EntityUpdate, InventoryUpdate
from src.core.items import ItemRegistry
from src.core.inventory import InventoryService

class ShopService:
    """Manages buying and selling of items at town shops."""

    @staticmethod
    def buy_item(
        entity: EntityState, 
        item_id: str, 
        quantity: int, 
        state: AuthoritativeState
    ) -> Optional[StateUpdate]:
        """Entity buys item from a nearby shop."""
        # 1. Proximity to any functional shop
        shop = next((b for b in state.buildings.values() if b.kind == "shop" and b.functional), None)
        if not shop:
            return None
            
        dist = abs(entity.position[0] - shop.position[0]) + abs(entity.position[1] - shop.position[1])
        if dist > 2.0:
            return None
            
        # 2. Check Cost
        item_def = ItemRegistry.get(item_id)
        if not item_def:
            return None
            
        from src.systems.economy import DynamicPriceService
        unit_price = DynamicPriceService.calculate_buy_price(item_def.value, state)
        total_cost = unit_price * quantity
        price_multiplier = unit_price / item_def.value if item_def.value > 0 else 1.0
        
        if entity.inventory.gold < total_cost:
            return None
            
        # 3. Check Capacity
        if not InventoryService.can_add_item(entity.inventory, item_id, quantity):
            return None
            
        # 4. Generate Intent
        from src.core.updates import ResourceTransferIntent
        return StateUpdate(
            entity_updates={
                entity.id: EntityUpdate(
                    entity_id=entity.id,
                    resource_transfers=[ResourceTransferIntent(
                        source_id=item_id,
                        source_kind="SHOP_BUY",
                        items_add=[ItemStack(item_id, quantity)],
                        gold_cost=total_cost,
                        price_multiplier=price_multiplier,
                        transfer_kind="BUY"
                    )]
                )
            }
        )

    @staticmethod
    def sell_item(
        entity: EntityState, 
        item_id: str, 
        quantity: int, 
        state: AuthoritativeState
    ) -> Optional[StateUpdate]:
        """Entity sells item to a nearby shop."""
        shop = next((b for b in state.buildings.values() if b.kind == "shop" and b.functional), None)
        if not shop:
            return None
            
        dist = abs(entity.position[0] - shop.position[0]) + abs(entity.position[1] - shop.position[1])
        if dist > 2.0:
            return None
            
        # 1. Check Inventory
        existing = next((s for s in entity.inventory.items if s.item_id == item_id), None)
        if not existing or existing.quantity < quantity:
            return None
            
        # 2. Check Value
        item_def = ItemRegistry.get(item_id)
        if not item_def:
            return None
            
        total_gain = (item_def.value * quantity) // 2 # Sell for half price
        
        # 3. Generate Intent
        from src.core.updates import ResourceTransferIntent
        return StateUpdate(
            entity_updates={
                entity.id: EntityUpdate(
                    entity_id=entity.id,
                    resource_transfers=[ResourceTransferIntent(
                        source_id=item_id,
                        source_kind="SHOP_SELL",
                        items_remove=[ItemStack(item_id, quantity)],
                        gold_delta=total_gain,
                        price_multiplier=1.0,
                        transfer_kind="SELL"
                    )]
                )
            }
        )

class ShopAction:
    """Action wrapper for economy tests."""
    @staticmethod
    def buy(entity: EntityState, item_id: str, quantity: int, state: AuthoritativeState) -> Optional[EntityUpdate]:
        res = ShopService.buy_item(entity, item_id, quantity, state)
        if res and entity.id in res.entity_updates:
            return res.entity_updates[entity.id]
        return None

    @staticmethod
    def sell(entity: EntityState, item_id: str, quantity: int, state: AuthoritativeState) -> Optional[EntityUpdate]:
        res = ShopService.sell_item(entity, item_id, quantity, state)
        if res and entity.id in res.entity_updates:
            return res.entity_updates[entity.id]
        return None
