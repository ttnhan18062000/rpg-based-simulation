"""Crafting gates and atomicity proven on the live path: ``ActionIntentAdapter.execute`` (REQUEST_CRAFT)
checks the requirements and builds the CRAFTING intent; ``AuthoritativeApplyPipeline.refine`` and
``ApplyPath.apply_generation`` resolve it (``ResourceTransactionResolver``). Replaces the proof that ran
the retired ``CraftingSystem.craft()`` (PROG-097..101, PROG-107).
"""
from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.registries import RecipeRegistry
from src.core.state import AuthoritativeState, ItemStack
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath
from src.engine.intent.action_intent import ActionIntent, ActionIntentAdapter
from src.engine.pipeline import AuthoritativeApplyPipeline

RECIPE = "craft_iron_sword"  # 2 iron_ore + 1 wood + 40 gold -> iron_sword (checked below, not assumed)


def _state(*, gold=100, items=None, known=(RECIPE,), max_slots=None):
    items = [ItemStack("iron_ore", 2), ItemStack("wood", 1)] if items is None else items
    entity = V2EntityBuilder(1).kind("hero").location(0, 0).inventory(gold=gold, items=items).build()
    entity = replace(entity, identity=replace(entity.identity, known_recipes=set(known)))
    if max_slots is not None:
        entity = replace(entity, inventory=replace(entity.inventory, max_slots=max_slots))
    return AuthoritativeState(tick=1, seed=42, entities={1: entity})


def _craft(state, recipe_id=RECIPE):
    intent = ActionIntent(kind="REQUEST_CRAFT", actor_id=1, target_id=f"opp_craft_{recipe_id}")
    updates = ActionIntentAdapter.execute(state.entities[1], intent, state.tick, None, None)
    refined = AuthoritativeApplyPipeline.refine(state, StateUpdate(entity_updates=updates))
    return updates[1], ApplyPath.apply_generation(state, refined)


def _held(state):
    return {s.item_id: s.quantity for s in state.entities[1].inventory.items}


def _untouched(update, after, *, gold=100, held=None):
    assert not update.resource_transfers
    assert _held(after) == (held if held is not None else {"iron_ore": 2, "wood": 1})
    assert after.entities[1].inventory.gold == gold


def test_the_recipe_under_test_costs_what_these_tests_assume():
    recipe = RecipeRegistry.get(RECIPE)
    assert dict(recipe.requires_items) == {"iron_ore": 2, "wood": 1} and recipe.gold_cost == 40


@pytest.mark.v2_contract
def test_craft_consumes_materials_and_gold_and_adds_the_product_together():
    """PROG-101, PROG-107: a craft that passes every gate is applied whole."""
    update, after = _craft(_state())
    (intent,) = update.resource_transfers
    assert intent.source_kind == "CRAFTING"
    assert _held(after) == {"iron_sword": 1}
    assert after.entities[1].inventory.gold == 60


@pytest.mark.v2_contract
def test_craft_needs_a_recipe_the_crafter_knows():
    """PROG-097: a recipe missing from the crafter's known set produces no craft."""
    state = _state(known=("craft_travel_ration",))
    update, after = _craft(state)
    _untouched(update, after)


@pytest.mark.v2_contract
def test_craft_needs_every_material():
    """PROG-098: a missing material blocks the craft and nothing is consumed."""
    state = _state(items=[ItemStack("iron_ore", 2)])
    update, after = _craft(state)
    _untouched(update, after, held={"iron_ore": 2})


@pytest.mark.v2_contract
def test_craft_needs_the_gold_cost():
    """PROG-099: too little gold blocks the craft and nothing is consumed."""
    update, after = _craft(_state(gold=39))
    _untouched(update, after, gold=39)


@pytest.mark.v2_contract
def test_craft_is_refused_whole_when_the_product_does_not_fit():
    """PROG-100, PROG-107: the capacity gate is the resolver's; a refused craft consumes neither materials nor gold."""
    update, after = _craft(_state(max_slots=0))
    assert update.resource_transfers  # the intent is built; the resolver refuses it
    assert _held(after) == {"iron_ore": 2, "wood": 1} and after.entities[1].inventory.gold == 100

