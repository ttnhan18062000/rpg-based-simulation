import pytest
from src.core.state import InventoryComponent, ItemStack, AuthoritativeState, EntityState
from src.core.updates import StateUpdate, EntityUpdate, InventoryUpdate
from src.engine.apply import ApplyPath
from src.core.inventory import InventoryService

def test_inventory_stack_size_enforcement():
    """
    Law: Items must respect the stack_size defined in ItemDefinition.
    Proof: Adding items beyond stack_size should create a new stack or be rejected if no slots.
    RPG-1649: inventory_slots_and_weight
    RPG-0031: item_inventory_contract
    """
    # 1. Setup: 18 iron ore in inventory (stack_size is 20)
    # Slots: 1/2 used
    inv = InventoryComponent(items=[ItemStack("iron_ore", 18)], max_slots=2, max_weight=100.0)
    entity = EntityState(id=1, kind="HERO", position=(0,0), inventory=inv)
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # 2. Update: Add 5 more iron ore. 
    # Total would be 23. 20 in first stack, 3 in second stack.
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, inventory=InventoryUpdate(items_add=[ItemStack("iron_ore", 5)]))
    })
    
    refined = ApplyPath.apply_generation(state, update)
    new_inv = refined.entities[1].inventory
    
    # CURRENT FAIL: It likely puts 23 in one stack because InventoryService doesn't check stack_size
    assert len(new_inv.items) == 2
    assert new_inv.items[0].quantity == 20
    assert new_inv.items[1].quantity == 3

def test_inventory_weight_preservation_delta():
    """
    Law: Inventory weight must be preserved and validated during deltas.
    """
    # Max weight 5.0. Current weight 4.0 (2 iron ore * 2.0)
    inv = InventoryComponent(items=[ItemStack("iron_ore", 2)], max_slots=10, max_weight=5.0)
    entity = EntityState(id=1, kind="HERO", position=(0,0), inventory=inv)
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # Adding 1 more iron ore (2.0) should fail as it exceeds 5.0
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, inventory=InventoryUpdate(items_add=[ItemStack("iron_ore", 1)]))
    })
    
    refined = ApplyPath.apply_generation(state, update)
    new_inv = refined.entities[1].inventory
    
    # Should still be 2 iron ore
    assert len(new_inv.items) == 1
    assert new_inv.items[0].quantity == 2

def test_partial_stack_fill_before_slot_rejection():
    """
    Law: Near-full stacks should be filled to capacity before rejecting due to slot limits.
    """
    # 1. Setup: 1 slot used (19 iron_ore), 1 slot remaining. Stack size 20.
    inv = InventoryComponent(items=[ItemStack("iron_ore", 19)], max_slots=2, max_weight=100.0)
    entity = EntityState(id=1, kind="HERO", position=(0,0), inventory=inv)
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # 2. Add 2 iron ore and 1 wood.
    # Iron ore: 1 goes to first stack (fills it), 1 goes to second slot.
    # Wood: No slots left, so wood is rejected.
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, inventory=InventoryUpdate(items_add=[
            ItemStack("iron_ore", 2),
            ItemStack("wood", 1)
        ]))
    })
    
    refined = ApplyPath.apply_generation(state, update)
    new_inv = refined.entities[1].inventory
    
    # Should have 2 iron_ore stacks (20 and 1) and NO wood
    assert len(new_inv.items) == 2
    assert any(s.item_id == "iron_ore" and s.quantity == 20 for s in new_inv.items)
    assert any(s.item_id == "iron_ore" and s.quantity == 1 for s in new_inv.items)
    assert not any(s.item_id == "wood" for s in new_inv.items)
