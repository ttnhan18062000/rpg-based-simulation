import pytest
from typing import Any, Dict
from src.core.registries import (
    AdapterError,
    CatalogToItemRegistryAdapter,
    CatalogToRecipeRegistryAdapter,
    CatalogToServiceRegistryAdapter,
    CatalogToRegionRegistryAdapter,
    CatalogToResourceRegistryAdapter,
    ArchetypeToEnemyRegistryAdapter,
    ItemDef,
    RecipeDef,
    ServiceDef,
    RegionDef,
    ResourceDef,
    EnemyDef
)


# Minimal Mock Objects mimicking Pydantic Models for test simplicity
class MockItem:
    def __init__(self, categories, rarity="COMMON", base_value=10, metadata=None):
        self.categories = categories
        self.rarity = rarity
        self.base_value = base_value
        self.metadata = metadata or {}


class MockRecipe:
    def __init__(self, ingredients, gold_cost, outputs, required_service=None):
        self.ingredients = ingredients
        self.gold_cost = gold_cost
        self.outputs = outputs
        self.required_service = required_service


class MockService:
    def __init__(self, provided_items=None):
        self.provided_items = provided_items or []


class MockRegion:
    def __init__(self, tags, display_name=None, danger_level=1):
        self.tags = tags
        self.display_name = display_name
        self.danger_level = danger_level


class MockResource:
    def __init__(self, resource_type, metadata=None):
        self.resource_type = resource_type
        self.metadata = metadata or {}


class MockEnemyProjection:
    def __init__(self, archetype_id, legacy_enemy_id, danger_hint, loot_table, spawn_regions):
        self.archetype_id = archetype_id
        self.legacy_enemy_id = legacy_enemy_id
        self.danger_hint = danger_hint
        self.loot_table = loot_table
        self.spawn_regions = spawn_regions


class MockArchetype:
    def __init__(self, stat_profile):
        self.stat_profile = stat_profile


class MockStatsProfile:
    def __init__(self, max_hp, atk, def_stat):
        self.max_hp = max_hp
        self.atk = atk
        self.def_stat = def_stat


class MockRepository:
    def __init__(self):
        self.items: Dict[str, Any] = {}
        self.recipes: Dict[str, Any] = {}
        self.services: Dict[str, Any] = {}
        self.regions: Dict[str, Any] = {}
        self.resources: Dict[str, Any] = {}
        self.legacy_enemy_projections: Dict[str, Any] = {}
        self.archetypes: Dict[str, Any] = {}
        self.stats_profiles: Dict[str, Any] = {}

    def get_entity_archetype(self, archetype_id: str):
        return self.archetypes.get(archetype_id)

    def get_stats_profile(self, stat_profile_id: str):
        return self.stats_profiles.get(stat_profile_id)


def test_item_adapter_happy_path():
    repo = MockRepository()
    repo.items["iron_sword"] = MockItem(categories=["weapon", "melee"], rarity="UNCOMMON", base_value=50)
    repo.items["small_potion"] = MockItem(categories=["consumable", "healing"], rarity="COMMON", base_value=15)
    repo.items["wood"] = MockItem(categories=["material"], rarity="COMMON", base_value=2)

    adapter = CatalogToItemRegistryAdapter(repo)
    adapted = adapter.adapt()

    assert len(adapted) == 3
    assert adapted["iron_sword"].use_kind == "weapon"
    assert adapted["iron_sword"].class_fit == ("warrior",)
    assert adapted["small_potion"].use_kind == "potion"
    assert adapted["wood"].use_kind == "material"


def test_item_adapter_error_handling():
    repo = MockRepository()
    # base_value is non-convertible string
    repo.items["broken_item"] = MockItem(categories=["weapon"], base_value="invalid")

    adapter = CatalogToItemRegistryAdapter(repo)
    with pytest.raises(AdapterError) as exc_info:
        adapter.adapt()
    
    assert exc_info.value.record_id == "broken_item"
    assert "invalid literal" in str(exc_info.value)


def test_recipe_adapter_happy_path():
    repo = MockRepository()
    repo.recipes["craft_iron_sword"] = MockRecipe(
        ingredients={"iron_ore": 2},
        gold_cost=10,
        outputs={"iron_sword": 1},
        required_service="blacksmith_hometown"
    )

    adapter = CatalogToRecipeRegistryAdapter(repo)
    adapted = adapter.adapt()

    # Recipe should register under both legacy name and craft_ prefixed name
    assert "iron_sword" in adapted
    assert "craft_iron_sword" in adapted
    assert adapted["iron_sword"].gold_cost == 10
    assert adapted["iron_sword"].output_item_id == "iron_sword"
    assert adapted["iron_sword"].service_req == "blacksmith"


def test_recipe_adapter_error_handling():
    repo = MockRepository()
    repo.recipes["bad_recipe"] = MockRecipe(
        ingredients={"wood": 1},
        gold_cost="invalid",
        outputs={}
    )

    adapter = CatalogToRecipeRegistryAdapter(repo)
    with pytest.raises(AdapterError) as exc_info:
        adapter.adapt()

    assert exc_info.value.record_id == "bad_recipe"


