import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, BuildingState, InventoryComponent, ItemKind, ItemStack
from src.core.items import ItemRegistry, ItemDefinition
from src.town.shop import ShopService
from src.core.governance import RuntimeMode

@pytest.fixture
def base_state():
    # Ensure healing_potion (value=100) is always in ItemRegistry regardless of
    # whether ItemRegistry.bootstrap() has been called by another test.
    # bootstrap() replaces _items with catalog content which omits healing_potion;
    # re-registering here makes these pricing tests order-independent.
    ItemRegistry._items["healing_potion"] = ItemDefinition(
        id="healing_potion", name="Healing Potion",
        kind=ItemKind.CONSUMABLE, weight=0.5, value=100,
        properties={"heal_amount": 50}
    )

    shop = BuildingState(
        id=101, kind="shop", position=(0.0, 0.0), hp=100, functional=True
    )
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .location(0.5, 0.5)
        .inventory(gold=1000)
        .social(public_reputation=0.0)  # no reputation discount — test raw pricing
        .build()
    )

    return AuthoritativeState(
        tick=1, seed=42,
        entities={1: entity},
        buildings={101: shop}
    )

def _market_buy_price(state):
    """What MarketSystem (the authoritative price law, Bible 03 section 4) charges for one healing potion at the shop."""
    from src.systems.economy_systems.market import MarketSystem
    return MarketSystem.calculate_price(state, state.buildings[101], "healing_potion", is_buy=True)


def test_normal_pricing(base_state):
    """Test pricing when pressure is zero."""
    res = ShopService.buy_item(base_state.entities[1], "healing_potion", 1, base_state)
    assert res is not None
    intent = res.entity_updates[1].resource_transfers[0]
    expected = _market_buy_price(base_state)
    assert intent.gold_cost == expected
    assert intent.price_multiplier == expected / 100

def test_buy_price_ignores_a_stale_salience_entry(base_state):
    """Reversed by TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING. The buy price used to be scaled by
    `1 + global_salience` (a pressure signal built from measured compute time), so the same seed on a slower host
    paid more. The price is now the item's base value; a leftover `global_salience` entry changes nothing."""
    for salience in (0.0, 0.5, 1.0, 3.5):
        state = replace(base_state, pressure_signals={"global_salience": salience})
        res = ShopService.buy_item(state.entities[1], "healing_potion", 1, state)
        assert res is not None
        intent = res.entity_updates[1].resource_transfers[0]
        assert intent.gold_cost == _market_buy_price(base_state), salience
        assert intent.price_multiplier == _market_buy_price(base_state) / 100, salience


def test_arbitrage_prevention(base_state):
    """Test that selling price remains static (half of base)."""
    state = replace(base_state, pressure_signals={"global_salience": 1.0})
    # Buy at MarketSystem's price (Bible 03 section 4); the stale salience entry no longer scales it
    buy_res = ShopService.buy_item(state.entities[1], "healing_potion", 1, state)
    assert buy_res.entity_updates[1].resource_transfers[0].gold_cost == _market_buy_price(base_state)
    
    # Verify selling price calculation logic doesn't use pressure
    from src.systems.economy import DynamicPriceService
    sell_price = DynamicPriceService.calculate_sell_price(100)
    assert sell_price == 50
