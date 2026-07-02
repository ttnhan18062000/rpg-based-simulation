# Compliance ID: WORLD-REG-100
from __future__ import annotations
import os
import pytest

from src.core.registries import (
    seed_phase1_content,
    ItemRegistry,
    ResourceRegistry,
    EnemyRegistry,
    RecipeRegistry,
    ServiceRegistry,
    RegionRegistry
)
from src.content.repository import CatalogRepository

ALLOWLIST = {
    "items": {
        "rusted_sword", "wooden_staff", "basic_bow", "leather_armor", "iron_sword",
        "hunter_blade", "apprentice_staff", "small_potion", "travel_ration", "repair_kit",
        "wood", "herb", "iron_ore", "beast_fang", "wolf_pelt", "moon_resin", "crystal_shard",
        "goblin_token", "ancient_fragment", "healing_flower"
    },
    "resources": {
        "node_wood", "node_herb", "node_iron", "node_resin", "node_flower"
    },
    "enemies": {
        "rat", "wolf", "goblin", "goblin_archer", "cave_spider", "bandit_scout", "elite_goblin"
    },
    "recipes": {
        "iron_sword", "hunter_blade", "small_potion"
    },
    "services": {
        "shop_hometown", "blacksmith_hometown", "guide_hometown", "guild_hometown", "inn_hometown"
    },
    "regions": {
        "hometown", "near_forest", "old_mine", "wolf_den", "north_ruin", "goblin_camp", "moon_cave"
    }
}


def test_hardcoded_content_regression_guard():
    """
    Ensure no new hardcoded registry content is added directly to python registries
    without having a corresponding definition in the content catalog or being explicitly allowlisted.
    """
    # 1. Force load the legacy hardcoded seed maps
    from src.core.modes import RuntimeContentMode
    seed_phase1_content(catalog_repo=None, required=False, mode=RuntimeContentMode.LEGACY_FALLBACK)

    # 2. Load the content catalog repository
    catalog_repo = CatalogRepository("data/content")

    # 3. Check Items
    for item_id in ItemRegistry.all():
        if item_id not in ALLOWLIST["items"]:
            # If not allowlisted, it must exist in the catalog
            assert item_id in catalog_repo.items, (
                f"New hardcoded item '{item_id}' added without catalog definition. "
                "All new items must be defined in the content catalog first."
            )

    # 4. Check Resources
    for res_id in ResourceRegistry.all():
        if res_id not in ALLOWLIST["resources"]:
            assert res_id in catalog_repo.resources, (
                f"New hardcoded resource '{res_id}' added without catalog definition."
            )

    # 5. Check Enemies
    for enemy_id in EnemyRegistry.all():
        if enemy_id not in ALLOWLIST["enemies"]:
            # Check projection registry
            assert enemy_id in catalog_repo.legacy_enemy_projections or enemy_id in catalog_repo.entity_archetypes, (
                f"New hardcoded enemy '{enemy_id}' added without catalog or projection definition."
            )

    # 6. Check Recipes
    for recipe_id in RecipeRegistry.all():
        if recipe_id not in ALLOWLIST["recipes"]:
            assert recipe_id in catalog_repo.recipes, (
                f"New hardcoded recipe '{recipe_id}' added without catalog definition."
            )

    # 7. Check Services
    for service_id in ServiceRegistry.all():
        if service_id not in ALLOWLIST["services"]:
            assert service_id in catalog_repo.services, (
                f"New hardcoded service '{service_id}' added without catalog definition."
            )

    # 8. Check Regions
    for region_id in RegionRegistry.all():
        if region_id not in ALLOWLIST["regions"]:
            assert region_id in catalog_repo.regions, (
                f"New hardcoded region '{region_id}' added without catalog definition."
            )
