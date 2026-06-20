# Compliance IDs: TCK-20260619-E13C-RECIPES
"""
Unit tests for crafting recipe catalog expansion.
Verifies: ≥25 recipes, gather→craft chain, ingredient/output integrity,
service coverage, and CatalogRepository load.
"""
import yaml
import pytest
from pathlib import Path

CONTENT_DIR = Path(__file__).parent.parent.parent.parent / "data" / "content" / "world"
RECIPES_PATH = CONTENT_DIR / "recipes.yaml"
ITEMS_PATH = CONTENT_DIR / "items.yaml"
SERVICES_PATH = CONTENT_DIR / "services.yaml"


def _load_yaml_list(path: Path) -> list:
    with open(path) as f:
        return [doc for doc in yaml.safe_load_all(f) if doc is not None]


def _load_flat_list(path: Path) -> list:
    """Load a YAML file that is a flat list (not multi-document)."""
    with open(path) as f:
        content = f.read()
    # YAML files use # STATE: ... comments but are single documents
    result = yaml.safe_load(content)
    if result is None:
        return []
    return result


@pytest.fixture(scope="module")
def recipes() -> list:
    return _load_flat_list(RECIPES_PATH)


@pytest.fixture(scope="module")
def items() -> list:
    return _load_flat_list(ITEMS_PATH)


@pytest.fixture(scope="module")
def services() -> list:
    return _load_flat_list(SERVICES_PATH)


@pytest.fixture(scope="module")
def item_ids(items) -> set:
    return {item["id"] for item in items}


@pytest.fixture(scope="module")
def service_ids(services) -> set:
    return {svc["id"] for svc in services}


@pytest.fixture(scope="module")
def recipe_by_id(recipes) -> dict:
    return {r["id"]: r for r in recipes}


def test_recipe_count_at_least_25(recipes):
    """recipes.yaml must have ≥ 25 entries (AC1)."""
    assert len(recipes) >= 25, (
        f"Expected ≥ 25 recipes, got {len(recipes)}"
    )


def test_gather_craft_chain_iron_to_steel(recipe_by_id):
    """smelt_iron_to_steel must exist and convert iron_ore → steel (AC2, chain step 1)."""
    recipe = recipe_by_id.get("smelt_iron_to_steel")
    assert recipe is not None, "smelt_iron_to_steel recipe missing"
    assert "iron_ore" in recipe["ingredients"], "iron_ore must be an ingredient"
    assert recipe["ingredients"]["iron_ore"] >= 1, "iron_ore count must be ≥ 1"
    assert "steel" in recipe["outputs"], "steel must be in outputs"
    assert recipe["required_service"] == "blacksmith_service"


def test_gather_craft_chain_steel_to_ember_axe(recipe_by_id):
    """craft_ember_axe must exist and consume steel → ember_axe (AC2, chain step 2)."""
    recipe = recipe_by_id.get("craft_ember_axe")
    assert recipe is not None, "craft_ember_axe recipe missing"
    assert "steel" in recipe["ingredients"], "steel must be an ingredient"
    assert "ember_axe" in recipe["outputs"], "ember_axe must be in outputs"
    assert recipe["required_service"] == "blacksmith_service"


def test_full_gather_craft_chain_connected(recipe_by_id):
    """The chain iron_ore→steel→ember_axe must be fully connected with no gaps."""
    # Step 1: iron_ore → steel
    smelt = recipe_by_id["smelt_iron_to_steel"]
    assert "iron_ore" in smelt["ingredients"]
    assert "steel" in smelt["outputs"]
    # Step 2: steel → ember_axe (steel from step 1 is the input)
    craft = recipe_by_id["craft_ember_axe"]
    assert "steel" in craft["ingredients"]
    assert "ember_axe" in craft["outputs"]


def test_all_recipe_ingredients_are_valid_items(recipes, item_ids):
    """Every ingredient ID across all recipes must exist in items.yaml."""
    errors = []
    for recipe in recipes:
        for ingredient_id in recipe.get("ingredients", {}).keys():
            if ingredient_id not in item_ids:
                errors.append(f"Recipe '{recipe['id']}': unknown ingredient '{ingredient_id}'")
    assert not errors, "\n".join(errors)


def test_all_recipe_outputs_are_valid_items(recipes, item_ids):
    """Every output ID across all recipes must exist in items.yaml."""
    errors = []
    for recipe in recipes:
        for output_id in recipe.get("outputs", {}).keys():
            if output_id not in item_ids:
                errors.append(f"Recipe '{recipe['id']}': unknown output '{output_id}'")
    assert not errors, "\n".join(errors)


def test_all_recipe_services_exist(recipes, service_ids):
    """Every required_service in recipes must exist in services.yaml."""
    errors = []
    for recipe in recipes:
        svc = recipe.get("required_service")
        if svc and svc not in service_ids:
            errors.append(f"Recipe '{recipe['id']}': unknown service '{svc}'")
    assert not errors, "\n".join(errors)


def test_service_coverage_all_types(recipes):
    """At least one recipe per service type: blacksmith, healer, arcane, general_store."""
    service_types = {r.get("required_service") for r in recipes if r.get("required_service")}
    for expected in ["blacksmith_service", "healer_service", "arcane_service", "general_store_service"]:
        assert expected in service_types, f"No recipe uses service '{expected}'"


def test_no_duplicate_recipe_ids(recipes):
    """Recipe IDs must be unique."""
    ids = [r["id"] for r in recipes]
    assert len(ids) == len(set(ids)), f"Duplicate recipe IDs: {[x for x in ids if ids.count(x) > 1]}"


def test_all_recipes_have_required_fields(recipes):
    """Every recipe must have id, ingredients, outputs."""
    for recipe in recipes:
        assert "id" in recipe, f"Recipe missing 'id': {recipe}"
        assert "ingredients" in recipe, f"Recipe '{recipe['id']}' missing 'ingredients'"
        assert "outputs" in recipe, f"Recipe '{recipe['id']}' missing 'outputs'"


def test_craft_small_potion_is_preserved(recipe_by_id):
    """Legacy craft_small_potion must still exist (regression guard)."""
    assert "craft_small_potion" in recipe_by_id, "craft_small_potion was removed — regression"


def test_catalog_repository_loads():
    """CatalogRepository.load_all() must complete without error and load ≥ 25 recipes (AC3)."""
    from src.content.repository import CatalogRepository
    repo = CatalogRepository("data/content")
    report = repo.load_all()
    # Family key is "world.recipes" per CANONICAL_FAMILIES spec
    recipe_count = report.record_counts.get("world.recipes", 0)
    assert recipe_count >= 25, f"CatalogRepository loaded only {recipe_count} recipes, expected ≥ 25"
    # Also verify via in-memory index
    assert len(repo.recipes) >= 25, f"repo.recipes has {len(repo.recipes)} entries, expected ≥ 25"
