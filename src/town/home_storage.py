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
            
        # 4. Generate Updates
        return StateUpdate(
            entity_updates={
                entity.id: EntityUpdate(
                    entity_id=entity.id,
                    inventory=InventoryUpdate(items_remove=[ItemStack(item_id, quantity)])
                )
            },
            home_storage_updates={
                entity.id: InventoryUpdate(items_add=[ItemStack(item_id, quantity)])
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
            
        home_inv = state.home_storage.get(entity.id)
        if not home_inv:
            return None
            
        existing = next((s for s in home_inv.items if s.item_id == item_id), None)
        if not existing or existing.quantity < quantity:
            return None
            
        if not InventoryService.can_add_item(entity.inventory, item_id, quantity):
            return None
            
        return StateUpdate(
            entity_updates={
                entity.id: EntityUpdate(
                    entity_id=entity.id,
                    inventory=InventoryUpdate(items_add=[ItemStack(item_id, quantity)])
                )
            },
            home_storage_updates={
                entity.id: InventoryUpdate(items_remove=[ItemStack(item_id, quantity)])
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
