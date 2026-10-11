"""TCK-20261007-SHOP-AND-BLACKSMITH-TOWN-PATHS-NEVER-RAN-IN-A-COMPILED-WORLD (shop half): `ShopSystem.enforce` found its shop through
`state.building_tiles`, which is empty in every compiled world, so the auto-sell and the buy price floor never ran. The shop is now found
through `service_reach` (a subject on a shop tile or orthogonally beside one is at the shop), and a purchase is priced by MarketSystem
(Bible 03 section 4)."""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState, InventoryComponent, ItemStack
from src.core.updates import EntityUpdate, StateUpdate
from src.engine.shop import ShopSystem
from src.systems.economy_systems.market import MarketSystem
from src.town.shop import ShopService


def _world(entity_pos, shop_gold=0, shop_stock=()):
    shop = BuildingState(id=10, kind="shop", position=(5.0, 5.0), functional=True,
                         inventory=InventoryComponent(gold=shop_gold, items=list(shop_stock)))
    ent = V2EntityBuilder(1).kind("worker").location(*entity_pos).inventory(gold=0).social(public_reputation=0.0).build()
    ent = replace(ent, inventory=replace(ent.inventory, items=[ItemStack("wood", 3)]))
    state = AuthoritativeState(tick=1, seed=1, entities={1: ent}, buildings={10: shop})  # building_tiles stays empty, as in a compiled world
    return state, ent


def _enforce(state, ent):
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, new_position=ent.navigation.position)})
    return ShopSystem.enforce(state, update).entity_updates[1]


def test_standing_beside_the_shop_sells_nothing(): 
    """Selling is a chosen act (the SELL action); the shop system no longer sells for whoever is beside it."""
    state, ent = _world((5.0, 6.0), shop_gold=1000)
    assert not [t for t in _enforce(state, ent).resource_transfers if t.source_kind == "SHOP_SELL"]


def test_a_purchase_is_priced_by_market_system():
    state, ent = _world((5.0, 6.0), shop_gold=0, shop_stock=[ItemStack("iron_ore", 10)])
    ent = replace(ent, inventory=replace(ent.inventory, gold=1000))
    state = replace(state, entities={1: ent})
    update = ShopService.buy_item(ent, "iron_ore", 2, state)
    (buy,) = update.entity_updates[1].resource_transfers
    assert buy.gold_cost == MarketSystem.calculate_price(state, state.buildings[10], "iron_ore", is_buy=True) * 2
