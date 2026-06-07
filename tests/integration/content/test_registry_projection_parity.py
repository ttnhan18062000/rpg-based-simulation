import pytest
from src.content.repository import CatalogRepository
from src.core.modes import RuntimeContentMode
from src.core.registries import (
    seed_phase1_content,
    ItemRegistry,
    RecipeRegistry,
    ServiceRegistry,
    RegionRegistry,
    ResourceRegistry,
    EnemyRegistry
)


@pytest.fixture(scope="module")
def loaded_catalog_repo():
    repo = CatalogRepository("data/content")
    repo.load_all()
    # Seed registries with compatibility mode to verify default behavior
    seed_phase1_content(repo, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
    return repo


def test_item_registry_parity(loaded_catalog_repo):
    """Verify each active ItemDefinition has parity in ItemRegistry."""
    for item_id, item_def in loaded_catalog_repo.items.items():
        assert ItemRegistry.contains(item_id), f"Item {item_id} is missing from ItemRegistry"
        projected = ItemRegistry.get(item_id)
        assert projected.id == item_def.id
        assert projected.rarity == item_def.rarity
        assert projected.base_value == int(item_def.base_value)
        # Verify tag/category parity
        assert set(projected.tags) == set(item_def.categories)


def test_recipe_registry_parity(loaded_catalog_repo):
    """Verify each active RecipeDefinition has parity in RecipeRegistry."""
    for rec_id, rec_def in loaded_catalog_repo.recipes.items():
        legacy_id = rec_id.replace("craft_", "") if rec_id.startswith("craft_") else rec_id
        assert RecipeRegistry.contains(rec_id) or RecipeRegistry.contains(legacy_id), f"Recipe {rec_id} is missing from RecipeRegistry"
        projected = RecipeRegistry.get(legacy_id)
        assert projected.output_item_id == list(rec_def.outputs.keys())[0] if rec_def.outputs else ""
        assert projected.gold_cost == int(rec_def.gold_cost)
        assert projected.requires_items == dict(rec_def.ingredients)


def test_service_registry_parity(loaded_catalog_repo):
    """Verify each active ServiceProfileDefinition has parity in ServiceRegistry."""
    for s_id, s_prof in loaded_catalog_repo.services.items():
        assert ServiceRegistry.contains(s_id), f"Service {s_id} is missing from ServiceRegistry"
        projected = ServiceRegistry.get(s_id)
        assert projected.id == s_id
        # Hometown services should not be present in catalog mode unless defined in catalog
        assert "shop_hometown" not in ServiceRegistry.all() or "shop_hometown" in loaded_catalog_repo.services


def test_region_registry_parity(loaded_catalog_repo):
    """Verify each active RuntimeRegionDefinition has parity in RegionRegistry."""
    for reg_id, reg_def in loaded_catalog_repo.regions.items():
        assert RegionRegistry.contains(reg_id), f"Region {reg_id} is missing from RegionRegistry"
        projected = RegionRegistry.get(reg_id)
        assert projected.id == reg_id
        assert projected.danger_level == reg_def.danger_level
        assert set(projected.tags) == set(reg_def.tags)


def test_enemy_projection_registry_parity(loaded_catalog_repo):
    """Verify each active LegacyEnemyProjectionDefinition has parity in EnemyRegistry."""
    for proj_id, proj in loaded_catalog_repo.legacy_enemy_projections.items():
        assert EnemyRegistry.contains(proj.legacy_enemy_id), f"Enemy {proj.legacy_enemy_id} is missing from EnemyRegistry"
        projected = EnemyRegistry.get(proj.legacy_enemy_id)
        assert projected.id == proj.legacy_enemy_id
        assert projected.danger_hint == proj.danger_hint
        assert projected.loot_table == dict(proj.loot_table)
        assert set(projected.spawn_regions) == set(proj.spawn_regions)
