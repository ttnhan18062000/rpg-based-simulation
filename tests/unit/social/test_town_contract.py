"""
Town contract and economy tests.
- RPG-0034: shop_sell_price_enforcement
- RPG-0035: blacksmith_material_consumption
- RPG-1654: blacksmith_recipe_learning_parity
- RPG-1660: shop_junk_auto_sell
"""

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import (
    AuthoritativeState,
    InventoryComponent,
    IdentityComponent,
    ItemStack,
)
from src.core.updates import StateUpdate
from src.core.state import BuildingState
from src.core.registries import RecipeRegistry as LiveRecipeRegistry
from src.engine.pipeline import AuthoritativeApplyPipeline


ENTITY_ID = 1
SHOP_POS = (5, 5)
BLACKSMITH_POS = (5, 6)
STEEL_SWORD_RECIPE = "craft_steel_sword"


def _make_inventory(items=None, gold=100):
    return InventoryComponent(items=items or [], gold=gold)


def _make_actor(pos, inventory_component, identity_component=None):
    actor = (
        V2EntityBuilder(ENTITY_ID)
        .kind("hero")
        .location(*pos)
        .identity()
        .build()
    )

    actor = replace(actor, inventory=inventory_component)

    if identity_component is not None:
        actor = replace(actor, identity=identity_component)

    return actor


def _make_town_state(actor, pos, building_kind):
    building = BuildingState(
        id=10,
        kind=building_kind,
        position=pos,
        inventory=InventoryComponent(gold=1000),
    )

    return AuthoritativeState(
        tick=1,
        seed=42,
        entities={ENTITY_ID: actor},
        buildings={building.id: building},
        town_tiles={pos},
        building_tiles={pos: building_kind},
    )


def _refine(state):
    return AuthoritativeApplyPipeline.refine(
        state,
        StateUpdate(force_full_scan=True, entity_updates={}),
    )


def _get_entity_update(refined):
    return refined.entity_updates[ENTITY_ID]


def _removed_item_ids(inventory_update):
    return sorted([
        item.item_id if hasattr(item, "item_id") else item
        for item in inventory_update.items_remove
    ])


def _removed_item_ids_expanded(inventory_update):
    actual_removed = []

    for item in inventory_update.items_remove:
        item_id = item.item_id if hasattr(item, "item_id") else item
        quantity = item.quantity if hasattr(item, "quantity") else 1
        actual_removed.extend([item_id] * quantity)

    return sorted(actual_removed)


def _added_item_ids(inventory_update):
    return sorted([
        item.item_id if hasattr(item, "item_id") else item
        for item in inventory_update.items_add
    ])


def _assert_no_inventory_update(refined):
    assert (
        ENTITY_ID not in refined.entity_updates
        or refined.entity_updates[ENTITY_ID].inventory is None
    )


def test_shop_sell_price_enforcement():
    """Law of Value: Verify that selling items results in exactly the expected gold delta."""
    e_id = 1
    pos = (5, 5)

    inventory_component = InventoryComponent(
        items=[
            ItemStack("wood", 1),
            ItemStack("wood", 1),
        ],
        gold=100,
    )

    actor = (
        V2EntityBuilder(1)
        .kind("hero")
        .location(*pos)
        .identity()
        .build()
    )
    actor = replace(actor, inventory=inventory_component)

    shop = BuildingState(
        id=10,
        kind="shop",
        position=pos,
        inventory=InventoryComponent(gold=1000),
    )

    state = AuthoritativeState(
        tick=1,
        seed=42,
        entities={e_id: actor},
        buildings={shop.id: shop},
        town_tiles={pos},
        building_tiles={pos: "shop"},
    )

    update = StateUpdate(force_full_scan=True, entity_updates={})
    refined = AuthoritativeApplyPipeline.refine(state, update)

    e_upd = refined.entity_updates[e_id]

    assert e_upd.inventory is not None
    assert e_upd.inventory.gold_delta == 10

    actual_removed = sorted([
        i.item_id if hasattr(i, "item_id") else i
        for i in e_upd.inventory.items_remove
    ])
    assert actual_removed == ["wood", "wood"]


def test_shop_junk_auto_sell():
    """Law of Value: Verify only junk/materials are auto-sold."""
    inventory_component = _make_inventory(
        items=[
            ItemStack("wood", 1),
            ItemStack("steel_sword", 1),
            ItemStack("iron_sword", 1),
        ],
        gold=100,
    )
    actor = _make_actor(SHOP_POS, inventory_component)
    state = _make_town_state(actor, SHOP_POS, "shop")

    refined = _refine(state)
    e_upd = _get_entity_update(refined)

    actual_removed = _removed_item_ids(e_upd.inventory)
    assert actual_removed == ["iron_sword", "wood"]
    assert e_upd.inventory.gold_delta == 10


