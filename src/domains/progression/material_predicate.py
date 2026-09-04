"""
src/domains/progression/material_predicate.py
───────────────────────────────────────────────────────────────────────────────
Shared material-possession predicate (TCK-20260904-MATERIAL-POSSESSION-PREDICATE, ideas 49/50).

Reads exclusively through src/core/recipes.py::RecipeRegistry -- the class the ticket's own
Acceptance Criteria explicitly names (src/core/recipes.py:15-48). 3 entries: iron_sword,
iron_shield, health_potion.

THREE other recipe-shaped things exist in this repo. Do NOT substitute any of them here:

1. src/core/registries.py::RecipeRegistry (registries.py:129-148) -- catalog-bootstrapped,
   up to 25 entries. Different dataclass field name (RecipeDef.requires_items vs. this
   module's Recipe.materials), different miss-behavior (.get() raises KeyError vs.
   recipes.py's get_recipe() returning None). Read by
   src/engine/intent/action_intent.py's REQUEST_CRAFT handling (both its pre-flight
   Requirement-building and its actual crafting-execution branch).

2. src/engine/blacksmith.py::BlacksmithSystem.RECIPES -- NOT a RecipeRegistry at all (a
   plain dict on BlacksmithSystem, no .get_recipe()/.get() classmethod), 14 entries, all
   craft_*-prefixed (craft_steel_sword, craft_battle_axe, ...). This is the class that
   actually, wholesale, populates entity.identity.known_recipes in live production today
   (src/engine/blacksmith.py:139-151, unconditionally wired every tick via
   src/engine/pipeline.py:223). Its 14 craft_* ids never overlap with this module's 3
   ids -- see TCK-20260904-MATERIAL-POSSESSION-PREDICATE's investigation.md "The THIRD
   recipe catalog" section for the full trace. This predicate does NOT read it: doing so
   would violate this ticket's own Acceptance Criteria #2, which requires the predicate
   to read recipes.py::RecipeRegistry specifically. The resulting namespace mismatch
   (this predicate returning () for craft_*-prefixed known_recipes members) is a
   disclosed, accepted, pre-existing limitation -- not something this ticket fixes.

Reading either of the other two here would silently change which recipes govern this
predicate's answer and is out of scope for this ticket (see
tickets/inprogress/TCK-20260904-MATERIAL-POSSESSION-PREDICATE.md's Out of Scope section).
"""

from __future__ import annotations
from typing import Tuple

from src.core.recipes import RecipeRegistry


def recipe_materials(recipe_id: str) -> Tuple[str, ...]:
    """
    Returns the material item_ids required by `recipe_id`, read through
    RecipeRegistry.get_recipe(recipe_id).materials keys.

    Returns () -- not an exception -- if recipe_id is not registered
    (mirrors RecipeRegistry.get_recipe()'s own None-on-miss contract).
    """
    recipe = RecipeRegistry.get_recipe(recipe_id)
    return tuple(recipe.materials.keys()) if recipe is not None else ()
