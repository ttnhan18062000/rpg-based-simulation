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
    Proves the material_gap check now reads recipe_materials() generically instead of the
    old hardcoded iron_sword/iron_ore literal -- covers health_potion/herb, a recipe the
    old hardcoded check could never recognize.
    """
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()

    entity = replace(entity,
        identity=replace(entity.identity, known_recipes={"health_potion"})
    )

    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    possession = PossessionUnderstandingService.evaluate(entity, state)
    report = GrowthGapEvaluator.evaluate(entity, possession, state)

    material_gaps = [g for g in report.gaps if g.key == "material_gap"]
    assert len(material_gaps) == 1
    assert "herb" in material_gaps[0].reason
    assert "health_potion" in material_gaps[0].reason


def test_growth_gap_craft_prefixed_known_recipes_produce_no_material_gap():
    """
    Disclosed-limitation pinning test: craft_*-prefixed known_recipes ids (the ones
    BlacksmithSystem.enforce() actually populates known_recipes with in production) are
    not entries in src/core/recipes.py::RecipeRegistry, so no material_gap is raised via
    this path. See src/domains/progression/material_predicate.py's module docstring.
    """
    b = (V2EntityBuilder(1)
         .kind("ACTOR")
         .location(0.0, 0.0)
         .combat(hp=100, atk=10)
         .lifecycle(active=True)
         .inventory(gold=100))
    entity = b.build()

    entity = replace(entity,
        identity=replace(entity.identity, known_recipes={"craft_steel_sword"})
    )

    state = AuthoritativeState(entities={1: entity}, tick=1, seed=1)
    possession = PossessionUnderstandingService.evaluate(entity, state)
    report = GrowthGapEvaluator.evaluate(entity, possession, state)

    gap_keys = [g.key for g in report.gaps]
    assert "material_gap" not in gap_keys
