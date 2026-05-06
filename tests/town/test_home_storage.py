import pytest
from src.core.state import AuthoritativeState, InventoryComponent, ItemStack
from src.core.builder import V2EntityBuilder
from src.town.home_storage import HomeStorageService

def test_transfer_to_home():
    # Setup entity with item
    entity = (V2EntityBuilder(1)
        .kind("HERO")
        .location(0, 0) # At town center
        .item("iron_ore", 5)
        .build())
    
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: entity},
        town_center=(0, 0),
        home_storage={}
    )
    
    # Move 3 iron ore to home
    update = HomeStorageService.transfer_to_home(entity, "iron_ore", 3, state)
    
    assert update is not None
    # Check inventory intent (remove 3)
    ent_upd = update.entity_updates[1]
    assert len(ent_upd.resource_transfers) == 1
    intent = ent_upd.resource_transfers[0]
    assert intent.items_remove[0].quantity == 3
    assert intent.transfer_kind == "DEPOSIT"

def test_transfer_from_home():
    # Setup home storage with item
    home_inv = InventoryComponent(items=[ItemStack("wood", 10)])
    entity = (V2EntityBuilder(1)
        .kind("HERO")
        .location(0, 0)
        .build())
    
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: entity},
        town_center=(0, 0),
        home_storage={1: home_inv}
    )
    
    # Move 5 wood from home
    update = HomeStorageService.transfer_from_home(entity, "wood", 5, state)
    
    assert update is not None
    # Check inventory intent (add 5)
    ent_upd = update.entity_updates[1]
    assert len(ent_upd.resource_transfers) == 1
    intent = ent_upd.resource_transfers[0]
    assert intent.items_add[0].quantity == 5
    assert intent.transfer_kind == "WITHDRAW"
