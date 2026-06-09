import os
import tempfile
import yaml
import pytest

from src.content.repository import CatalogRepository
from src.core.modes import RuntimeContentMode, AdapterHeuristicUsage
from src.core.registries import (
    seed_phase1_content,
    AdapterProjectionResult,
    ItemRegistry,
    RecipeRegistry,
    ServiceRegistry,
    RegionRegistry,
    ResourceRegistry,
    EnemyRegistry,
)


@pytest.fixture(scope="module")
def loaded_catalog_repo():
    repo = CatalogRepository("data/content")
    repo.load_all()
    seed_phase1_content(repo, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
    return repo


# ── CATALOG_WITH_COMPATIBILITY parity ────────────────────────────────────────

def test_item_registry_parity(loaded_catalog_repo):
    """Verify each active ItemDefinition has parity in ItemRegistry."""
    for item_id, item_def in loaded_catalog_repo.items.items():
        assert ItemRegistry.contains(item_id), f"Item {item_id} is missing from ItemRegistry"
        projected = ItemRegistry.get(item_id)
        assert projected.id == item_def.id
        assert projected.rarity == item_def.rarity
        assert projected.base_value == int(item_def.base_value)
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


def test_compatibility_mode_heuristic_usages_are_detailed(loaded_catalog_repo):
    """CATALOG_WITH_COMPATIBILITY projection returns typed heuristic records — not just a count."""
    result = seed_phase1_content(loaded_catalog_repo, mode=RuntimeContentMode.CATALOG_WITH_COMPATIBILITY)
    assert isinstance(result, AdapterProjectionResult)
    assert isinstance(result.heuristic_usages, tuple)
    assert len(result.heuristic_usages) > 0, "Expected heuristic inferences from real catalog"
    for usage in result.heuristic_usages:
        assert isinstance(usage, AdapterHeuristicUsage)
        assert usage.record_id, "heuristic usage must have a record_id"
        assert usage.adapter, "heuristic usage must have an adapter name"
        assert usage.reason, "heuristic usage must have a reason"
        assert usage.heuristic_type in ("use_kind", "class_fit", "affordances", "legacy_id",
                                         "source_region_tags", "required_tool", "base_difficulty")


# ── CATALOG_STRICT parity ─────────────────────────────────────────────────────

def _build_strict_catalog(tmp_dir: str) -> CatalogRepository:
    """Build a minimal fully-explicit catalog so CATALOG_STRICT produces zero heuristics."""
    os.makedirs(os.path.join(tmp_dir, "world"), exist_ok=True)
    os.makedirs(os.path.join(tmp_dir, "compatibility"), exist_ok=True)
    os.makedirs(os.path.join(tmp_dir, "entities"), exist_ok=True)

    items = [
        {
            "id": "iron_sword",
            "schema_version": "itemdefinition.v1",
            "categories": ["weapon", "melee"],
            "rarity": "UNCOMMON",
            "base_value": 80.0,
            "use_kind": "weapon",
            "class_fit": ["warrior"],
            "metadata": {"class_fit": ["warrior"]},
        }
    ]
    resources = [
        {
            "id": "node_iron",
            "schema_version": "resourcedefinition.v1",
            "resource_type": "iron_ore",
            "legacy_id": "node_iron",
            "required_tool": "pickaxe",
            "metadata": {
                "source_region_tags": ["old_mine"],
                "base_difficulty": 2,
            },
        }
    ]
    services = [
        {
            "id": "blacksmith_village",
            "schema_version": "servicedefinition.v1",
            "provided_items": [],
            "affordances": ["craft", "repair"],
        }
    ]

    with open(os.path.join(tmp_dir, "world", "items.yaml"), "w") as f:
        yaml.dump(items, f)
    with open(os.path.join(tmp_dir, "world", "resources.yaml"), "w") as f:
        yaml.dump(resources, f)
    with open(os.path.join(tmp_dir, "world", "services.yaml"), "w") as f:
        yaml.dump(services, f)
    for fname in ["recipes.yaml"]:
        with open(os.path.join(tmp_dir, "world", fname), "w") as f:
            yaml.dump([], f)
    with open(os.path.join(tmp_dir, "world", "runtime_regions.yaml"), "w") as f:
        yaml.dump([{"id": "hometown", "schema_version": "runtimeregiondefinition.v1",
                    "danger_level": 0, "tags": ["safe"]}], f)
    with open(os.path.join(tmp_dir, "compatibility", "legacy_enemy_projection.yaml"), "w") as f:
        yaml.dump([], f)
    with open(os.path.join(tmp_dir, "entities", "entity_archetypes.yaml"), "w") as f:
        yaml.dump([], f)
    with open(os.path.join(tmp_dir, "entities", "stat_profiles.yaml"), "w") as f:
        yaml.dump([], f)

    repo = CatalogRepository(tmp_dir)
    repo.load_all()
    return repo


def test_strict_mode_produces_zero_heuristic_usages():
    """CATALOG_STRICT with a fully-explicit catalog produces an empty heuristic_usages tuple."""
    with tempfile.TemporaryDirectory() as tmp:
        repo = _build_strict_catalog(tmp)
        result = seed_phase1_content(repo, mode=RuntimeContentMode.CATALOG_STRICT)
        assert isinstance(result, AdapterProjectionResult)
        assert result.heuristic_usages == (), (
            f"Expected zero heuristic usages in CATALOG_STRICT, got {result.heuristic_usages}"
        )
        assert result.heuristic_count == 0


# ── LEGACY_FALLBACK parity ────────────────────────────────────────────────────

def test_legacy_fallback_seeds_only_hardcoded_records():
    """LEGACY_FALLBACK mode seeds only hardcoded records and returns None."""
    result = seed_phase1_content(catalog_repo=None, mode=RuntimeContentMode.LEGACY_FALLBACK)
    assert result is None
    assert ItemRegistry.contains("rusted_sword")
    assert ItemRegistry.contains("wooden_staff")
    assert ItemRegistry.contains("small_potion")
    assert ResourceRegistry.contains("node_wood")
    assert ResourceRegistry.contains("node_iron")
    assert EnemyRegistry.contains("rat")
    assert EnemyRegistry.contains("wolf")
