import pytest
from src.core.state import AuthoritativeState, EntityState, BuildingState, InventoryComponent, ItemStack
from src.town.shop import ShopService
from src.town.blacksmith import BlacksmithService

def test_shop_buy():
    entity = EntityState(
        id=1, kind="HERO", position=(10, 10),
        inventory=InventoryComponent(gold=100)
    )
    shop = BuildingState(id=1, kind="shop", position=(10, 10))
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: entity},
        buildings={1: shop}
    )
    
    # Buy healing_potion (Value 1)
    update = ShopService.buy_item(entity, "healing_potion", 2, state)
    
    assert update is not None
    ent_upd = update.entity_updates[1]
    assert ent_upd.inventory.gold_delta == -2 # Value is 1 in registry
    assert ent_upd.inventory.items_add[0].item_id == "healing_potion"

def test_blacksmith_craft():
    entity = EntityState(
        id=1, kind="HERO", position=(5, 5),
        inventory=InventoryComponent(
            gold=100,
            items=[
                ItemStack("iron_ore", 10),
                ItemStack("wood", 5)
            ]
        )
    )
    blacksmith = BuildingState(id=2, kind="blacksmith", position=(5, 5))
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: entity},
        buildings={2: blacksmith}
    )
    
    # Craft iron_sword (Materials: 5 iron_ore, 2 wood)
    update = BlacksmithService.craft_item(entity, "iron_sword", state)
    
    assert update is not None
    ent_upd = update.entity_updates[1]
    # Check removals
    mats_rem = {s.item_id: s.quantity for s in ent_upd.inventory.items_remove}
    assert mats_rem["iron_ore"] == 5
    assert mats_rem["wood"] == 2
    # Check addition
    assert ent_upd.inventory.items_add[0].item_id == "iron_sword"
