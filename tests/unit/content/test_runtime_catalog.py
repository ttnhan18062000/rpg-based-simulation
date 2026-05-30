# Compliance IDs: WORLD-CAT-TEST-PHASE13
import os
import pytest
import tempfile
import yaml
from src.content.repository import CatalogRepository
from src.content.validator import CatalogValidator


def test_runtime_catalog_expansion_loading():
    """Verify that CatalogRepository successfully loads item, legacy projections, recipe, and region configurations."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create directories
        os.makedirs(os.path.join(tmp_dir, "world"), exist_ok=True)
        os.makedirs(os.path.join(tmp_dir, "compatibility"), exist_ok=True)

        # 1. Create world/items.yaml
        items_data = [
            {
                "id": "iron_sword",
                "display_name": "Iron Sword",
                "schema_version": "itemdefinition.v1",
                "categories": ["weapon"],
                "rarity": "COMMON",
                "base_value": 150.0,
                "materials": ["iron"]
            },
            {
                "id": "iron_ore",
                "display_name": "Iron Ore",
                "schema_version": "itemdefinition.v1",
                "categories": ["material"],
                "rarity": "COMMON",
                "base_value": 10.0
            }
        ]
        with open(os.path.join(tmp_dir, "world", "items.yaml"), "w") as f:
            yaml.dump(items_data, f)

        # 2. Create compatibility/legacy_enemy_projection.yaml
        projections_data = [
            {
                "id": "goblin",
                "archetype_id": "goblin_scout",
                "legacy_enemy_id": "goblin",
                "danger_hint": "MEDIUM",
                "loot_table": {
                    "iron_sword": 0.05
                },
                "spawn_regions": ["starting_forest"]
            }
        ]
        with open(os.path.join(tmp_dir, "compatibility", "legacy_enemy_projection.yaml"), "w") as f:
            yaml.dump(projections_data, f)

        # 3. Create world/recipes.yaml
        recipes_data = [
            {
                "id": "smelt_iron",
                "display_name": "Smelt Iron Ore",
                "schema_version": "recipedefinition.v1",
                "ingredients": {
                    "iron_ore": 3
                },
                "outputs": {
                    "iron_sword": 1
                },
                "gold_cost": 25.0,
                "required_level": 1,
                "required_service": "blacksmith_forge"
            }
        ]
        with open(os.path.join(tmp_dir, "world", "recipes.yaml"), "w") as f:
            yaml.dump(recipes_data, f)

        # 4. Create world/runtime_regions.yaml
        regions_data = [
            {
                "id": "starting_forest",
                "display_name": "Starting Forest",
                "schema_version": "runtimeregiondefinition.v1",
                "danger_level": 1,
                "allowed_enemy_ids": ["goblin"],
                "travel_cost": 0.0
            }
        ]
        with open(os.path.join(tmp_dir, "world", "runtime_regions.yaml"), "w") as f:
            yaml.dump(regions_data, f)

        # Also add dummy services to satisfy blacksmith_forge
        services_data = [
            {
                "id": "blacksmith_forge",
                "display_name": "Blacksmith Forge Service",
                "schema_version": "serviceprofiledefinition.v1",
                "provided_items": ["iron_sword"]
            }
        ]
        with open(os.path.join(tmp_dir, "world", "services.yaml"), "w") as f:
            yaml.dump(services_data, f)

        repo = CatalogRepository(tmp_dir)
        repo.load_all()

        # Check repository lookups
        assert repo.get_item("iron_sword") is not None
        assert repo.get_item("iron_sword").categories == ["weapon"]
        assert repo.get_item("iron_sword").base_value == 150.0

        assert repo.get_legacy_enemy_projection("goblin") is not None
        assert repo.get_legacy_enemy_projection("goblin").legacy_enemy_id == "goblin"

        assert repo.get_recipe("smelt_iron") is not None
        assert repo.get_recipe("smelt_iron").gold_cost == 25.0

        assert repo.get_region("starting_forest") is not None
        assert repo.get_region("starting_forest").danger_level == 1

        # Check metadata routing APIs
        all_items = repo.get_all_ids_by_type("item")
        assert "iron_sword" in all_items
        assert "iron_ore" in all_items

        all_recipes = repo.get_all_ids_by_type("recipe")
        assert "smelt_iron" in all_recipes

        all_regions = repo.get_all_ids_by_type("region")
        assert "starting_forest" in all_regions


def test_runtime_catalog_relational_failures():
    """Verify that CatalogValidator catches relational violations across items, recipes, regions, and legacy projections."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create directories
        os.makedirs(os.path.join(tmp_dir, "world"), exist_ok=True)
        os.makedirs(os.path.join(tmp_dir, "compatibility"), exist_ok=True)

        # Legacy projection referencing non-existent archetype, non-existent loot item, and non-existent region
        projections_data = [
            {
                "id": "rogue_goblin",
                "archetype_id": "missing_archetype",
                "legacy_enemy_id": "goblin",
                "danger_hint": "MEDIUM",
                "loot_table": {
                    "legendary_axe": 0.01
                },
                "spawn_regions": ["missing_volcano"]
            }
        ]
        with open(os.path.join(tmp_dir, "compatibility", "legacy_enemy_projection.yaml"), "w") as f:
            yaml.dump(projections_data, f)

        # Recipe referencing non-existent ingredients, outputs, and services
        recipes_data = [
            {
                "id": "craft_legendary",
                "display_name": "Craft Legendary",
                "schema_version": "recipedefinition.v1",
                "ingredients": {
                    "missing_material": 10
                },
                "outputs": {
                    "legendary_axe": 1
                },
                "gold_cost": 500.0,
                "required_level": 5,
                "required_service": "missing_mystic_forge"
            }
        ]
        with open(os.path.join(tmp_dir, "world", "recipes.yaml"), "w") as f:
            yaml.dump(recipes_data, f)

        # Region referencing non-existent enemy/archetype
        regions_data = [
            {
                "id": "cursed_ruins",
                "display_name": "Cursed Ruins",
                "schema_version": "runtimeregiondefinition.v1",
                "danger_level": 5,
                "allowed_enemy_ids": ["missing_undead"],
                "travel_cost": 100.0
            }
        ]
        with open(os.path.join(tmp_dir, "world", "runtime_regions.yaml"), "w") as f:
            yaml.dump(regions_data, f)

        repo = CatalogRepository(tmp_dir)
        repo.load_all()

        validator = CatalogValidator(repo)
        issues = validator.validate()

        errors = [i for i in issues if i.severity == "ERROR"]
        rule_ids = {i.rule_id for i in errors}

        # Check that all relational rule violations are caught
        assert "CAT-REL-014" in rule_ids  # Legacy projection references non-existent archetype/loot item/spawn region
        assert "CAT-REL-015" in rule_ids  # Recipe ingredient/output missing item or missing service
        assert "CAT-REL-016" in rule_ids  # Region allowed enemy missing archetype/projection
