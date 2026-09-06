"""
src/domains/progression/material_predicate.py
───────────────────────────────────────────────────────────────────────────────
Shared material-possession predicate. Originally built (TCK-20260904-MATERIAL-POSSESSION-
PREDICATE, ideas 49/50) reading src/core/recipes.py::RecipeRegistry (legacy, 3 entries) per that
ticket's own Acceptance Criteria at the time -- deliberately disclosed then as inert against real
production data, since entities never organically learn any of that registry's 3 ids.

TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE closed that gap: this module now reads
src/core/registries.py::RecipeRegistry (catalog-bootstrapped, 25 entries) -- the same registry
src/engine/blacksmith.py's wholesale-learn step now populates entity.identity.known_recipes with
(src/engine/blacksmith.py:144), and the same one src/engine/intent/action_intent.py's REQUEST_CRAFT
branch reads for real AI-driven crafting (dispatched from src/domains/adventure/resolver.py's
ACQUIRE_ITEM objective). Both the population side and this consumption side now point at the same
real registry, so a real, organically-learned known_recipes id genuinely matches here.

TWO other recipe-shaped things exist in this repo. Neither is used here:

1. src/core/recipes.py::RecipeRegistry -- the module this predicate used to read. Confirmed to now
   have zero real callers anywhere in src/ (its own get_recipe() is fully unreferenced once this
   module stopped using it). Left in place, undeleted -- a disclosed, deliberate scope decision
   (TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE's own Completion Summary), not this predicate's
   concern to remove.

2. src/engine/blacksmith.py::BlacksmithSystem.RECIPES -- NOT a RecipeRegistry at all (a plain dict
   on BlacksmithSystem, no .get_recipe()/.get() classmethod), 14 entries, all craft_*-prefixed.
   Confirmed (TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE's investigation) to reference items and
   materials that were never actually authored anywhere in the real content catalog -- 13 of its 14
   output items and 11 of its 15 required materials don't exist in CatalogRepository at all. No
   longer the known_recipes population source (see blacksmith.py:144) and never a candidate source
   for this predicate.
"""

from __future__ import annotations
from typing import Tuple

from src.core.registries import RecipeRegistry


def recipe_materials(recipe_id: str) -> Tuple[str, ...]:
    """
    Returns the material item_ids required by `recipe_id`, read through
    RecipeRegistry.get(recipe_id).requires_items keys.

    Returns () -- not an exception -- if recipe_id is not registered. RecipeRegistry.get() raises
    KeyError on miss (unlike the legacy src/core/recipes.py::RecipeRegistry.get_recipe()'s
    None-on-miss contract this function used to build on) -- guarded here via .contains() first so
    this function's own miss contract (never raise, return ()) stays unchanged for its callers
    (possession.py, gaps.py).
    """
    if not RecipeRegistry.contains(recipe_id):
        return ()
    recipe = RecipeRegistry.get(recipe_id)
    return tuple(recipe.requires_items.keys())
