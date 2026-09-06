"""
src/domains/progression/gaps.py
───────────────────────────────────────────────────────────────────────────────
Phase 6 — GrowthGapEvaluator

Identifies progression weaknesses (weapon, repair, material, gold, level/AP,
skill gaps) deterministically based on active state features, and prioritizes
the dominant gap.
"""

from __future__ import annotations
from typing import List, Optional

from src.core.state import EntityState, AuthoritativeState, EquipSlot
from src.domains.progression.material_predicate import recipe_materials
from src.domains.progression.schema import GrowthGap, GrowthGapReport, PossessionUnderstandingComponent


class GrowthGapEvaluator:
    """
    Analyzes equipment durability, recipe needs, attribute AP availability, 
    and gold resources to generate specialized GrowthGap reports.
    """

    @staticmethod
    def evaluate(
        entity: EntityState,
        possession: PossessionUnderstandingComponent,
        state: AuthoritativeState,
    ) -> GrowthGapReport:
        gaps: List[GrowthGap] = []

        # 1. Weapon Gap & Repair Gap
        equip = getattr(entity, "equipment", None)
        slots = getattr(equip, "slots", {}) or {}
        durability = getattr(equip, "durability", {}) or {}

        curr_weapon = slots.get(EquipSlot.MAIN_HAND)
        
        # Weapon Strength Gap
        if not curr_weapon or curr_weapon == "rusted_sword":
            gaps.append(GrowthGap(
                key="weapon_gap",
                severity=0.85 if not curr_weapon else 0.6,
                confidence=1.0,
                reason="Main hand weapon is weak or missing.",
                candidate_resolution_tags=("weapon_upgrade", "craft_weapon")
            ))

        # Repair Gap
        # Check all equip slots for low durability
        worst_durability = 1.0
        for slot, dur_val in durability.items():
            if dur_val < worst_durability:
                worst_durability = dur_val

        if worst_durability < 0.5:
            # Critical repair gap
            severity = 0.9 if worst_durability < 0.2 else 0.5
            gaps.append(GrowthGap(
                key="repair_gap",
                severity=severity,
                confidence=1.0,
                reason=f"Equipment durability is critical ({worst_durability:.2f}).",
                candidate_resolution_tags=("blacksmith_repair",)
            ))

        # 2. Material Gap. See material_predicate.recipe_materials() docstring: reads
        # src/core/registries.py::RecipeRegistry (TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE)
        # -- the same registry known_recipes is now organically populated from.
        id_comp = getattr(entity, "identity", None)
        known_recipes = getattr(id_comp, "known_recipes", set()) or set()
        inventory_item_ids = {
            stack.item_id
            for stack in getattr(entity.inventory, "items", []) or []
            if stack.quantity > 0
        }

        missing_material_recipe = None
        missing_material_id = None
        for recipe_id in sorted(known_recipes):
            for material_id in recipe_materials(recipe_id):
                if material_id not in inventory_item_ids:
                    missing_material_recipe = recipe_id
                    missing_material_id = material_id
                    break
            if missing_material_recipe:
                break

        if missing_material_recipe:
            gaps.append(GrowthGap(
                key="material_gap",
                severity=0.5,
                confidence=0.8,
                reason=f"Missing {missing_material_id} to craft {missing_material_recipe} recipe.",
                candidate_resolution_tags=("gather_material", "buy_material")
            ))

        # 3. Gold Gap
        inv = getattr(entity, "inventory", None)
        gold = getattr(inv, "gold", 0) or 0
        if gold < 50:
            gaps.append(GrowthGap(
                key="gold_gap",
                severity=0.4 if gold < 10 else 0.2,
                confidence=0.9,
                reason=f"Low gold reserves ({gold}g). Cannot afford upgrades or repairs.",
                candidate_resolution_tags=("sell_loot", "complete_quests")
            ))

        # 4. Level/AP Gap
        unspent_ap = getattr(id_comp, "unspent_ap", 0) or 0
        if unspent_ap > 0:
            gaps.append(GrowthGap(
                key="level_gap",
                severity=0.7,
                confidence=1.0,
                reason=f"Have {unspent_ap} unspent Attribute Points ready for allocation.",
                candidate_resolution_tags=("allocate_ap",)
            ))

        # Determine dominant gap
        dominant: Optional[str] = None
        if gaps:
            # Sort by severity descending
            sorted_gaps = sorted(gaps, key=lambda g: g.severity, reverse=True)
            dominant = sorted_gaps[0].key

        return GrowthGapReport(
            gaps=tuple(gaps),
            dominant_gap=dominant
        )
