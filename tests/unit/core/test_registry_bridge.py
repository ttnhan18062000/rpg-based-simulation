import os
import tempfile
import yaml
import pytest
import dataclasses

from src.content.repository import CatalogRepository
from src.core.modes import RuntimeContentMode
from src.core.registries import (
    seed_phase1_content,
    AdapterProjectionResult,
    ItemRegistry,
    ResourceRegistry,
    EnemyRegistry,
    RecipeRegistry,
    ServiceRegistry,
    RegionRegistry,
    runtime_content_source,
    catalog_fingerprint
)
from src.core.items import ItemRegistry as CoreItemRegistry, ItemKind, EquipSlot


@pytest.fixture(autouse=True)
def cleanup_registries():
    """Automatically reset registries to default hardcoded fallback state after each test."""
    yield
    seed_phase1_content(None)


@pytest.fixture
def mock_catalog_repo():
    """Fixture that initializes a temporary catalog repository with mock definitions."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create directories matching repository expectations
        os.makedirs(os.path.join(tmp_dir, "world"), exist_ok=True)
        os.makedirs(os.path.join(tmp_dir, "compatibility"), exist_ok=True)
        os.makedirs(os.path.join(tmp_dir, "entities"), exist_ok=True)

        # 1. World items
        items_data = [
            {
                "id": "rusted_sword",
                "display_name": "Rusted Sword",
                "schema_version": "itemdefinition.v1",
                "categories": ["weapon", "melee"],
                "rarity": "COMMON",
                "base_value": 10.0,
                "metadata": {
                    "weight": 3.0,
                    "stack_size": 1,
                    "properties": {
                        "atk_bonus": 3,
                        "range": 1
                    }
                }
            },
            {
                "id": "wooden_staff",
                "display_name": "Wooden Staff",
                "schema_version": "itemdefinition.v1",
                "categories": ["weapon", "magic"],
                "rarity": "COMMON",
                "base_value": 10.0,
                "metadata": {
                    "weight": 2.0,
                    "stack_size": 1,
                    "properties": {
                        "atk_bonus": 5,
                        "range": 2
                    }
                }
            },
            {
                "id": "small_potion",
                "display_name": "Small Potion",
                "schema_version": "itemdefinition.v1",
                "categories": ["consumable", "healing"],
                "rarity": "COMMON",
                "base_value": 15.0,
                "metadata": {
                    "weight": 0.2,
                    "stack_size": 20,
                    "properties": {
                        "heal_amount": 50
                    }
                }
            },
            {
                "id": "wood",
                "display_name": "Wood",
                "schema_version": "itemdefinition.v1",
                "categories": ["material"],
                "rarity": "COMMON",
                "base_value": 2.0
            },
            {
                "id": "beast_fang",
                "display_name": "Beast Fang",
                "schema_version": "itemdefinition.v1",
                "categories": ["material"],
                "rarity": "UNCOMMON",
                "base_value": 15.0
            },
            {
                "id": "iron_ore",
                "display_name": "Iron Ore",
                "schema_version": "itemdefinition.v1",
                "categories": ["material"],
                "rarity": "COMMON",
                "base_value": 10.0
            },
            {
                "id": "iron_sword",
                "display_name": "Iron Sword",
                "schema_version": "itemdefinition.v1",
                "categories": ["weapon", "melee"],
                "rarity": "UNCOMMON",
                "base_value": 80.0
            }
        ]
        with open(os.path.join(tmp_dir, "world", "items.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(items_data, f)

        # 2. World resources
        resources_data = [
            {
                "id": "wood_node",
                "display_name": "Wood Node",
                "schema_version": "resourcedefinition.v1",
                "resource_type": "wood",
                "metadata": {
                    "preferred_biomes": ["near_forest"],
                    "base_difficulty": 1
                }
            },
            {
                "id": "iron_vein",
                "display_name": "Iron Vein",
                "schema_version": "resourcedefinition.v1",
                "resource_type": "iron_ore",
                "metadata": {
                    "preferred_biomes": ["old_mine"],
                    "required_tool": "pickaxe",
                    "base_difficulty": 2
                }
            }
        ]
        with open(os.path.join(tmp_dir, "world", "resources.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(resources_data, f)

        # 3. Compatibility projections
        projections_data = [
            {
                "id": "rat_proj",
                "archetype_id": "rat_archetype",
                "legacy_enemy_id": "rat",
                "danger_hint": "EASY",
                "loot_table": {
                    "beast_fang": 0.2
                },
                "spawn_regions": ["hometown", "near_forest"]
            },
            {
                "id": "wolf_proj",
                "archetype_id": "wolf_archetype",
                "legacy_enemy_id": "wolf",
                "danger_hint": "MEDIUM",
                "loot_table": {
                    "beast_fang": 0.3
                },
                "spawn_regions": ["near_forest"]
            }
        ]
        with open(os.path.join(tmp_dir, "compatibility", "legacy_enemy_projection.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(projections_data, f)

        # 4. Entity archetypes
        archetypes_data = [
            {
                "id": "rat_archetype",
                "race": "beast",
                "faction": "monster_faction",
                "role": "beast",
                "stat_profile": "rat_stats",
                "combat_profile": "beast_combat",
                "cognition_profile": "beast_cognition",
                "drive_profile": "beast_drive",
                "inventory_profile": "beast_inventory"
            },
            {
                "id": "wolf_archetype",
                "race": "beast",
                "faction": "monster_faction",
                "role": "beast",
                "stat_profile": "wolf_stats",
                "combat_profile": "beast_combat",
                "cognition_profile": "beast_cognition",
                "drive_profile": "beast_drive",
                "inventory_profile": "beast_inventory"
            }
        ]
        with open(os.path.join(tmp_dir, "entities", "entity_archetypes.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(archetypes_data, f)

        # 5. Stat profiles
        stats_data = [
            {
                "id": "rat_stats",
                "hp": 15,
                "max_hp": 15,
                "atk": 4,
                "def": 1,
                "attack_range": 1
            },
            {
                "id": "wolf_stats",
                "hp": 45,
                "max_hp": 45,
                "atk": 12,
                "def": 3,
                "attack_range": 1
            }
        ]
        with open(os.path.join(tmp_dir, "entities", "stat_profiles.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(stats_data, f)

        # 6. World recipes
        recipes_data = [
            {
                "id": "craft_iron_sword",
                "display_name": "Craft Iron Sword",
                "schema_version": "recipedefinition.v1",
                "ingredients": {
                    "iron_ore": 2,
                    "wood": 1
                },
                "gold_cost": 40.0,
                "outputs": {
                    "iron_sword": 1
                },
                "required_level": 1,
                "required_service": "blacksmith"
            }
        ]
        with open(os.path.join(tmp_dir, "world", "recipes.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(recipes_data, f)

        services_data = [
            {
                "id": "shop_hometown",
                "display_name": "Shop Hometown",
                "schema_version": "serviceprofiledefinition.v1",
                "provided_items": ["small_potion"],
                "gold_cost": 0.0
            },
            {
                "id": "blacksmith_hometown",
                "display_name": "Blacksmith Hometown",
                "schema_version": "serviceprofiledefinition.v1",
                "provided_items": [],
                "gold_cost": 10.0
            },
            {
                "id": "shop",
                "display_name": "General Shop",
                "schema_version": "serviceprofiledefinition.v1",
                "provided_items": ["small_potion"],
                "gold_cost": 0.0
            },
            {
                "id": "blacksmith",
                "display_name": "Blacksmith Forge",
                "schema_version": "serviceprofiledefinition.v1",
                "provided_items": [],
                "gold_cost": 10.0
            }
        ]
        with open(os.path.join(tmp_dir, "world", "services.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(services_data, f)

        # 8. World regions
        regions_data = [
            {
                "id": "hometown",
                "display_name": "Hometown Center",
                "schema_version": "runtimeregiondefinition.v1",
                "danger_level": 0,
                "tags": ["safe"]
            },
            {
                "id": "near_forest",
                "display_name": "Near Forest Wilderness",
                "schema_version": "runtimeregiondefinition.v1",
                "danger_level": 1,
                "tags": ["wild"]
            }
        ]
        with open(os.path.join(tmp_dir, "world", "runtime_regions.yaml"), "w", encoding="utf-8") as f:
            yaml.dump(regions_data, f)

        repo = CatalogRepository(tmp_dir)
        repo.load_all()
        yield repo


def test_registry_bridge_seeding_catalog(mock_catalog_repo):
    """Test that seed_phase1_content maps all components correctly under catalog seeding."""
    seed_phase1_content(mock_catalog_repo)

    # 1. Verify ItemRegistry (legacy)
    assert ItemRegistry.contains("rusted_sword")
    assert ItemRegistry.contains("wooden_staff")
    assert ItemRegistry.contains("small_potion")
    assert ItemRegistry.contains("wood")
    assert ItemRegistry.contains("beast_fang")
    assert ItemRegistry.contains("iron_ore")
    assert ItemRegistry.contains("iron_sword")

    sword_legacy = ItemRegistry.get("rusted_sword")
    assert "weapon" in sword_legacy.tags
    assert sword_legacy.use_kind == "weapon"
    assert sword_legacy.rarity == "COMMON"
    assert sword_legacy.base_value == 10

    potion_legacy = ItemRegistry.get("small_potion")
    assert "consumable" in potion_legacy.tags
    assert potion_legacy.use_kind == "potion"

    # 2. Verify CoreItemRegistry (runtime)
    assert CoreItemRegistry.get("rusted_sword") is not None
    sword_core = CoreItemRegistry.get("rusted_sword")
    assert sword_core.kind == ItemKind.WEAPON
    assert sword_core.weight == 3.0
    assert sword_core.stack_size == 1
    assert sword_core.properties.get("atk_bonus") == 3
    assert sword_core.properties.get("range") == 1
    assert sword_core.properties.get("slot") == EquipSlot.MAIN_HAND

    # Test overrides/defaults
    potion_core = CoreItemRegistry.get("small_potion")
    assert potion_core.kind == ItemKind.CONSUMABLE
    assert potion_core.weight == 0.2
    assert potion_core.stack_size == 20
    assert potion_core.properties.get("heal_amount") == 50

    iron_sword_core = CoreItemRegistry.get("iron_sword")
    assert iron_sword_core.kind == ItemKind.WEAPON
    # Test core defaults for un-overridden weapon
    assert iron_sword_core.weight == 3.0
    assert iron_sword_core.stack_size == 1
    assert iron_sword_core.properties.get("atk_bonus") == 10  # from legacy override or default logic

    # 3. Verify ResourceRegistry
    # Checks mapping of wood_node (which seeds both "node_wood" and "wood_node")
    assert ResourceRegistry.contains("node_wood") or ResourceRegistry.contains("wood_node")
    # Our bridge maps wood_node -> node_wood
    res_wood = ResourceRegistry.get("node_wood")
    assert res_wood.yield_item == "wood"
    assert "near_forest" in res_wood.source_region_tags
    assert res_wood.required_tool is None
    assert res_wood.base_difficulty == 1

    res_iron = ResourceRegistry.get("node_iron")
    assert res_iron.yield_item == "iron_ore"
    assert "old_mine" in res_iron.source_region_tags
    assert res_iron.required_tool == "pickaxe"
    assert res_iron.base_difficulty == 2

    # 4. Verify EnemyRegistry (with projection and stat profiling joins)
    assert EnemyRegistry.contains("rat")
    assert EnemyRegistry.contains("wolf")
    
    rat = EnemyRegistry.get("rat")
    assert rat.danger_hint == "EASY"
    assert rat.max_hp == 15
    assert rat.atk == 4
    assert rat.def_stat == 1
    assert rat.loot_table.get("beast_fang") == 0.2
    assert "hometown" in rat.spawn_regions

    # 5. Verify RecipeRegistry
    assert RecipeRegistry.contains("iron_sword")
    recipe = RecipeRegistry.get("iron_sword")
    assert recipe.requires_items.get("iron_ore") == 2
    assert recipe.requires_items.get("wood") == 1
    assert recipe.service_req == "blacksmith"
    assert recipe.gold_cost == 40
    assert recipe.output_item_id == "iron_sword"

    # 6. Verify ServiceRegistry
    # ServiceRegistry maps Hometown default services
    assert ServiceRegistry.contains("shop_hometown")
    assert ServiceRegistry.contains("blacksmith_hometown")
    
    shop = ServiceRegistry.get("shop_hometown")
    assert "buy" in shop.supported_affordances
    assert "sell" in shop.supported_affordances
    
    # And custom services from catalog
    assert ServiceRegistry.contains("blacksmith")
    bs = ServiceRegistry.get("blacksmith")
    assert "craft" in bs.supported_affordances

    # 7. Verify RegionRegistry
    assert RegionRegistry.contains("hometown")
    assert RegionRegistry.contains("near_forest")
    
    hometown = RegionRegistry.get("hometown")
    assert hometown.name == "Hometown Center"
    assert "safe" in hometown.tags
    assert hometown.danger_level == 0

    # 8. Check observability variables
    from src.core.registries import runtime_content_source as active_source, catalog_fingerprint as active_fingerprint
    assert active_source == "catalog"
    assert active_fingerprint == mock_catalog_repo.fingerprint


def test_registry_bridge_fallback():
    """Test that seed_phase1_content falls back to legacy hardcoded seeding correctly."""
    seed_phase1_content(None)

    # 1. Verify ItemRegistry
    assert ItemRegistry.contains("rusted_sword")
    assert ItemRegistry.get("rusted_sword").use_kind == "weapon"

    # 2. Verify ResourceRegistry
    assert ResourceRegistry.contains("node_wood")
    assert ResourceRegistry.get("node_wood").yield_item == "wood"

    # 3. Verify EnemyRegistry
    assert EnemyRegistry.contains("rat")
    assert EnemyRegistry.get("rat").max_hp == 15

    # 4. Verify RecipeRegistry
    assert RecipeRegistry.contains("iron_sword")

    # 5. Verify ServiceRegistry
    assert ServiceRegistry.contains("shop_hometown")

    # 6. Verify RegionRegistry
    assert RegionRegistry.contains("hometown")

    # 7. Check observability variables
    from src.core.registries import runtime_content_source as active_source, catalog_fingerprint as active_fingerprint
    assert active_source == "legacy_hardcoded"
    assert active_fingerprint is None


def test_referential_integrity_catalog(mock_catalog_repo):
    """Verify referential integrity in catalog-seeded state."""
    seed_phase1_content(mock_catalog_repo)

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


def test_runtime_content_mode_enum_has_migration_and_v2():
    assert RuntimeContentMode.MIGRATION.value == "migration"
    assert RuntimeContentMode.V2.value == "v2"
    assert len(RuntimeContentMode) == 2


def test_seed_with_migration_mode_returns_projection_result(mock_catalog_repo):
    result = seed_phase1_content(mock_catalog_repo, mode=RuntimeContentMode.MIGRATION)
    assert isinstance(result, AdapterProjectionResult)
    assert result.mode == RuntimeContentMode.MIGRATION
    assert result.item_count > 0
    assert result.service_count > 0
    assert result.resource_count > 0
    assert result.heuristic_count >= 0


def test_seed_with_v2_mode_raises_if_unresolved_entities_exist():
    import tempfile, os, yaml
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.makedirs(os.path.join(tmp_dir, "world"), exist_ok=True)
        os.makedirs(os.path.join(tmp_dir, "compatibility"), exist_ok=True)
        os.makedirs(os.path.join(tmp_dir, "entities"), exist_ok=True)
        items_data = [{"id": "no_use_kind_item", "schema_version": "itemdefinition.v1", "categories": ["weapon"], "rarity": "COMMON", "base_value": 5.0}]
        with open(os.path.join(tmp_dir, "world", "items.yaml"), "w") as f:
            yaml.dump(items_data, f)
        for fname in ["resources.yaml", "recipes.yaml", "services.yaml"]:
            with open(os.path.join(tmp_dir, "world", fname), "w") as f:
                yaml.dump([], f)
        with open(os.path.join(tmp_dir, "world", "runtime_regions.yaml"), "w") as f:
            yaml.dump([{"id": "hometown", "schema_version": "runtimeregiondefinition.v1", "danger_level": 0, "tags": ["safe"]}], f)
        with open(os.path.join(tmp_dir, "compatibility", "legacy_enemy_projection.yaml"), "w") as f:
            yaml.dump([], f)
        with open(os.path.join(tmp_dir, "entities", "entity_archetypes.yaml"), "w") as f:
            yaml.dump([], f)
        with open(os.path.join(tmp_dir, "entities", "stat_profiles.yaml"), "w") as f:
            yaml.dump([], f)
        from src.content.repository import CatalogRepository
        from src.core.registries import AdapterError
        repo = CatalogRepository(tmp_dir)
        repo.load_all()
        with pytest.raises(AdapterError):
            seed_phase1_content(repo, mode=RuntimeContentMode.V2)


def test_seed_legacy_fallback_returns_none():
    result = seed_phase1_content(None)
    assert result is None


def test_adapter_projection_result_is_frozen_dataclass():
    result = AdapterProjectionResult(
        mode=RuntimeContentMode.MIGRATION,
        item_count=5,
        service_count=3,
        resource_count=2,
        heuristic_count=1,
    )
    assert dataclasses.is_dataclass(result)
    assert result.item_count == 5
    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
        result.item_count = 99
