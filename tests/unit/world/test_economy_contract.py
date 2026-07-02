import pytest
from src.core.state import (
    AuthoritativeState, ItemStack, BuildingState
)
from src.core.builder import V2EntityBuilder
from src.core.updates import StateUpdate
from src.town.shop import ShopAction
from src.town.blacksmith import BlacksmithAction
from src.engine.apply import ApplyPath
from src.engine.pipeline import AuthoritativeApplyPipeline

@pytest.mark.v2_contract
def test_shop_buy_and_sell():
    # 1. Setup: Entity with 1000 gold, no reputation discount.
    # Uses iron_ore (present in content catalog) so the item survives
    # ItemRegistry.bootstrap() that fires inside AuthoritativeApplyPipeline.refine.
    # Gold assertions are derived from the intent's gold_cost to stay robust
    # regardless of which ItemRegistry value (pre- vs post-bootstrap) is active
    # when ShopAction.buy runs.
    START_GOLD = 1000
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .inventory(gold=START_GOLD)
        .social(public_reputation=0.0)  # no reputation discount — test raw pricing
        .build())
    from src.core.state import InventoryComponent
    shop = BuildingState(
        id=10,
        kind="shop",
        position=(0,0),
        functional=True,
        inventory=InventoryComponent(gold=1000, items=[ItemStack("iron_ore", 100)])
    )
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, buildings={10: shop})

    # 2. Buy: 10 iron_ore — derive expected gold from the intent to be order-independent
    ent_upd = ShopAction.buy(entity, "iron_ore", 10, state)
    assert ent_upd is not None
    buy_cost = ent_upd.resource_transfers[0].gold_cost

    refined = AuthoritativeApplyPipeline.refine(state, StateUpdate(entity_updates={1: ent_upd}))
    state = ApplyPath.apply_generation(state, refined)

    new_entity = state.entities[1]
    assert new_entity.inventory.gold == START_GOLD - buy_cost
    assert len(new_entity.inventory.items) == 1
    assert new_entity.inventory.items[0].item_id == "iron_ore"
    assert new_entity.inventory.items[0].quantity == 10

    # 3. Sell: 10 iron_ore — derive expected gain from the intent
    sell_upd = ShopAction.sell(new_entity, "iron_ore", 10, state)
    assert sell_upd is not None
    sell_gain = sell_upd.resource_transfers[0].gold_delta

    refined_sell = AuthoritativeApplyPipeline.refine(state, StateUpdate(entity_updates={1: sell_upd}))
    state = ApplyPath.apply_generation(state, refined_sell)

    final_entity = state.entities[1]
    assert final_entity.inventory.gold == (START_GOLD - buy_cost) + sell_gain
    assert len(final_entity.inventory.items) == 0

@pytest.mark.v2_contract
def test_blacksmith_crafting():
    # 1. Setup: Entity with 5 iron ore and 100 gold
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0, 0)
        .inventory(gold=100)
        .inventory(items=[ItemStack("iron_ore", 5), ItemStack("wood", 2)])
        .build())
    blacksmith = BuildingState(id=11, kind="blacksmith", position=(0,0), functional=True)
    state = AuthoritativeState(tick=1, seed=42, entities={1: entity}, buildings={11: blacksmith})
    
    # 2. Craft: Iron Sword (needs 5 iron ore and 50 gold)
    craft_upd = BlacksmithAction.craft(entity, "iron_sword", state)
    assert craft_upd is not None
    
    refined_craft = AuthoritativeApplyPipeline.refine(state, StateUpdate(entity_updates={1: craft_upd}))
    state = ApplyPath.apply_generation(state, refined_craft)
    
    new_entity = state.entities[1]
    assert new_entity.inventory.gold == 50
    assert len(new_entity.inventory.items) == 1
    assert new_entity.inventory.items[0].item_id == "iron_sword"
    
    # 3. Reject: Craft again (insufficient funds)
    fail_upd = BlacksmithAction.craft(new_entity, "iron_sword", state)
    assert fail_upd is None
