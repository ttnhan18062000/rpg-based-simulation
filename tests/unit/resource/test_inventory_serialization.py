import pytest
from dataclasses import replace
from src.core.state import (
    EntityState, IdentityComponent, InventoryComponent, 
    ItemStack, ItemKind, EquipSlot
)
from src.core.updates import InventoryUpdate
from src.core.inventory import InventoryService
from src.core.items import ItemRegistry, ItemDefinition
from src.core.builder import V2EntityBuilder

def test_inventory_stack_merging():
    # Registry has wood with stack_size 20 (default)
    # Let's ensure it's in registry
    if not ItemRegistry.get("wood"):
        ItemRegistry._items["wood"] = ItemDefinition("wood", "Wood", ItemKind.MATERIAL, weight=1.0)
    
    inv = InventoryComponent(max_slots=5, max_weight=100.0, items=[
        ItemStack("wood", 15)
    ])
    
    # Add 10 wood. 5 should merge, 5 should create new stack.
    update = InventoryUpdate(items_add=[ItemStack("wood", 10)])
    new_inv = InventoryService.apply_update(inv, update)
    
    assert len(new_inv.items) == 2
    assert new_inv.items[0].quantity == 20
    assert new_inv.items[1].quantity == 5
    
    print("\nSuccessfully verified inventory stack merging.")

def test_inventory_limits():
    inv = InventoryComponent(max_slots=2, max_weight=10.0, items=[])
    
    # 1. Slot Limit
    # Add 3 different items (only 2 should fit)
    update = InventoryUpdate(items_add=[
        ItemStack("iron_ore", 1),
        ItemStack("herb", 1),
        ItemStack("bread", 1)
    ])
    new_inv = InventoryService.apply_update(inv, update)
    assert len(new_inv.items) == 2
    
    # 2. Weight Limit
    # iron_ore weight is 2.0. max_weight 10.0.
    # Add 10 iron_ore. Only 5 should fit.
    inv_weight = InventoryComponent(max_slots=10, max_weight=10.0, items=[])
    update_weight = InventoryUpdate(items_add=[ItemStack("iron_ore", 10)])
    new_inv_weight = InventoryService.apply_update(inv_weight, update_weight)
    
    total_qty = sum(s.quantity for s in new_inv_weight.items)
    assert total_qty == 5
    
    print("\nSuccessfully verified inventory capacity limits (slots/weight).")

def test_entity_serialization_roundtrip():
    import json
    
    m1 = (V2EntityBuilder(1)
          .location(5.0, 5.0)
          .inventory(gold=100)
          .build())
    
    # Manually add an item for serialization check
    m1 = replace(m1, inventory=replace(m1.inventory, 
        items=[ItemStack("wood", 5, properties={"quality": "high"})]
    ))
    
    # Serialize to dict
    data = m1.to_dict()
    
    # Ensure nested structures are preserved
    assert data["inventory"]["gold"] == 100
    assert data["inventory"]["items"][0]["item_id"] == "wood"
    assert data["inventory"]["items"][0]["properties"]["quality"] == "high"
    
    # Mock "json" roundtrip with set handling
    def set_default(obj):
        from collections import deque
        if isinstance(obj, (set, deque)):
            return list(obj)
        # Handle enums
        from enum import Enum
        if isinstance(obj, Enum):
             return obj.value
        raise TypeError(f"Type {type(obj)} not serializable")
        
    js_str = json.dumps(data, default=set_default)
    loaded_data = json.loads(js_str)
    
    assert loaded_data["inventory"]["items"][0]["item_id"] == "wood"
    
    print("\nSuccessfully verified EntityState serialization roundtrip.")
