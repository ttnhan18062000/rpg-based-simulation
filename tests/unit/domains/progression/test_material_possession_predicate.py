"""
tests/unit/domains/progression/test_material_possession_predicate.py

recipe_materials() predicate tests. Originally built for TCK-20260904-MATERIAL-POSSESSION-
PREDICATE reading src/core/recipes.py::RecipeRegistry (legacy, 3 entries); updated by
TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE to read src/core/registries.py::RecipeRegistry (the
real, live, catalog-backed registry known_recipes is now organically populated from).
"""

import pytest

from src.core.registries import RecipeRegistry
from src.domains.progression.material_predicate import recipe_materials


@pytest.mark.parametrize(
    "recipe_id,expected_material",
    [
        # "iron_sword"/"iron_shield" are real un-prefixed legacy-alias ids
        # (CatalogToRecipeRegistryAdapter strips the "craft_" prefix and registers both forms
        # pointing at the same RecipeDef -- src/core/registries.py:299-301) -- still real,
        # still resolve, not coincidental leftovers from the old recipes.py registry.
        ("iron_sword", "iron_ore"),
        ("iron_shield", "iron_ore"),
        # A real craft_*-prefixed id with no un-prefixed alias collision, and a real
        # un-prefixed alias for the same recipe -- both resolve to the same RecipeDef.
        ("craft_healer_bundle", "herb"),
        ("healer_bundle", "herb"),
    ],
)
def test_recipe_materials_returns_materials_for_each_live_recipe(recipe_id, expected_material):
    materials = recipe_materials(recipe_id)
    assert expected_material in materials


def test_recipe_materials_unregistered_recipe_returns_empty_tuple_not_exception():
    materials = recipe_materials("this_recipe_id_does_not_exist")
    assert materials == ()


def test_recipe_materials_docstring_disambiguates_all_three_registry_like_classes():
    import src.domains.progression.material_predicate as module

    doc = module.__doc__ or ""
    assert "src/core/recipes.py" in doc
    assert "src/core/registries.py" in doc
    assert "src/engine/blacksmith.py" in doc


def test_material_predicate_imports_registries_py_registry_not_recipes_py():
    """Before TCK-20260904-RECIPE-CATALOG-NAMESPACE-BRIDGE this asserted the opposite (bound to
    recipes.py's None-on-miss legacy class). Now bound to registries.py's real, live,
    KeyError-on-miss class -- recipe_materials()'s own .contains() guard (not this class) is what
    keeps recipe_materials()'s own never-raise contract intact for its callers."""
    import src.domains.progression.material_predicate as module

    assert module.RecipeRegistry is RecipeRegistry
    assert RecipeRegistry.contains("this_recipe_id_does_not_exist") is False
    with pytest.raises(KeyError):
        RecipeRegistry.get("this_recipe_id_does_not_exist")
