import pytest
from src.core.state import AuthoritativeState, BuildingState, ItemStack
from src.core.builder import V2EntityBuilder
from src.town.shop import ShopService
from src.town.blacksmith import BlacksmithService

def test_shop_buy():
    entity = (V2EntityBuilder(1)
        .kind("HERO")
        .location(10, 10)
        .gold(100)
        .build())
    shop = BuildingState(id=1, kind="shop", position=(10, 10))
    state = AuthoritativeState(
        tick=100, seed=42,
        entities={1: entity},
        buildings={1: shop}
    )
    
    # Buy bread (Value 1)
    update = ShopService.buy_item(entity, "bread", 2, state)
    
    assert update is not None
    ent_upd = update.entity_updates[1]
    assert ent_upd.resource_transfers is not None
    assert ent_upd.resource_transfers[0].gold_cost == 2
    assert ent_upd.resource_transfers[0].items_add[0].item_id == "bread"

def test_blacksmith_craft():
    entity = (V2EntityBuilder(1)
        .kind("HERO")
        .location(5, 5)
        .gold(100)
        .item("iron_ore", 10)
        .item("wood", 5)
        .build())
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
    # Check intent
    assert len(ent_upd.resource_transfers) == 1
    intent = ent_upd.resource_transfers[0]
    mats_rem = {s.item_id: s.quantity for s in intent.items_remove}
    assert mats_rem["iron_ore"] == 5
    assert mats_rem["wood"] == 2
    assert intent.items_add[0].item_id == "iron_sword"
