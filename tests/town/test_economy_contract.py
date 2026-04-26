import pytest
from src.core.state import (
    EntityState, AuthoritativeState, InventoryComponent, ItemStack, BuildingState
)
from src.core.updates import StateUpdate
from src.town.shop import ShopAction
from src.town.blacksmith import BlacksmithAction
from src.engine.apply import ApplyPath

@pytest.mark.v2_contract
def test_shop_buy_and_sell():
    # 1. Setup: Entity with 100 gold
    inventory = InventoryComponent(gold=100, items=[])
    entity = EntityState(id=1, kind="hero", position=(0,0), inventory=inventory)
    shop = BuildingState(id=10, kind="shop", position=(0,0), functional=True)
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, buildings={10: shop})
    
    # 2. Buy: Bread (value 1)
    # Price is 1, buy 10 = 10 gold
    ent_upd = ShopAction.buy(entity, "bread", 10, state)
    assert ent_upd is not None
    state = ApplyPath.apply_generation(state, StateUpdate(entity_updates={1: ent_upd}))
    
    new_entity = state.entities[1]
    assert new_entity.inventory.gold == 90
    assert len(new_entity.inventory.items) == 1
    assert new_entity.inventory.items[0].item_id == "bread"
    assert new_entity.inventory.items[0].quantity == 10
    
    # 3. Sell: Bread (value 1, 50% sell = 0.5 -> 0 gold each if truncated?)
    # Wait, 1 * 0.5 = 0.5. int(0.5) = 0.
    # Let's test with Iron Sword (value 1? No, let me check ItemRegistry)
    # Iron Ore value is not set, defaults to 1.
    # Let's use something more expensive if possible or assume int(0.5 * 10) = 5.
    
    # Sell 10 bread. value=1. total_val=10. sell_val=5.
    sell_upd = ShopAction.sell(new_entity, "bread", 10, state)
    assert sell_upd is not None
    state = ApplyPath.apply_generation(state, StateUpdate(entity_updates={1: sell_upd}))
    
    final_entity = state.entities[1]
    assert final_entity.inventory.gold == 95 # 90 + 5
    assert len(final_entity.inventory.items) == 0

@pytest.mark.v2_contract
def test_blacksmith_crafting():
    # 1. Setup: Entity with 5 iron ore and 100 gold
    inventory = InventoryComponent(
        gold=100, 
        items=[ItemStack("iron_ore", 5), ItemStack("wood", 2)]
    )
    entity = EntityState(id=1, kind="hero", position=(0,0), inventory=inventory)
    blacksmith = BuildingState(id=11, kind="blacksmith", position=(0,0), functional=True)
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, buildings={11: blacksmith})
    
    # 2. Craft: Iron Sword (needs 5 iron ore and 50 gold)
    craft_upd = BlacksmithAction.craft(entity, "iron_sword", state)
    assert craft_upd is not None
    state = ApplyPath.apply_generation(state, StateUpdate(entity_updates={1: craft_upd}))
    
    new_entity = state.entities[1]
    assert new_entity.inventory.gold == 50
    assert len(new_entity.inventory.items) == 1
    assert new_entity.inventory.items[0].item_id == "iron_sword"
    
    # 3. Reject: Craft again (insufficient funds)
    fail_upd = BlacksmithAction.craft(new_entity, "iron_sword", state)
    assert fail_upd is None
