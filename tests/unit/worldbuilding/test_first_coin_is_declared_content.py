"""EXCH-02 (owner decisions 34 and 37): starting coin is declared world content. Shops and inns start with a till and stock, every declared
inventory profile is applied to the entities of its archetype at compile, and the village labourer starts with no coin (no starting purse
standing in for earning). Amounts are the authored values (`merchant_trade_pack` 250, `blacksmith_toolkit` 80, `guard_basic_kit` 20 ...)."""
import collections
from functools import lru_cache

import pytest

from src.core.items import food_hunger_recovery
from tests.helpers.scenario import compile_world

pytestmark = [pytest.mark.domain("economy"), pytest.mark.level("unit")]

MEASURED = ["crowded_frontier", "frontier_living_world", "urban_political"]


@lru_cache(maxsize=None)
def _state(world):
    return compile_world(world, 42)


def _stock(building):
    return {s.item_id: s.quantity for s in building.inventory.items}


@pytest.mark.parametrize("world", MEASURED)
def test_shops_and_inns_start_with_a_till_and_stock_and_other_buildings_with_neither(world):
    for building in _state(world).buildings.values():
        if building.kind == "shop":
            assert building.inventory.gold == 250 and _stock(building) == {"travel_ration": 10, "wood": 10, "iron_ore": 5}
        elif building.kind == "inn":
            assert building.inventory.gold == 100 and _stock(building) == {"travel_ration": 20, "bread": 10}  # an inn has food to sell
        else:
            assert building.inventory.gold == 0 and not building.inventory.items


@pytest.mark.parametrize("world", MEASURED)
def test_declared_inventory_profiles_are_applied_by_role(world):
    gold = collections.Counter()
    for entity in _state(world).entities.values():
        props = entity.identity.properties or {}
        gold[(props.get("faction_id"), entity.identity.role.name, entity.inventory.gold)] += 1
    assert gold[("merchant_league", "SHOPKEEPER", 250)] == 3  # trade capital (merchant_trade_pack)
    assert gold[("town_council", "GUARD", 20)] == 5  # guard_basic_kit
    assert gold[("town_council", "WORKER", 80)] == 1  # the blacksmith's toolkit purse


@pytest.mark.parametrize("world", MEASURED)
def test_the_village_labourer_starts_with_no_coin_and_no_goods(world):
    labourers = [e for e in _state(world).entities.values()
                 if (e.identity.properties or {}).get("faction_id") == "town_council" and e.identity.role.name == "WORKER" and e.inventory.gold == 0]
    assert len(labourers) == 8 and all(not e.inventory.items for e in labourers)


@pytest.mark.parametrize("world", MEASURED)
def test_the_only_food_entering_through_profiles_is_the_merchants_rations(world):
    food = collections.Counter()
    for entity in _state(world).entities.values():
        for stack in entity.inventory.items:
            if food_hunger_recovery(stack.item_id) > 0.0:
                food[(entity.identity.role.name, stack.item_id)] += stack.quantity
    assert dict(food) == {("SHOPKEEPER", "travel_ration"): 15}  # 3 merchants x 5 rations


def test_crowded_frontier_has_a_forage_node_owned_by_a_hazard_free_near_edge_region():
    """Decision 35: crowded_frontier's lack of wild land was an oversight; the forest edge beside its settlement holds a thicket."""
    from src.engine.legality import LegalityServiceV2
    state = _state("crowded_frontier")
    nodes = [n for n in state.resource_nodes.values() if food_hunger_recovery(n.yields_item) > 0.0]
    assert len(nodes) == 1 and nodes[0].max_charges == 10
    owner = LegalityServiceV2.get_region_for_position(nodes[0].position, state)
    assert owner.id == "forest_edge" and owner.kind == "WILDERNESS" and owner.hazard_level == 0.0


def test_region_ids_are_unique_across_all_world_modules():
    """A region id declared by two modules collides when both are composed (the near_forest/wolf_den case); the new forest_edge must be unique."""
    import glob
    import yaml
    ids = collections.Counter()
    for path in glob.glob("data/content/world_modules/*.yaml"):
        for region in (yaml.safe_load(open(path)) or {}).get("regions") or []:
            ids[region["id"]] += 1
    assert ids["forest_edge"] == 1
