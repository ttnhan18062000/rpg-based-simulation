"""EXCH-02 (owner decision 34): SELL. A subject chooses to sell (the SELL step, then the SELL action at a shop); the shop pays out of its own
purse at MarketSystem's price per unit; coins and goods are conserved; gear stays with its owner; food is sold only as surplus."""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.conservation import ResourceTransactionResolver
from src.core.enums import ReasonCode
from src.core.models.inventory import EquipSlot
from src.core.state import AuthoritativeState, BuildingState, InventoryComponent, ItemStack
from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
from src.engine.shop_sale import FOOD_KEPT_HUNGER_RECOVERY, plan_sale, spare_quantity, unit_price
from src.engine.domain.action_router import ActionRouter
from src.systems.economy_systems.market import MarketSystem


def _world(items, shop_gold=1000, pos=(5.0, 6.0), gold=0):
    shop = BuildingState(id=10, kind="shop", position=(5.0, 5.0), functional=True, inventory=InventoryComponent(gold=shop_gold))
    ent = V2EntityBuilder(1).kind("worker").properties({"species_id": "human"}).location(*pos).inventory(gold=gold).social(public_reputation=0.0).build()
    ent = replace(ent, inventory=replace(ent.inventory, items=list(items)))
    state = AuthoritativeState(tick=1, seed=1, entities={1: ent}, buildings={10: shop}, town_tiles={(5, 5), (5, 6), (5, 4), (4, 5), (6, 5)})
    return state, ent, shop


def test_the_sale_is_priced_per_unit_by_market_system_times_the_quantity():
    state, ent, shop = _world([ItemStack("wood", 5)])
    sale = plan_sale(state, ent, shop)
    assert sale.source_kind == "SHOP_SELL" and sale.items_remove == [ItemStack("wood", 5)]
    assert sale.gold_delta == 5 * MarketSystem.calculate_price(state, shop, "wood", is_buy=False)  # not one price for the whole stack


def test_the_shop_never_pays_more_than_its_purse_and_the_coin_comes_out_of_it():
    state, ent, shop = _world([ItemStack("wood", 5)], shop_gold=3)
    price = unit_price(state, shop, "wood")
    sale = plan_sale(state, ent, shop)
    assert sale.items_remove == [ItemStack("wood", 3 // price)] and sale.gold_delta == (3 // price) * price
    result = ResourceTransactionResolver.resolve(state, ent, sale, reservations={})
    assert result.accepted and result.inventory_update.gold_delta == sale.gold_delta
    assert result.building_update.inventory.gold_delta == -sale.gold_delta  # total coin is conserved


def test_an_empty_shop_purse_buys_nothing():
    state, ent, shop = _world([ItemStack("wood", 5)], shop_gold=0)
    assert plan_sale(state, ent, shop) is None


def test_gear_stays_with_its_owner_and_only_the_surplus_sells():
    state, ent, shop = _world([ItemStack("iron_sword", 1), ItemStack("wood", 2)])
    ent = replace(ent, equipment=replace(ent.equipment, slots={EquipSlot.MAIN_HAND: "iron_sword"}))
    assert [s.item_id for s in plan_sale(state, ent, shop).items_remove] == ["wood"]  # the equipped sword stays
    ent = replace(ent, inventory=replace(ent.inventory, items=[ItemStack("iron_sword", 3)]))
    assert plan_sale(state, ent, shop).items_remove == [ItemStack("iron_sword", 2)]  # a spare sword sells, the last one does not


def test_food_is_sold_only_as_surplus_over_one_meals_worth():
    state, ent, shop = _world([ItemStack("wild_berries", 5)])
    kept = 2  # 2 berries of 30 hunger = FOOD_KEPT_HUNGER_RECOVERY (60)
    assert FOOD_KEPT_HUNGER_RECOVERY == 60.0 and spare_quantity(ent, ent.inventory.items[0]) == 5 - kept
    assert plan_sale(state, ent, shop).items_remove == [ItemStack("wild_berries", 5 - kept)]
    state, ent, shop = _world([ItemStack("wild_berries", 2)])
    assert plan_sale(state, ent, shop) is None  # one meal's worth is not surplus


def test_the_sell_action_at_a_shop_attaches_the_sale_when_it_executes():
    state, ent, shop = _world([ItemStack("wood", 4)])
    out = ActionRouter.execute_action(ent, {"action": "SELL", "target_id": 10}, state.tick, None, state)[1]
    (sale,) = [t for t in out.resource_transfers if t.source_kind == "SHOP_SELL"]
    assert sale.items_remove == [ItemStack("wood", 4)]


def test_no_sale_without_the_sell_action_and_none_away_from_a_shop():
    state, ent, shop = _world([ItemStack("wood", 4)])
    assert not [t for t in ActionRouter.execute_action(ent, {"action": "REST"}, state.tick, None, state)[1].resource_transfers if t.source_kind == "SHOP_SELL"]
    far, ent_far, _ = _world([ItemStack("wood", 4)], pos=(5.0, 9.0))
    assert not ActionRouter.execute_action(ent_far, {"action": "SELL", "target_id": 10}, far.tick, None, far)[1].resource_transfers


def test_the_sell_step_opens_only_for_a_subject_with_goods_a_funded_shop_would_buy():
    from src.ai.goals.base import OpeningStepKind
    from src.ai.goals.opening_steps import opening_steps
    state, ent, shop = _world([ItemStack("wood", 4)])
    step = next(s for s in opening_steps(ent, state) if s.kind is OpeningStepKind.EARN_THEN_BUY)
    assert step.available and step.target_id == "10" and step.target_pos == (5.0, 5.0)
    empty = replace(state, buildings={10: replace(shop, inventory=InventoryComponent(gold=0))})
    step = next(s for s in opening_steps(ent, empty) if s.kind is OpeningStepKind.EARN_THEN_BUY)
    assert not step.available and step.reason
