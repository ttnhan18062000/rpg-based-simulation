"""TCK-20260808-CONTENT-CATALOG-INVENTORY-REFRESH."""
import glob
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from generate_content_inventory import _SINGLE_FILE_CATEGORIES, generate  # noqa: E402


def test_all_categories_present():
    counts = generate()
    expected = set(_SINGLE_FILE_CATEGORIES.keys()) | {
        "Simulation scenarios", "World modules", "World compositions",
        "World compositions (generated)",
    }
    assert set(counts.keys()) == expected


def test_counts_are_real_not_placeholder():
    counts = generate()

    items = yaml.safe_load(Path("data/content/world/items.yaml").read_text())
    items_list = items if isinstance(items, list) else next(
        v for v in items.values() if isinstance(v, list)
    )
    assert counts["Items"] == len(items_list)

    factions = yaml.safe_load(Path("data/content/social/factions.yaml").read_text())
    factions_list = factions if isinstance(factions, list) else next(
        v for v in factions.values() if isinstance(v, list)
    )
    assert counts["Factions"] == len(factions_list)

    recipes = yaml.safe_load(Path("data/content/world/recipes.yaml").read_text())
    recipes_list = recipes if isinstance(recipes, list) else next(
        v for v in recipes.values() if isinstance(v, list)
    )
    assert counts["Recipes"] == len(recipes_list)


def test_world_modules_and_compositions_counted_by_file():
    counts = generate()
    assert counts["World modules"] == len(glob.glob("data/content/world_modules/*.yaml"))
    assert counts["World compositions"] == len(glob.glob("data/content/world_compositions/*.yaml"))
    assert counts["World compositions (generated)"] == len(
        glob.glob("data/content/world_compositions/generated/*.yaml")
    )
