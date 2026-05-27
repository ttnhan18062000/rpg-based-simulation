"""
tests/unit/cognition/test_phase2_capability_estimate_service.py

Phase 2 — CapabilityEstimateService unit tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.state import CombatComponent, StaminaComponent
from src.core.models.inventory import ItemStack, InventoryComponent
from src.cognition.capability_estimate import CapabilityEstimateService, CapabilityContext


def _entity(
    hp=100, max_hp=100,
    stamina=100, max_stamina=100,
    attack=10, defense=2,
    level=1,
    gold=50,
    items=None,
):
    b = V2EntityBuilder(1)
    b.replace_combat(CombatComponent(hp=hp, max_hp=max_hp, atk=attack, def_stat=defense))
    b.replace_stamina(StaminaComponent(current=stamina, max_stamina=max_stamina))
    b.identity(evolution_level=level)
    if items:
        inv = InventoryComponent(items=items, gold=gold)
        b.replace_inventory(inv)
    else:
        b.inventory(gold=gold)
    return b.build()


# ── Combat estimates ──────────────────────────────────────────────────────────

class TestCapabilityCombat:
    def test_phase2_capability_weak_entity_vs_rat_moderate(self):
        entity = _entity(attack=5, level=1, hp=100, max_hp=100)
        ctx = CapabilityContext.for_combat(["rat"])
        result = CapabilityEstimateService.estimate(entity, context=ctx, tick=1)
        est = result.estimates.get("combat.enemy_type.rat")
        assert est is not None
        assert est.estimate > 0.0

    def test_phase2_capability_weak_entity_vs_wolf_lower_than_rat(self):
        entity = _entity(attack=5, level=1, hp=100, max_hp=100)
        ctx = CapabilityContext.for_combat(["rat", "wolf"])
        result = CapabilityEstimateService.estimate(entity, context=ctx, tick=1)
        rat_est = result.estimates["combat.enemy_type.rat"].estimate
        wolf_est = result.estimates["combat.enemy_type.wolf"].estimate
        assert wolf_est < rat_est

    def test_phase2_capability_wounded_entity_lower_than_healthy(self):
        healthy = _entity(attack=10, level=1, hp=100, max_hp=100)
        wounded = _entity(attack=10, level=1, hp=15, max_hp=100)
        ctx = CapabilityContext.for_combat(["rat"])
        h_result = CapabilityEstimateService.estimate(healthy, context=ctx, tick=1)
        w_result = CapabilityEstimateService.estimate(wounded, context=ctx, tick=1)
        assert w_result.estimates["combat.enemy_type.rat"].estimate < h_result.estimates["combat.enemy_type.rat"].estimate

    def test_phase2_capability_better_weapon_improves_combat_estimate(self):
        weak = _entity(attack=5, level=1)
        strong = _entity(attack=30, level=1)
        ctx = CapabilityContext.for_combat(["wolf"])
        w_result = CapabilityEstimateService.estimate(weak, context=ctx, tick=1)
        s_result = CapabilityEstimateService.estimate(strong, context=ctx, tick=1)
        assert s_result.estimates["combat.enemy_type.wolf"].estimate > w_result.estimates["combat.enemy_type.wolf"].estimate

    def test_phase2_capability_unknown_enemy_has_low_confidence(self):
        entity = _entity()
        ctx = CapabilityContext.for_combat(["ancient_horror"])
        result = CapabilityEstimateService.estimate(entity, context=ctx, tick=1)
        est = result.estimates.get("combat.enemy_type.ancient_horror")
        assert est is not None
        assert est.confidence < 0.7  # unknown enemy = lower confidence


# ── Travel estimates ──────────────────────────────────────────────────────────

class TestCapabilityTravel:
    def test_phase2_capability_hometown_is_safe(self):
        entity = _entity(hp=100, max_hp=100)
        ctx = CapabilityContext(travel_regions=("hometown",))
        result = CapabilityEstimateService.estimate(entity, context=ctx, tick=1)
        est = result.estimates.get("travel.region.hometown")
        assert est is not None
        assert est.estimate >= 0.9

    def test_phase2_capability_wounded_entity_lowers_travel_estimate(self):
        healthy = _entity(hp=100, max_hp=100)
        wounded = _entity(hp=15, max_hp=100)
        ctx = CapabilityContext(travel_regions=("north_ruin",))
        h_result = CapabilityEstimateService.estimate(healthy, context=ctx, tick=1)
        w_result = CapabilityEstimateService.estimate(wounded, context=ctx, tick=1)
        assert w_result.estimates["travel.region.north_ruin"].estimate < h_result.estimates["travel.region.north_ruin"].estimate

    def test_phase2_capability_unknown_region_has_low_confidence(self):
        entity = _entity()
        ctx = CapabilityContext(travel_regions=("mystery_island",))
        result = CapabilityEstimateService.estimate(entity, context=ctx, tick=1)
        est = result.estimates.get("travel.region.mystery_island")
        assert est is not None
        assert est.confidence < 0.6


# ── Crafting estimates ────────────────────────────────────────────────────────

class TestCapabilityCraft:
    def test_phase2_capability_missing_materials_craft_estimate_zero(self):
        # Entity has no items
        entity = _entity()
        recipe_data = {"iron_sword": {"requires_items": {"iron_ore": 2, "wood": 1}, "gold_cost": 0}}
        ctx = CapabilityContext.for_crafting(["iron_sword"], recipe_data=recipe_data)
        result = CapabilityEstimateService.estimate(entity, context=ctx, tick=1)
        est = result.estimates.get("craft.recipe.iron_sword")
        assert est is not None
        assert est.estimate == 0.0

    def test_phase2_capability_has_materials_craft_estimate_positive(self):
        items = [
            ItemStack(item_id="iron_ore", quantity=2),
            ItemStack(item_id="wood", quantity=1),
        ]
        entity = _entity(items=items, gold=100)
        recipe_data = {"iron_sword": {"requires_items": {"iron_ore": 2, "wood": 1}, "gold_cost": 0}}
        ctx = CapabilityContext.for_crafting(["iron_sword"], recipe_data=recipe_data)
        result = CapabilityEstimateService.estimate(entity, context=ctx, tick=1)
        est = result.estimates.get("craft.recipe.iron_sword")
        assert est is not None
        assert est.estimate > 0.5

    def test_phase2_capability_missing_gold_for_craft_estimate_zero(self):
        items = [ItemStack(item_id="iron_ore", quantity=2), ItemStack(item_id="wood", quantity=1)]
        entity = _entity(items=items, gold=0)
        recipe_data = {"iron_sword": {"requires_items": {"iron_ore": 2, "wood": 1}, "gold_cost": 50}}
        ctx = CapabilityContext.for_crafting(["iron_sword"], recipe_data=recipe_data)
        result = CapabilityEstimateService.estimate(entity, context=ctx, tick=1)
        est = result.estimates.get("craft.recipe.iron_sword")
        assert est is not None
        assert est.estimate == 0.0

    def test_phase2_capability_unknown_recipe_returns_low_estimate(self):
        entity = _entity()
        ctx = CapabilityContext.for_crafting(["mystery_brew"])  # no recipe_data
        result = CapabilityEstimateService.estimate(entity, context=ctx, tick=1)
        est = result.estimates.get("craft.recipe.mystery_brew")
        assert est is not None
        assert est.estimate <= 0.3
        assert est.confidence <= 0.3


# ── General behaviour ─────────────────────────────────────────────────────────

class TestCapabilityGeneral:
    def test_phase2_capability_none_context_returns_empty(self):
        entity = _entity()
        result = CapabilityEstimateService.estimate(entity, context=None, tick=5)
        assert result.estimates == {}

    def test_phase2_capability_output_is_deterministic(self):
        entity = _entity(attack=10, level=1, hp=60, max_hp=100)
        ctx = CapabilityContext.for_combat(["rat", "wolf"])
        r1 = CapabilityEstimateService.estimate(entity, context=ctx, tick=1)
        r2 = CapabilityEstimateService.estimate(entity, context=ctx, tick=1)
        assert r1 == r2

    def test_phase2_capability_does_not_mutate_entity(self):
        entity = _entity(hp=50, max_hp=100)
        hp_before = entity.combat.hp
        ctx = CapabilityContext.for_combat(["rat"])
        CapabilityEstimateService.estimate(entity, context=ctx, tick=1)
        assert entity.combat.hp == hp_before
