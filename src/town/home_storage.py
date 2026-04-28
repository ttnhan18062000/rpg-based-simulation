from __future__ import annotations
from typing import Optional, List, Dict
from src.core.state import AuthoritativeState, EntityState, InventoryComponent, ItemStack
from src.core.updates import StateUpdate, EntityUpdate, InventoryUpdate
from src.core.inventory import InventoryService

class HomeStorageService:
    """Manages transfers between entity inventory and persistent home storage."""

    @staticmethod
    def transfer_to_home(
        entity: EntityState, 
        item_id: str, 
        quantity: int, 
        state: AuthoritativeState
    ) -> Optional[StateUpdate]:
        """Move item from entity inventory to their home storage."""
        # 1. Proximity Check
        # Home storage is accessible at the town center (simple M7 rule)
        dist = abs(entity.position[0] - state.town_center[0]) + abs(entity.position[1] - state.town_center[1])
        if dist > 2.0:
            return None
            
        # 2. Check Entity Inventory
        inv = entity.inventory
        existing = next((s for s in inv.items if s.item_id == item_id), None)
        if not existing or existing.quantity < quantity:
            return None
            
        # 3. Check Home Storage Capacity
        home_inv = state.home_storage.get(entity.id)
        if not home_inv:
            # Initialize storage if it doesn't exist
            home_inv = InventoryComponent(max_slots=32, max_weight=200.0)
            
        if not InventoryService.can_add_item(home_inv, item_id, quantity):
            return None
            
        # 4. Generate Transaction Intent
        from src.core.updates import ResourceTransferIntent
        intent = ResourceTransferIntent(
            source_id="HOME_STORAGE",
            source_kind="HOME_STORAGE",
            items_remove=[ItemStack(item_id, quantity)], # Entity gives to source
            transfer_kind="DEPOSIT"
        )
        
        return StateUpdate(
            entity_updates={
                entity.id: EntityUpdate(
                    entity_id=entity.id,
                    resource_transfers=[intent]
                )
            }
        )

    @staticmethod
    def transfer_from_home(
        entity: EntityState, 
        item_id: str, 
        quantity: int, 
        state: AuthoritativeState
    ) -> Optional[StateUpdate]:
        """Move item from home storage to entity inventory."""
        dist = abs(entity.position[0] - state.town_center[0]) + abs(entity.position[1] - state.town_center[1])
        if dist > 2.0:
            return None
            
        # 4. Generate Transaction Intent
        from src.core.updates import ResourceTransferIntent
        intent = ResourceTransferIntent(
            source_id="HOME_STORAGE",
            source_kind="HOME_STORAGE",
            items_add=[ItemStack(item_id, quantity)], # Entity gains from source
            transfer_kind="WITHDRAW"
        )
        
        return StateUpdate(
            entity_updates={
                entity.id: EntityUpdate(
                    entity_id=entity.id,
                    resource_transfers=[intent]
                )
            }
        )

class HomeStorageAction:
    """Action wrapper for inventory tests."""
    @staticmethod
    def deposit(entity: EntityState, item_id: str, quantity: int, state: AuthoritativeState) -> Optional[StateUpdate]:
        return HomeStorageService.transfer_to_home(entity, item_id, quantity, state)

    @staticmethod
    def withdraw(entity: EntityState, item_id: str, quantity: int, state: AuthoritativeState) -> Optional[StateUpdate]:
        return HomeStorageService.transfer_from_home(entity, item_id, quantity, state)
