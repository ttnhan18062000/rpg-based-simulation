"""D79 step 2: the catalog's base_value is the only price source; the market names no item and parses no item name for its kind."""
import inspect

import pytest

from src.core.items import ItemRegistry
from src.core.state import ItemStack
from src.systems.economy_systems import market
from src.systems.economy_systems.market import UNKNOWN_ITEM_BASE_VALUE, MarketSystem
from tests.unit.world.test_sell_is_a_chosen_act import _world


@pytest.fixture(autouse=True)
def _restore_registry():
    yield
    ItemRegistry.bootstrap({})


def _content(**values):
    ItemRegistry.bootstrap({k: {"id": k, "categories": [cat], "base_value": v} for k, (cat, v) in values.items()})


def test_the_base_value_is_the_catalog_value_not_a_table():
    _content(iron_ore=("material", 12), herb=("material", 3), iron_sword=("weapon", 80))
    assert [MarketSystem.get_item_base_value(i) for i in ("iron_ore", "herb", "iron_sword")] == [12.0, 3.0, 80.0]


def test_only_an_item_the_catalog_does_not_know_defaults():
    _content(stone=("material", 2))
    assert MarketSystem.get_item_base_value("not_an_item") == UNKNOWN_ITEM_BASE_VALUE


def test_a_declared_zero_value_is_zero_not_the_default():
    _content(grass_cover=("consumable", 0))
    assert MarketSystem.get_item_base_value("grass_cover") == 0.0


def test_the_kind_a_price_modifier_keys_on_is_the_content_kind_not_a_name_parse():
    _content(odd_sword_ore=("material", 4), blade=("weapon", 9))
    assert MarketSystem.get_item_kind("odd_sword_ore") == "MATERIAL"  # a name containing "sword" and "ore" is still a material
    assert MarketSystem.get_item_kind("blade") == "WEAPON" and MarketSystem.get_item_kind("nothing") == "OTHER"


def test_the_price_is_the_catalog_value_times_the_existing_modifiers():
    _content(iron_ore=("material", 12))
    state, ent, shop = _world([ItemStack("iron_ore", 1)])
    assert MarketSystem.calculate_price(state, shop, "iron_ore", is_buy=True) == int(12 * 1.2)
    assert MarketSystem.calculate_price(state, shop, "iron_ore", is_buy=False) == int(12 * 0.8)


def test_the_market_names_no_item():
    source = inspect.getsource(market)
    for literal in ("iron_ore", "steel_ore", "iron_sword", "herb", "health_potion", "leather", "cloth", '"sword"', '"plate"', '"potion"'):
        assert literal not in source


def test_a_catalog_item_without_a_base_value_fails_to_compile():
    from pydantic import ValidationError

    from src.content.schema import ItemDefinition

    with pytest.raises(ValidationError, match="base_value"):
        ItemDefinition(id="x", display_name="X", categories=["material"])
    assert ItemDefinition(id="x", display_name="X", categories=["material"], base_value=0).base_value == 0.0
