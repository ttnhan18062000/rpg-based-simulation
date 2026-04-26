from __future__ import annotations
from typing import List, Optional, Tuple
from src.core.state import InventoryComponent, ItemStack, EntityState, EquipSlot
from src.core.items import ItemRegistry
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.updates import InventoryUpdate

class InventoryService:
    """Service for managing inventory state and validation."""

    @staticmethod
    def calculate_total_weight(inventory: InventoryComponent) -> float:
        """Calculate total weight of all items in inventory."""
        total = 0.0
        for stack in inventory.items:
            item_id = stack.item_id if hasattr(stack, "item_id") else stack
            quantity = stack.quantity if hasattr(stack, "quantity") else 1
            defn = ItemRegistry.get(item_id)
            if defn:
                total += defn.weight * quantity
        return total

    @staticmethod
    def can_add_item(inventory: InventoryComponent, item_id: str, quantity: int) -> bool:
        """Check if an item can be added without exceeding slots or weight."""
        defn = ItemRegistry.get(item_id)
        if not defn:
            return False
            
        # 1. Check Weight
        current_weight = InventoryService.calculate_total_weight(inventory)
        if current_weight + (defn.weight * quantity) > inventory.max_weight:
            return False
            
        # 2. Check Slots
        existing_stack = next((s for s in inventory.items if (s.item_id if hasattr(s, "item_id") else s) == item_id), None)
        if existing_stack:
            # If it can stack, it doesn't take a new slot (assuming we don't exceed stack_size)
            # For simplicity in M1, we assume infinite stacking within a slot or handling split stacks
            # In V2, we should probably check stack_size
            pass
        else:
            if len(inventory.items) >= inventory.max_slots:
                return False
                
        return True

    @staticmethod
    def can_equip_item(entity: EntityState, item_id: str, slot: EquipSlot) -> bool:
        """Check if an item can be equipped in the specified slot."""
        defn = ItemRegistry.get(item_id)
        if not defn:
            return False
            
        # Check if item has correct slot property
        required_slot = defn.properties.get("slot")
        if required_slot != slot:
            return False
            
    @staticmethod
    def apply_update(inventory: InventoryComponent, update: InventoryUpdate) -> InventoryComponent:
        """Apply authoritative updates to inventory, merging stacks and enforcing limits."""
        from dataclasses import replace
        new_items = list(inventory.items)
        
        # 1. Handle Removals
        for remove_stack in update.items_remove:
            existing = next((s for s in new_items if (s.item_id if hasattr(s, "item_id") else s) == remove_stack.item_id), None)
            if existing:
                existing_qty = existing.quantity if hasattr(existing, "quantity") else 1
                new_qty = max(0, existing_qty - remove_stack.quantity)
                new_items.remove(existing)
                if new_qty > 0:
                    new_items.append(ItemStack(remove_stack.item_id, new_qty))
        
        # 2. Handle Additions
        for add_stack in update.items_add:
            # Check capacity
            if not InventoryService.can_add_item(inventory, add_stack.item_id, add_stack.quantity):
                # In M1, we skip addition if it exceeds capacity
                continue
                
            existing = next((s for s in new_items if (s.item_id if hasattr(s, "item_id") else s) == add_stack.item_id), None)
            if existing:
                existing_qty = existing.quantity if hasattr(existing, "quantity") else 1
                new_qty = existing_qty + add_stack.quantity
                new_items.remove(existing)
                new_items.append(ItemStack(add_stack.item_id, new_qty))
            else:
                if len(new_items) < inventory.max_slots:
                    new_items.append(add_stack)
        
        return replace(
            inventory,
            items=new_items,
            gold=inventory.gold + update.gold_delta
        )
