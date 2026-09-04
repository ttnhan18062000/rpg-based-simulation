"""
tests/unit/domains/progression/test_material_possession_predicate.py

TCK-20260904-MATERIAL-POSSESSION-PREDICATE — recipe_materials() predicate tests.
"""

import pytest

from src.core.recipes import RecipeRegistry
from src.domains.progression.material_predicate import recipe_materials


@pytest.mark.parametrize(
    "recipe_id,expected_material",
    [
        ("iron_sword", "iron_ore"),
        ("iron_shield", "iron_ore"),
        ("health_potion", "herb"),
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


def test_material_predicate_imports_recipes_py_registry_not_registries_py():
    import src.domains.progression.material_predicate as module

    assert module.RecipeRegistry is RecipeRegistry
    # recipes.py::RecipeRegistry.get_recipe() returns None on miss; confirms this
    # module is bound to the None-on-miss class, not registries.py's KeyError-raising one.
    assert RecipeRegistry.get_recipe("this_recipe_id_does_not_exist") is None