def test_blacksmith_material_consumption():
    """Law of Materials: Crafting must consume exact resources and gold."""
    inventory_component = _make_inventory(
        items=[
            ItemStack("iron_ore", 1),
            ItemStack("iron_ore", 1),
            ItemStack("wood", 1),
        ],
        gold=100,
    )
    identity_component = IdentityComponent(
        known_recipes={STEEL_SWORD_RECIPE},
        craft_target=STEEL_SWORD_RECIPE,
    )
    actor = _make_actor(BLACKSMITH_POS, inventory_component, identity_component)
    state = _make_town_state(actor, BLACKSMITH_POS, "blacksmith")

    refined = _refine(state)
    e_upd = _get_entity_update(refined)

    assert e_upd.inventory.gold_delta == -60
    assert _removed_item_ids_expanded(e_upd.inventory) == [
        "iron_ore",
        "iron_ore",
        "wood",
    ]

    actual_added = _added_item_ids(e_upd.inventory)
    assert actual_added == ["steel_sword"]
    assert e_upd.identity.craft_target == ""


def test_blacksmith_insufficient_materials():
    """Law of Materials: Crafting fails if materials are missing."""
    inventory_component = _make_inventory(
        items=[
            ItemStack("iron_ore", 1),
            ItemStack("wood", 1),
        ],
        gold=100,
    )
    identity_component = IdentityComponent(
        known_recipes={STEEL_SWORD_RECIPE},
        craft_target=STEEL_SWORD_RECIPE,
    )
    actor = _make_actor(BLACKSMITH_POS, inventory_component, identity_component)
    state = _make_town_state(actor, BLACKSMITH_POS, "blacksmith")

    refined = _refine(state)

    _assert_no_inventory_update(refined)


def test_blacksmith_insufficient_gold():
    """Law of Materials: Crafting fails if gold is missing."""
    inventory_component = _make_inventory(
        items=[
            ItemStack("iron_ore", 1),
            ItemStack("iron_ore", 1),
            ItemStack("wood", 1),
        ],
        gold=10,
    )
    identity_component = IdentityComponent(
        known_recipes={STEEL_SWORD_RECIPE},
        craft_target=STEEL_SWORD_RECIPE,
    )
    actor = _make_actor(BLACKSMITH_POS, inventory_component, identity_component)
    state = _make_town_state(actor, BLACKSMITH_POS, "blacksmith")

    refined = _refine(state)

    _assert_no_inventory_update(refined)


def test_blacksmith_unknown_recipe():
    """Law of Knowledge: Crafting fails if recipe is not known.

    BEFORE TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE, wholesale-learn populated
    recipes_learned from BlacksmithSystem.RECIPES's own private 14-entry craft_* list, so
    STEEL_SWORD_RECIPE (one of those 14) was itself a real member of the learned set.

    AFTER: wholesale-learn populates from the real, live registries.py::RecipeRegistry instead
    (TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE) -- STEEL_SWORD_RECIPE is not a member of that
    catalog (confirmed: none of BlacksmithSystem.RECIPES's 14 ids exist in the real catalog), so
    this test now asserts against a real registries.py id instead. craft_target is left as
    STEEL_SWORD_RECIPE deliberately -- the wholesale-learn branch `continue`s before reaching the
    craft_target-gated crafting-execution branch this tick (entity.identity.known_recipes was
    empty), so craft_target's value is irrelevant to what this test actually exercises.
    """
    inventory_component = _make_inventory(
        items=[
            ItemStack("iron_ore", 1),
            ItemStack("iron_ore", 1),
            ItemStack("wood", 1),
        ],
        gold=100,
    )
    identity_component = IdentityComponent(
        known_recipes=set(),
        craft_target=STEEL_SWORD_RECIPE,
    )
    actor = _make_actor(BLACKSMITH_POS, inventory_component, identity_component)
    state = _make_town_state(actor, BLACKSMITH_POS, "blacksmith")

    refined = _refine(state)

    e_upd = _get_entity_update(refined)
    assert "craft_iron_sword" in e_upd.identity.recipes_learned
    assert e_upd.inventory is None


def test_blacksmith_recipe_learning_parity():
    """Law of Knowledge: Recipe learning is wholesale on first visit.

    BEFORE TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE, wholesale-learn populated recipes_learned
    from BlacksmithSystem.RECIPES's own private 14-entry list, so the learned count was a fixed
    literal (14).

    AFTER: wholesale-learn populates from the real, live registries.py::RecipeRegistry
    (TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE) -- asserted generically against that registry's
    own live key set, not a hardcoded literal, so this test does not re-break the next time the
    real content catalog's recipe count changes.
    """
    inventory_component = InventoryComponent()
    identity_component = IdentityComponent(known_recipes=set())

    actor = _make_actor(BLACKSMITH_POS, inventory_component, identity_component)
    state = _make_town_state(actor, BLACKSMITH_POS, "blacksmith")

    refined = _refine(state)

    e_upd = _get_entity_update(refined)
    assert set(e_upd.identity.recipes_learned) == set(LiveRecipeRegistry.all().keys())