# Compliance IDs: PROG-005, TOWN-012, TOWN-079, TOWN-080, TOWN-081, TOWN-104, TOWN-105, TOWN-109, TOWN-110, TOWN-111, TOWN-126, TOWN-127, TOWN-128
# Compliance IDs: TOWN-079, TOWN-080, TOWN-081
from __future__ import annotations
from typing import List, Optional, Tuple
from src.core.state import (
    InventoryComponent, ItemStack, EntityState, EquipSlot, AuthoritativeState,
    ItemInstance, AcquiredMethod,
)
from src.core.items import ItemRegistry
from typing import TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)
if TYPE_CHECKING:
    from src.core.updates import InventoryUpdate
    from src.core.update_models.resources import ResourceTransferIntent

class InventoryService:
    """Service for managing inventory state and validation."""

    @staticmethod
    def apply_transfer(inventory: InventoryComponent, transfer: ResourceTransferIntent) -> InventoryComponent:
        from src.core.updates import InventoryUpdate
        upd = InventoryUpdate(
            items_add=transfer.items_add,
            items_remove=transfer.items_remove,
            gold_delta=transfer.gold_delta - transfer.gold_cost
        )
        return InventoryService.apply_update(inventory, upd)

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
        """
        Check if an item can be added without exceeding slots or weight.
        Logic ID: TOWN-013 (Bounded capacity check)
        """
        defn = ItemRegistry.get(item_id)
        if not defn:
            return False
            
        # 1. Check Weight
        current_weight = InventoryService.calculate_total_weight(inventory)
        if current_weight + (defn.weight * quantity) > inventory.max_weight:
            return False
            
        # 2. Check Slots
        existing_stack = next((s for s in inventory.items if s.item_id == item_id), None)
        if not existing_stack:
            if len(inventory.items) >= inventory.max_slots:
                return False
                
        return True

    @staticmethod
    def can_add_items(inventory: InventoryComponent, item_stacks: List[ItemStack]) -> bool:
        """Check if a list of item stacks can be added without exceeding slots or weight."""
        temp_items = list(inventory.items)
        total_weight = InventoryService.calculate_total_weight(inventory)
        
        for stack in item_stacks:
            defn = ItemRegistry.get(stack.item_id)
            if not defn:
                return False # Law: Unknown items cannot be added
                
            # Logic ID: TOWN-012 (Weight pressure check)
            total_weight += defn.weight * stack.quantity
            if total_weight > inventory.max_weight:
                return False
                
            remaining_qty = stack.quantity
            # 1. Fill existing stack
            existing = next((s for s in temp_items if s.item_id == stack.item_id), None)
            if existing and existing.quantity < defn.stack_size:
                space = defn.stack_size - existing.quantity
                to_add = min(remaining_qty, space)
                # Update existing stack in temp_items (optional for slot count, but good for completeness)
                # For slots, we only care if we need NEW ones.
                remaining_qty -= to_add
                logger.debug(f"DEBUG: Filling existing stack for {stack.item_id}. Space: {space}, to_add: {to_add}, remaining: {remaining_qty}")
            
            # 2. Add new stacks
            while remaining_qty > 0:
                if len(temp_items) >= inventory.max_slots:
                    logger.debug(f"DEBUG: Capacity FAIL for {stack.item_id}. Slots: {len(temp_items)}/{inventory.max_slots}")
                    return False
                to_add = min(remaining_qty, defn.stack_size)
                temp_items.append(ItemStack(stack.item_id, to_add))
                remaining_qty -= to_add
                logger.debug(f"DEBUG: Added new stack for {stack.item_id}. Slots: {len(temp_items)}")
                
        return True

    @staticmethod
    def can_add_items_with_removals(inventory: InventoryComponent, items_add: List[ItemStack], items_remove: List[ItemStack]) -> bool:
        """Check capacity after accounting for item removals (Phase 8)."""
        from dataclasses import replace
        # 1. Simulate removals
        new_items = list(inventory.items)
        for remove_stack in items_remove:
             existing = next((s for s in new_items if s.item_id == remove_stack.item_id), None)
             if existing:
                 new_qty = max(0, existing.quantity - remove_stack.quantity)
                 new_items.remove(existing)
                 if new_qty > 0:
                     new_items.append(ItemStack(remove_stack.item_id, new_qty))
                     
        # 2. Check adds on the simulated inventory
        # We must create a temporary inventory object to use existing validation logic
        temp_inv = replace(inventory, items=new_items)
        return InventoryService.can_add_items(temp_inv, items_add)

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
        if not update.items_remove and not update.items_add:
            if update.gold_delta == 0:
                return inventory
            from dataclasses import replace
            return replace(inventory, gold=max(0, inventory.gold + update.gold_delta))
            
        from dataclasses import replace
        new_items = list(inventory.items)
        
        # 1. Handle Removals
        for remove_stack in update.items_remove:
            # Multi-stack removal logic
            remaining_to_remove = remove_stack.quantity
            indices_to_remove = []
            for i, existing in enumerate(new_items):
                if existing.item_id == remove_stack.item_id:
                    if existing.quantity <= remaining_to_remove:
                        remaining_to_remove -= existing.quantity
                        indices_to_remove.append(i)
                    else:
                        new_items[i] = replace(existing, quantity=existing.quantity - remaining_to_remove)
                        remaining_to_remove = 0
                        break
            
            # Remove indices in reverse to avoid shifting
            for i in sorted(indices_to_remove, reverse=True):
                new_items.pop(i)
        
        # Calculate current weight once for efficiency
        current_weight = InventoryService.calculate_total_weight(replace(inventory, items=new_items))
        
        # 2. Handle Additions
        for add_stack in update.items_add:
            defn = ItemRegistry.get(add_stack.item_id)
            if not defn:
                continue
                
            remaining_to_add = add_stack.quantity
            
            # First, try to fill existing partially-filled stacks
            for i, existing in enumerate(new_items):
                if existing.item_id == add_stack.item_id and existing.quantity < defn.stack_size:
                    space_in_stack = defn.stack_size - existing.quantity
                    amount_to_add = min(remaining_to_add, space_in_stack)
                    
                    # Weight Check
                    if current_weight + (defn.weight * amount_to_add) > inventory.max_weight:
                        # Add as much as fits weight-wise
                        max_fit = int((inventory.max_weight - current_weight) / defn.weight)
                        amount_to_add = min(amount_to_add, max_fit)
                        
                    if amount_to_add > 0:
                        new_items[i] = replace(existing, quantity=existing.quantity + amount_to_add)
                        current_weight += defn.weight * amount_to_add
                        remaining_to_add -= amount_to_add
                        
                if remaining_to_add <= 0:
                    break
            
            # Second, create new stacks if there are slots remaining
            while remaining_to_add > 0 and len(new_items) < inventory.max_slots:
                amount_to_add = min(remaining_to_add, defn.stack_size)
                
                # Weight Check
                if current_weight + (defn.weight * amount_to_add) > inventory.max_weight:
                    max_fit = int((inventory.max_weight - current_weight) / defn.weight)
                    amount_to_add = min(amount_to_add, max_fit)
                
                if amount_to_add <= 0:
                    break
                    
                new_items.append(replace(add_stack, quantity=amount_to_add))
                current_weight += defn.weight * amount_to_add
                remaining_to_add -= amount_to_add
        
        return replace(
            inventory,
            items=new_items,
            gold=max(0, inventory.gold + update.gold_delta)
        )


