"""
src/domains/progression/possession.py
───────────────────────────────────────────────────────────────────────────────
Phase 6 — PossessionUnderstandingService

Evaluates inventory items against known recipes, active objectives, and equipment
to assign subjective keep/sell/equip/craft priorities with trace reason logs.
"""

from __future__ import annotations
from typing import Dict, Any

from src.core.state import EntityState, AuthoritativeState
from src.core.models.inventory import EquipSlot
from src.domains.progression.material_predicate import recipe_materials
from src.domains.progression.schema import PossessionMeaning, PossessionUnderstandingComponent


class PossessionUnderstandingService:
    """
    Evaluates item keep/sell/equip priorities subjectively.
    """

    @staticmethod
    def evaluate(
        entity: EntityState,
        state: AuthoritativeState,
    ) -> PossessionUnderstandingComponent:
        """
        Evaluate items currently owned by the actor.
        """
        meanings: Dict[str, PossessionMeaning] = {}
        
        # Load inventory items
        inv = getattr(entity, "inventory", None)
        items = getattr(inv, "items", []) or []

        # Load active recipes from identity/known_recipes
        id_comp = getattr(entity, "identity", None)
        known_recipes = getattr(id_comp, "known_recipes", set()) or set()

        for stack in items:
            item_id = stack.item_id
            known_uses = []
            keep_priority = 0.1
            sell_priority = 0.1
            equip_priority = 0.0
            craft_priority = 0.0
            reason = "No known strategic use."

            # 1. Check if material for a known recipe. See material_predicate.recipe_materials()
            # docstring: reads src/core/registries.py::RecipeRegistry (TCK-20260904-RECIPE-
            # CATALOG-NAMESPACE-BRIDGE) -- the same registry known_recipes is now organically
            # populated from, so a real recipe id genuinely matches here.
            matching_recipes = tuple(
                recipe_id for recipe_id in sorted(known_recipes)
                if item_id in recipe_materials(recipe_id)
            )
            is_recipe_material = bool(matching_recipes)
            if is_recipe_material:
                known_uses.extend(matching_recipes)
                keep_priority = 0.95
                craft_priority = 0.8
                reason = f"Required for known {matching_recipes[0]} recipe."

            # 2. Check if a better compatible gear than equipped
            is_weapon = item_id in ("iron_sword", "steel_sword", "rusted_sword")
            if is_weapon:
                equip = getattr(entity, "equipment", None)
                slots = getattr(equip, "slots", {}) or {}
                curr_weapon = slots.get(EquipSlot.MAIN_HAND)
                
                # Check weapon power comparison
                is_better = False
                if item_id == "iron_sword" and (not curr_weapon or curr_weapon == "rusted_sword"):
                    is_better = True
                elif item_id == "steel_sword" and (not curr_weapon or curr_weapon in ("rusted_sword", "iron_sword")):
                    is_better = True

                if is_better:
                    equip_priority = 0.9
                    keep_priority = 0.85
                    reason = "Direct upgrade to current equipped weapon."
                else:
                    sell_priority = 0.8
                    reason = "Worse than current equipped weapon, safe to sell."

            # 3. Check for rare/unknown items
            if item_id == "ancient_fragment":
                keep_priority = 0.9
                reason = "Unknown rare item clue. Keep for inquiry."

            if not is_recipe_material and not is_weapon and item_id != "ancient_fragment":
                sell_priority = 0.7
                reason = "Safe junk loot, fund spending routes."

            # Fetch value from ItemRegistry if available
            from src.core.items import ItemRegistry
            item_def = ItemRegistry.get(item_id)
            val = float(item_def.value if item_def else 10.0)

            meanings[item_id] = PossessionMeaning(
                item_id=item_id,
                known_uses=tuple(known_uses),
                estimated_value=val,
                keep_priority=keep_priority,
                sell_priority=sell_priority,
                equip_priority=equip_priority,
                craft_priority=craft_priority,
                reason=reason,
            )

        return PossessionUnderstandingComponent(
            meanings=meanings,
            last_evaluated_tick=state.tick,
        )
