import pytest
from src_legacy.core.state import (
    EntityState, InventoryComponent, ItemStack, EquipSlot, ItemKind, AuthoritativeState
)
from src_legacy.core.updates import StateUpdate, EntityUpdate, InventoryUpdate, EquipmentUpdate
from src_legacy.engine.apply import ApplyPath

@pytest.mark.v2_contract
def test_inventory_stacking():
    # Initial state: 5 iron ore
    inventory = InventoryComponent(items=[ItemStack("iron_ore", 5)], gold=100)
    entity = EntityState(id=1, kind="hero", position=(0,0), inventory=inventory)
    state = StateUpdate() # Placeholder
    
    # Update: add 5 more iron ore
    ent_upd = EntityUpdate(
        entity_id=1, 
        inventory=InventoryUpdate(items_add=[ItemStack("iron_ore", 5)])
    )
    
    from src_legacy.core.state import AuthoritativeState
    prior_state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    state_upd = StateUpdate(entity_updates={1: ent_upd})
    
    new_state = ApplyPath.apply_generation(prior_state, state_upd)
    new_entity = new_state.entities[1]
    
    # Should be 10 iron ore in a single stack
    assert len(new_entity.inventory.items) == 1
    assert new_entity.inventory.items[0].item_id == "iron_ore"
    assert new_entity.inventory.items[0].quantity == 10

@pytest.mark.v2_contract
def test_inventory_capacity_limits():
    # Inventory with 1 slot used and 2 max slots
    inventory = InventoryComponent(
        items=[ItemStack("wood", 1)], 
        max_slots=2, 
        max_weight=10.0
    )
    entity = EntityState(id=1, kind="hero", position=(0,0), inventory=inventory)
    prior_state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # 1. Test Weight Limit (iron ore is 2.0 each, 10 iron ore = 20.0 weight)
    ent_upd_weight = EntityUpdate(
        entity_id=1, 
        inventory=InventoryUpdate(items_add=[ItemStack("iron_ore", 10)])
    )
    new_state_w = ApplyPath.apply_generation(prior_state, StateUpdate(entity_updates={1: ent_upd_weight}))
    # Should NOT have added the iron ore (weight limit 10.0, iron 20.0)
    assert len(new_state_w.entities[1].inventory.items) == 1
    assert new_state_w.entities[1].inventory.items[0].item_id == "wood"
    
    # 2. Test Slot Limit
    # Add iron ore (2.0) and bread (0.2). Both fit weight, but bread would take 3rd slot
    ent_upd_slots = EntityUpdate(
        entity_id=1, 
        inventory=InventoryUpdate(items_add=[ItemStack("iron_ore", 1), ItemStack("bread", 1)])
    )
    new_state_s = ApplyPath.apply_generation(prior_state, StateUpdate(entity_updates={1: ent_upd_slots}))
    # Should have added iron ore (2nd slot) but NOT bread (3rd slot)
    assert len(new_state_s.entities[1].inventory.items) == 2
    item_ids = [s.item_id for s in new_state_s.entities[1].inventory.items]
    assert "iron_ore" in item_ids
    assert "bread" not in item_ids

@pytest.mark.v2_contract
def test_equipment_and_gold_updates():
    entity = EntityState(id=1, kind="hero", position=(0,0))
    prior_state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    ent_upd = EntityUpdate(
        entity_id=1,
        inventory=InventoryUpdate(gold_delta=50),
        equipment=EquipmentUpdate(slot_updates={EquipSlot.MAIN_HAND: "iron_sword"})
    )
    
    new_state = ApplyPath.apply_generation(prior_state, StateUpdate(entity_updates={1: ent_upd}))
    new_entity = new_state.entities[1]
    
    assert new_entity.inventory.gold == 50
    assert new_entity.equipment.slots[EquipSlot.MAIN_HAND] == "iron_sword"
