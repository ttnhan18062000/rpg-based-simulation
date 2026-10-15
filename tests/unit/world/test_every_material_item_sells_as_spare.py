"""D79 step 1: a shop buys every item the content files under MATERIAL (no name list in the code); an item with no category does not compile."""
import inspect
from dataclasses import replace

import pytest

from src.core.items import ItemRegistry
from src.core.state import ItemStack
from src.engine import shop_sale
from src.engine.shop_sale import plan_sale, spare_quantity
from tests.unit.world.test_sell_is_a_chosen_act import _world


@pytest.fixture(autouse=True)
def _restore_registry():
    yield
    ItemRegistry.bootstrap({})


def test_a_material_the_old_list_never_named_sells_whole():
    state, ent, shop = _world([ItemStack("stone", 4), ItemStack("ancient_core", 1)])
    assert [(s.item_id, s.quantity) for s in plan_sale(state, ent, shop).items_remove] == [("stone", 4), ("ancient_core", 1)]


def test_a_catalog_material_sells_by_its_category_alone():
    ItemRegistry.bootstrap({"silver_ore": {"id": "silver_ore", "categories": ["material"], "base_value": 12}})
    state, ent, shop = _world([ItemStack("silver_ore", 3)])
    assert spare_quantity(ent, ent.inventory.items[0]) == 3
    assert plan_sale(state, ent, shop).items_remove == [ItemStack("silver_ore", 3)]


def test_an_item_with_no_category_is_a_compile_error():
    with pytest.raises(ValueError, match="no categories"):
        ItemRegistry.bootstrap({"mystery": {"id": "mystery", "categories": [], "base_value": 1}})


def test_an_item_the_registry_does_not_know_is_not_sold():
    state, ent, shop = _world([ItemStack("not_an_item", 3)])
    assert plan_sale(state, ent, shop) is None


def test_the_sale_code_names_no_item():
    source = inspect.getsource(shop_sale)
    assert not hasattr(shop_sale, "SELLABLE_MATERIALS")
    for literal in ("wood", "iron_ore", "fiber", "leather", "iron_sword"):
        assert f'"{literal}"' not in source


def test_a_tool_or_trinket_with_no_category_of_its_own_is_not_a_material_and_is_not_sold():
    ItemRegistry.bootstrap({"spanner": {"id": "spanner", "categories": ["tool"], "base_value": 20},
                            "charm": {"id": "charm", "categories": ["trinket", "holy"], "base_value": 60}})
    assert ItemRegistry.get("spanner").kind.value == "OTHER" and ItemRegistry.get("charm").kind.value == "OTHER"
    state, ent, shop = _world([ItemStack("spanner", 2), ItemStack("charm", 1)])
    assert plan_sale(state, ent, shop) is None


def test_the_shipped_tools_and_trinkets_resolve_to_no_sellable_kind():
    import yaml
    rows = yaml.safe_load(open("data/content/world/items.yaml"))
    ItemRegistry.bootstrap({row["id"]: row for row in rows})
    odd = [row["id"] for row in rows if set(row["categories"]) & {"tool", "trinket"} and not set(row["categories"]) & {"weapon", "armor", "material", "consumable"}]
    assert len(odd) == 4 and all(ItemRegistry.get(i).kind.value == "OTHER" for i in odd)
    assert all(ItemRegistry.get(row["id"]).kind.value == "MATERIAL" for row in rows if "material" in row["categories"])
