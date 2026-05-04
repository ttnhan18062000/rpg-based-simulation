import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, BuildingState, InventoryComponent, ItemKind, ItemStack
from src.core.items import ItemRegistry, ItemDefinition
from src.town.shop import ShopService
from src.core.governance import RuntimeMode

@pytest.fixture
def base_state():
    # Ensure ItemRegistry has what we need
    # We already updated healing_potion in items.py to value=100
    
    shop = BuildingState(
        id=101, kind="shop", position=(0.0, 0.0), hp=100, functional=True
    )
    from src.core.builder import V2EntityBuilder
    entity = (V2EntityBuilder(1)
        .kind("hero")
        .at((0.5, 0.5))
        .with_inventory(gold=1000)
        .build()
    )
    
    return AuthoritativeState(
        tick=1, seed=42,
        entities={1: entity},
        buildings={101: shop}
    )

def test_normal_pricing(base_state):
    """Test pricing when pressure is zero."""
    res = ShopService.buy_item(base_state.entities[1], "healing_potion", 1, base_state)
    assert res is not None
    intent = res.entity_updates[1].resource_transfers[0]
    assert intent.gold_cost == 100
    assert intent.price_multiplier == 1.0

def test_pressure_scaling(base_state):
    """Test that price scales with global_salience."""
    state = replace(base_state, pressure_signals={"global_salience": 0.5})
    res = ShopService.buy_item(state.entities[1], "healing_potion", 1, state)
    assert res is not None
    intent = res.entity_updates[1].resource_transfers[0]
    assert intent.gold_cost == 150 # 100 * (1.0 + 0.5)
    assert intent.price_multiplier == 1.5

def test_price_cap_enforcement(base_state):
    """Test that price cap (3.0x) is enforced even if pressure is higher."""
    state = replace(base_state, pressure_signals={"global_salience": 3.5})
    res = ShopService.buy_item(state.entities[1], "healing_potion", 1, state)
    assert res is not None
    intent = res.entity_updates[1].resource_transfers[0]
    assert intent.gold_cost == 300 # Cap at 3.0x
    assert intent.price_multiplier == 3.0

def test_arbitrage_prevention(base_state):
    """Test that selling price remains static (half of base)."""
    state = replace(base_state, pressure_signals={"global_salience": 1.0})
    # Buy at 2.0x base (200)
    buy_res = ShopService.buy_item(state.entities[1], "healing_potion", 1, state)
    assert buy_res.entity_updates[1].resource_transfers[0].gold_cost == 200
    
    # Verify selling price calculation logic doesn't use pressure
    from src.systems.economy import DynamicPriceService
    sell_price = DynamicPriceService.calculate_sell_price(100)
    assert sell_price == 50