class ItemInstanceService:
    """Per-tick stateful id allocator for ItemInstance minting, mirroring EntityGenerator._last_id
    (src/systems/world_systems/generator.py:28-32). Callers MUST construct exactly one
    ItemInstanceService(state) per tick/phase invocation and reuse that same instance across every
    maybe_create_instance() call within that invocation — never re-instantiate mid-tick — so that
    two mints in the same tick never read the same next_item_instance_id and collide. At the end
    of the phase, propose next_item_instance_id_set=<instance>.last_id + 1 in the StateUpdate only
    if at least one instance was actually minted (mirrors src/world/spawn.py:119's
    `next_entity_id_set=generator._last_id + 1 if entities_add else None`)."""

    def __init__(self, state: "AuthoritativeState"):
        self._last_id = state.next_item_instance_id - 1

    @property
    def last_id(self) -> int:
        return self._last_id

    def maybe_create_instance(
        self,
        item_id: str,
        significant: bool,
        owner_entity_id: int,
        tick: int,
        acquired_method: AcquiredMethod,
        state: "AuthoritativeState",
    ) -> Optional[ItemInstance]:
        """Pure construction only — does not mutate state. Caller must route the result through
        StateUpdate.item_instances_add_or_update + next_item_instance_id_set (using this
        instance's .last_id, see class docstring), applied only by ApplyPath.apply_generation.
        Returns None when `significant` is False (ordinary ItemStack path, unaffected) or when
        ENABLE_ITEM_INSTANCE_HISTORY is not ON. Does NOT increment/consume an id in either
        None-returning case."""
        if not significant:
            return None
        flags = getattr(state, "feature_flags", None) or {}
        if flags.get("ENABLE_ITEM_INSTANCE_HISTORY", "OFF") != "ON":
            return None
        self._last_id += 1
        return ItemInstance(
            instance_id=self._last_id,
            item_id=item_id,
            owner_history=[str(owner_entity_id)],
            acquired_tick=tick,
            acquired_method=acquired_method,
        )
