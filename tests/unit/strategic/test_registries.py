import pytest
from src.core.registries import (
    ItemRegistry, ResourceRegistry, EnemyRegistry, RecipeRegistry,
    ServiceRegistry, RegionRegistry
)


def test_registry_bootstrap_and_lookups():
    """Verify registries successfully bootstrap Phase 1 seed content and support O(1) query lookups."""
    # Test ItemRegistry
    assert ItemRegistry.contains("rusted_sword")
    item = ItemRegistry.get("rusted_sword")
    assert item.base_value == 10
    assert "weapon" in item.tags
    assert item.use_kind == "weapon"

    # Test ResourceRegistry
    assert ResourceRegistry.contains("node_wood")
    res = ResourceRegistry.get("node_wood")
    assert res.yield_item == "wood"
    assert "near_forest" in res.source_region_tags

    # Test KeyError on missing values
    with pytest.raises(KeyError):
        ItemRegistry.get("super_non_existent_item")


def test_referential_integrity():
    """Verify referential integrity across resources, enemies, and recipes in the seeded database."""
    # 1. Recipes requirements & outputs exist in ItemRegistry
    for recipe in RecipeRegistry.all().values():
        assert ItemRegistry.contains(recipe.output_item_id)
        for req_item in recipe.requires_items:
            assert ItemRegistry.contains(req_item)

    # 2. Resource yields exist in ItemRegistry
    for res in ResourceRegistry.all().values():
        assert ItemRegistry.contains(res.yield_item)

    # 3. Enemy drops exist in ItemRegistry
    for enemy in EnemyRegistry.all().values():
        for drop_item in enemy.loot_table:
            assert ItemRegistry.contains(drop_item)

    # 4. Service locations match valid RegionRegistry IDs
    for service in ServiceRegistry.all().values():
        assert RegionRegistry.contains(service.region_id)