def test_service_adapter_happy_path():
    repo = MockRepository()
    repo.services["general_store"] = MockService(provided_items=["potion"])

    adapter = CatalogToServiceRegistryAdapter(repo)
    adapted = adapter.adapt()

    # Hometown defaults should exist
    assert "shop_hometown" in adapted
    # Dynamic service should exist
    assert "general_store" in adapted
    assert "buy" in adapted["general_store"].supported_affordances


def test_region_adapter_happy_path():
    repo = MockRepository()
    repo.regions["deep_forest"] = MockRegion(tags=["wild"], danger_level=3)

    adapter = CatalogToRegionRegistryAdapter(repo)
    adapted = adapter.adapt()

    assert "hometown" in adapted  # Default hometown region should be seeded
    assert "deep_forest" in adapted
    assert adapted["deep_forest"].danger_level == 3
    assert adapted["deep_forest"].name == "Deep Forest"


def test_resource_adapter_happy_path():
    repo = MockRepository()
    repo.resources["iron_vein"] = MockResource("iron_ore", metadata={"base_difficulty": 2, "required_tool": "pickaxe"})

    adapter = CatalogToResourceRegistryAdapter(repo)
    adapted = adapter.adapt()

    assert "node_iron" in adapted
    assert "iron_vein" in adapted
    assert adapted["node_iron"].yield_item == "iron_ore"
    assert adapted["node_iron"].required_tool == "pickaxe"


def test_enemy_adapter_happy_path():
    repo = MockRepository()
    repo.legacy_enemy_projections["wolf_proj"] = MockEnemyProjection(
        archetype_id="wolf_archetype",
        legacy_enemy_id="wolf",
        danger_hint="MEDIUM",
        loot_table={"wolf_pelt": 0.5},
        spawn_regions=["near_forest"]
    )
    repo.archetypes["wolf_archetype"] = MockArchetype("wolf_stats")
    repo.stats_profiles["wolf_stats"] = MockStatsProfile(max_hp=40, atk=12, def_stat=3)

    adapter = ArchetypeToEnemyRegistryAdapter(repo)
    adapted = adapter.adapt()

    assert "rat" in adapted  # Rat fallback
    assert "wolf" in adapted
    assert adapted["wolf"].max_hp == 40
    assert adapted["wolf"].atk == 12
    assert adapted["wolf"].danger_hint == "MEDIUM"


def test_item_adapter_uses_explicit_use_kind():
    repo = MockRepository()
    item = MockItem(categories=["weapon"], rarity="COMMON", base_value=10)
    item.use_kind = "custom_use_kind"
    item.class_fit = ["warrior"]
    repo.items["test_item"] = item

    # Strict catalog-backed mode (migration_mode=False)
    adapter = CatalogToItemRegistryAdapter(repo, migration_mode=False)
    adapted = adapter.adapt()
    assert adapted["test_item"].use_kind == "custom_use_kind"


def test_item_adapter_uses_explicit_class_fit():
    repo = MockRepository()
    item = MockItem(categories=["weapon"], rarity="COMMON", base_value=10)
    item.use_kind = "weapon"
    item.class_fit = ["ranger", "rogue"]
    repo.items["test_item"] = item

    adapter = CatalogToItemRegistryAdapter(repo, migration_mode=False)
    adapted = adapter.adapt()
    assert adapted["test_item"].class_fit == ("ranger", "rogue")


def test_resource_adapter_uses_explicit_legacy_id():
    repo = MockRepository()
    res = MockResource("wood")
    res.legacy_id = "custom_node_wood"
    res.metadata = {"source_region_tags": ["forest"]}
    repo.resources["wood_node"] = res

    adapter = CatalogToResourceRegistryAdapter(repo, migration_mode=False)
    adapted = adapter.adapt()
    assert "custom_node_wood" in adapted
    assert adapted["custom_node_wood"].yield_item == "wood"


def test_service_adapter_does_not_inject_default_service_in_catalog_mode():
    repo = MockRepository()
    service = MockService()
    service.affordances = ["buy"]
    repo.services["trade_service"] = service

    adapter = CatalogToServiceRegistryAdapter(repo, catalog_mode=True, migration_mode=False)
    adapted = adapter.adapt()
    # Should NOT contain hometown services
    assert "shop_hometown" not in adapted
    assert "trade_service" in adapted


def test_fallback_enemy_not_seeded_in_catalog_mode():
    repo = MockRepository()
    adapter = ArchetypeToEnemyRegistryAdapter(repo, catalog_mode=True)
    adapted = adapter.adapt()
    # Rat fallback should NOT be seeded in catalog mode
    assert "rat" not in adapted


def test_fallback_usage_reported_in_legacy_mode():
    from src.core.registries import seed_phase1_content, fallback_usage_reported
    import src.core.registries as registries
    registries.fallback_usage_reported = False

    # Seed without catalog repo -> triggers fallback legacy backup mode
    seed_phase1_content(catalog_repo=None)
    assert registries.fallback_usage_reported is True
