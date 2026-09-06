"""
tests/unit/domains/progression/test_phase6_growth_gap_evaluator.py

Phase 6 — GrowthGapEvaluator tests.
"""

import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, ItemStack, EquipmentComponent, EquipSlot
from src.core.builder import V2EntityBuilder
from src.domains.progression.possession import PossessionUnderstandingService
from src.domains.progression.gaps import GrowthGapEvaluator


def test_weak_weapon_creates_weapon_gap():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()
    
    # Missing weapon (EquipSlot.MAIN_HAND is empty)
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    possession = PossessionUnderstandingService.evaluate(entity, state)
    report = GrowthGapEvaluator.evaluate(entity, possession, state)
    
    gap_keys = [g.key for g in report.gaps]
    assert "weapon_gap" in gap_keys
    assert report.dominant_gap == "weapon_gap"


def test_damaged_weapon_creates_repair_gap():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()
    
    # Mock equipped weapon and critically low durability
    entity = replace(entity,
        equipment=EquipmentComponent(
            slots={EquipSlot.MAIN_HAND: "iron_sword"},
            durability={EquipSlot.MAIN_HAND: 0.15}
        )
    )
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    possession = PossessionUnderstandingService.evaluate(entity, state)
    report = GrowthGapEvaluator.evaluate(entity, possession, state)
    
    gap_keys = [g.key for g in report.gaps]
    assert "repair_gap" in gap_keys
    # Durability is 0.15, repair_gap severity is 0.9, weapon is equipped, so dominant gap should be repair_gap
    assert report.dominant_gap == "repair_gap"


def test_missing_recipe_material_creates_material_gap():
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()
    
    # Knows iron_sword, but inventory is empty (no iron_ore)
    entity = replace(entity,
        identity=replace(entity.identity, known_recipes={"iron_sword"})
    )
    
    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    possession = PossessionUnderstandingService.evaluate(entity, state)
    report = GrowthGapEvaluator.evaluate(entity, possession, state)
    
    gap_keys = [g.key for g in report.gaps]
    assert "material_gap" in gap_keys


def test_growth_gap_material_gap_uses_real_recipe_lookup_not_hardcoded_literal():
    """
    Proves the material_gap check reads recipe_materials() generically instead of a
    hardcoded iron_sword/iron_ore literal -- covers craft_healer_bundle/herb, a real
    registries.py::RecipeRegistry recipe (TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE) a
    hardcoded check could never recognize.
    """
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()

    entity = replace(entity,
        identity=replace(entity.identity, known_recipes={"craft_healer_bundle"})
    )

    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    possession = PossessionUnderstandingService.evaluate(entity, state)
    report = GrowthGapEvaluator.evaluate(entity, possession, state)

    material_gaps = [g for g in report.gaps if g.key == "material_gap"]
    assert len(material_gaps) == 1
    assert "craft_healer_bundle" in material_gaps[0].reason


def test_growth_gap_craft_prefixed_known_recipes_now_produce_material_gap():
    """
    BEFORE TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE, this was a disclosed-limitation pinning
    test: craft_*-prefixed known_recipes ids (the ones BlacksmithSystem.enforce() actually
    populated known_recipes with) were not entries in src/core/recipes.py::RecipeRegistry (the
    registry recipe_materials() read at the time), so no material_gap was ever raised via this
    path -- a real, disclosed gap, not a bug.

    AFTER: both the population side (BlacksmithSystem) and recipe_materials() now read the same
    real registry (src/core/registries.py::RecipeRegistry), so a real, organically-learned
    craft_*-prefixed recipe id genuinely produces a material_gap when its materials are missing.
    `craft_iron_sword` is a real registries.py recipe (materials: iron_ore, wood) -- not the old,
    fictional `craft_steel_sword`.
    """
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()

    entity = replace(entity,
        identity=replace(entity.identity, known_recipes={"craft_iron_sword"})
    )

    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    possession = PossessionUnderstandingService.evaluate(entity, state)
    report = GrowthGapEvaluator.evaluate(entity, possession, state)

    material_gaps = [g for g in report.gaps if g.key == "material_gap"]
    assert len(material_gaps) == 1
    assert "craft_iron_sword" in material_gaps[0].reason
