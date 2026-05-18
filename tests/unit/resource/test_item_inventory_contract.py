import pytest
from src.core.state import (
    EntityState, InventoryComponent, ItemStack, EquipSlot, ItemKind, AuthoritativeState
)
from src.core.updates import StateUpdate, EntityUpdate, InventoryUpdate, EquipmentUpdate
from src.engine.apply import ApplyPath

@pytest.mark.v2_contract
def test_inventory_stacking():
    # Initial state: 5 iron ore
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .inventory(gold=100, items=[ItemStack("iron_ore", 5)])
        .build())
    state = StateUpdate() # Placeholder
    
    # Update: add 5 more iron ore
    ent_upd = EntityUpdate(
        entity_id=1, 
        inventory=InventoryUpdate(items_add=[ItemStack("iron_ore", 5)])
    )
    
    from src.core.state import AuthoritativeState
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
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .inventory(items=[ItemStack("wood", 1)], max_slots=2, max_weight=10.0)
        .build())
    prior_state = AuthoritativeState(tick=1, seed=42, entities={1: entity})
    
    # 1. Test Weight Limit (iron ore is 2.0 each, 10 iron ore = 20.0 weight)
    ent_upd_weight = EntityUpdate(
        entity_id=1, 
        inventory=InventoryUpdate(items_add=[ItemStack("iron_ore", 10)])
    )
    new_state_w = ApplyPath.apply_generation(prior_state, StateUpdate(entity_updates={1: ent_upd_weight}))
    # Should have added 4 iron ore (8.0 weight) to reach 9.0 total, as 5 would exceed 10.0
    assert len(new_state_w.entities[1].inventory.items) == 2
    item_ids_w = [s.item_id for s in new_state_w.entities[1].inventory.items]
    assert "iron_ore" in item_ids_w
    assert any(s.item_id == "iron_ore" and s.quantity == 4 for s in new_state_w.entities[1].inventory.items)
    
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
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .build())
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
