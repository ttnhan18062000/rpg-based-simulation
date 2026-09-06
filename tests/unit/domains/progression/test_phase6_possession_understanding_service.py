"""
tests/unit/domains/progression/test_phase6_possession_understanding_service.py

Phase 6 — PossessionUnderstandingService tests.
"""

import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, ItemStack, EquipmentComponent, EquipSlot
from src.core.builder import V2EntityBuilder
from src.domains.progression.possession import PossessionUnderstandingService


def test_material_for_active_recipe_has_high_keep_priority():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()
    
    stack = ItemStack(item_id="iron_ore", quantity=1)
    entity = replace(entity,
        inventory=replace(entity.inventory, items=[stack]),
        identity=replace(entity.identity, known_recipes={"iron_sword"})
    )
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    comp = PossessionUnderstandingService.evaluate(entity, state)
    
    assert "iron_ore" in comp.meanings
    meaning = comp.meanings["iron_ore"]
    assert meaning.keep_priority > 0.9
    assert meaning.craft_priority > 0.7
    assert "iron_sword" in meaning.known_uses
    assert "iron_sword" in meaning.reason


def test_junk_item_has_sell_priority():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()
    
    stack = ItemStack(item_id="broken_mug", quantity=5)
    entity = replace(entity,
        inventory=replace(entity.inventory, items=[stack])
    )
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    comp = PossessionUnderstandingService.evaluate(entity, state)
    
    assert "broken_mug" in comp.meanings
    meaning = comp.meanings["broken_mug"]
    assert meaning.sell_priority > 0.6
    assert meaning.keep_priority < 0.2
    assert "junk" in meaning.reason or "No known" in meaning.reason or "spending" in meaning.reason


def test_better_weapon_gets_equip_priority():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()
    
    stack = ItemStack(item_id="iron_sword", quantity=1)
    entity = replace(entity,
        inventory=replace(entity.inventory, items=[stack]),
        equipment=EquipmentComponent(slots={EquipSlot.MAIN_HAND: "rusted_sword"})
    )
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    comp = PossessionUnderstandingService.evaluate(entity, state)
    
    assert "iron_sword" in comp.meanings
    meaning = comp.meanings["iron_sword"]
    assert meaning.equip_priority > 0.8
    assert "upgrade" in meaning.reason


def test_material_possession_predicate_recognizes_known_recipe_material():
    """Generalized normal flow beyond the original hardcoded iron_ore/iron_sword pair. Uses a real
    registries.py::RecipeRegistry recipe (craft_healer_bundle, requires herb + healing_flower) --
    the old "health_potion" fixture predates TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE and is
    not a real id in the current live registry."""
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()

    stack = ItemStack(item_id="herb", quantity=3)
    entity = replace(entity,
        inventory=replace(entity.inventory, items=[stack]),
        identity=replace(entity.identity, known_recipes={"craft_healer_bundle"})
    )

    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    comp = PossessionUnderstandingService.evaluate(entity, state)

    assert "herb" in comp.meanings
    meaning = comp.meanings["herb"]
    assert meaning.keep_priority > 0.9
    assert meaning.craft_priority > 0.7
    assert "craft_healer_bundle" in meaning.known_uses


def test_material_possession_predicate_empty_inventory_returns_false_no_crash():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()

    entity = replace(entity,
        inventory=replace(entity.inventory, items=[]),
        identity=replace(entity.identity, known_recipes={"iron_sword"})
    )

    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    comp = PossessionUnderstandingService.evaluate(entity, state)

    assert comp.meanings == {}


def test_material_possession_predicate_craft_prefixed_known_recipes_now_match():
    """
    BEFORE TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE, this was a disclosed-limitation pinning
    test: craft_*-prefixed known_recipes ids (the ones BlacksmithSystem.enforce() actually,
    wholesale, populated known_recipes with) were not entries in src/core/recipes.py::
    RecipeRegistry (the registry this predicate read at the time), so the predicate correctly-
    but-uselessly did NOT treat iron_ore as a recipe material for them -- a real, disclosed gap,
    not a bug.

    AFTER: both the population side (BlacksmithSystem) and this predicate now read the same real
    registry (src/core/registries.py::RecipeRegistry), so a real, organically-learned craft_*-
    prefixed recipe id genuinely matches. `craft_iron_sword` here is a real registries.py recipe
    (materials: iron_ore, wood) -- not the old, fictional `craft_steel_sword` (BlacksmithSystem's
    own private, orphaned recipe list, confirmed to reference items/materials that don't exist
    anywhere in the real content catalog).
    """
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()

    stack = ItemStack(item_id="iron_ore", quantity=1)
    entity = replace(entity,
        inventory=replace(entity.inventory, items=[stack]),
        identity=replace(entity.identity, known_recipes={"craft_iron_sword"})
    )

    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    comp = PossessionUnderstandingService.evaluate(entity, state)

    assert "iron_ore" in comp.meanings
    meaning = comp.meanings["iron_ore"]
    assert meaning.known_uses == ("craft_iron_sword",)
    assert meaning.craft_priority == 0.8
