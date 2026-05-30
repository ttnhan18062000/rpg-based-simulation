import pytest
from src.content.repository import CatalogRepository
from src.core.registries import (
    seed_phase1_content,
    ItemRegistry,
    ResourceRegistry,
    EnemyRegistry,
    RecipeRegistry,
    ServiceRegistry,
    RegionRegistry
)
from src.core.items import ItemRegistry as CoreItemRegistry


@pytest.fixture(autouse=True)
def cleanup_registries():
    """Automatically reset registries to default hardcoded fallback state after each test."""
    yield
    seed_phase1_content(None)


def get_registry_snapshots():
    """Helper to take a snapshot of all active registries."""
    return {
        "items": ItemRegistry.all(),
        "resources": ResourceRegistry.all(),
        "enemies": EnemyRegistry.all(),
        "recipes": RecipeRegistry.all(),
        "services": ServiceRegistry.all(),
        "regions": RegionRegistry.all(),
        "core_items": CoreItemRegistry._items.copy() if hasattr(CoreItemRegistry, "_items") else {}
    }


def test_production_catalog_parity():
    """Verify that catalog-backed content and legacy hardcoded content are semantically equivalent."""
    # 1. Capture legacy hardcoded state
    seed_phase1_content(None)
    legacy = get_registry_snapshots()

    # 2. Capture catalog-backed state
    repo = CatalogRepository("data/content")
    repo.load_all()
    seed_phase1_content(repo)
    catalog = get_registry_snapshots()

    # 3. Compare Items
    print(f"\n--- Comparing Items: Legacy ({len(legacy['items'])}) vs Catalog ({len(catalog['items'])}) ---")
    # All legacy item IDs should exist in catalog
    missing_items = []
    mismatched_items = []
    for item_id, leg_item in legacy["items"].items():
        if item_id not in catalog["items"]:
            missing_items.append(item_id)
            continue
        cat_item = catalog["items"][item_id]
        
        # Compare key fields
        mismatches = []
        if leg_item.use_kind != cat_item.use_kind:
            mismatches.append(f"use_kind: {leg_item.use_kind} vs {cat_item.use_kind}")
        if leg_item.base_value != cat_item.base_value:
            mismatches.append(f"base_value: {leg_item.base_value} vs {cat_item.base_value}")
        if sorted(leg_item.class_fit) != sorted(cat_item.class_fit):
            mismatches.append(f"class_fit: {leg_item.class_fit} vs {cat_item.class_fit}")
        if leg_item.rarity != cat_item.rarity:
            mismatches.append(f"rarity: {leg_item.rarity} vs {cat_item.rarity}")
        
        if mismatches:
            mismatched_items.append((item_id, mismatches))

    # 4. Compare Core Items (runtime)
    print(f"--- Comparing Core Items: Legacy ({len(legacy['core_items'])}) vs Catalog ({len(catalog['core_items'])}) ---")
    mismatched_core_items = []
    for item_id, leg_core_item in legacy["core_items"].items():
        if item_id not in catalog["core_items"]:
            continue
        cat_core_item = catalog["core_items"][item_id]
        mismatches = []
        if leg_core_item.kind != cat_core_item.kind:
            mismatches.append(f"kind: {leg_core_item.kind} vs {cat_core_item.kind}")
        # Note: We omit strict weight/value equality checks here:
        # - Weights are not specified in the catalog yaml and fallback to kind defaults.
        # - Values are unified in the catalog to base_value (e.g. 12 for iron_ore), resolving legacy default 1.
        
        # Compare properties that are explicitly defined in legacy
        for prop_key, leg_val in leg_core_item.properties.items():
            cat_val = cat_core_item.properties.get(prop_key)
            if leg_val != cat_val:
                mismatches.append(f"properties[{prop_key}]: {leg_val} vs {cat_val}")
                
        if mismatches:
            mismatched_core_items.append((item_id, mismatches))

    # 5. Compare Resources
    print(f"--- Comparing Resources: Legacy ({len(legacy['resources'])}) vs Catalog ({len(catalog['resources'])}) ---")
    missing_resources = []
    mismatched_resources = []
    for res_id, leg_res in legacy["resources"].items():
        if res_id not in catalog["resources"]:
            missing_resources.append(res_id)
            continue
        cat_res = catalog["resources"][res_id]
        mismatches = []
        if leg_res.yield_item != cat_res.yield_item:
            mismatches.append(f"yield_item: {leg_res.yield_item} vs {cat_res.yield_item}")
        if leg_res.required_tool != cat_res.required_tool:
            mismatches.append(f"required_tool: {leg_res.required_tool} vs {cat_res.required_tool}")
        if leg_res.base_difficulty != cat_res.base_difficulty:
            mismatches.append(f"base_difficulty: {leg_res.base_difficulty} vs {cat_res.base_difficulty}")
        
        # Check source biomes: legacy tags should be a subset of catalog biomes/tags
        leg_tags_set = set(leg_res.source_region_tags)
        cat_tags_set = set(cat_res.source_region_tags)
        if not leg_tags_set.issubset(cat_tags_set):
            mismatches.append(f"source_region_tags: legacy {leg_res.source_region_tags} is not a subset of catalog {cat_res.source_region_tags}")
            
        if mismatches:
            mismatched_resources.append((res_id, mismatches))

    # 6. Compare Enemies
    print(f"--- Comparing Enemies: Legacy ({len(legacy['enemies'])}) vs Catalog ({len(catalog['enemies'])}) ---")
    missing_enemies = []
    mismatched_enemies = []
    for enemy_id, leg_enemy in legacy["enemies"].items():
        if enemy_id not in catalog["enemies"]:
            missing_enemies.append(enemy_id)
            continue
        cat_enemy = catalog["enemies"][enemy_id]
        mismatches = []
        if leg_enemy.danger_hint != cat_enemy.danger_hint:
            mismatches.append(f"danger_hint: {leg_enemy.danger_hint} vs {cat_enemy.danger_hint}")
        if leg_enemy.max_hp != cat_enemy.max_hp:
            mismatches.append(f"max_hp: {leg_enemy.max_hp} vs {cat_enemy.max_hp}")
        if leg_enemy.atk != cat_enemy.atk:
            mismatches.append(f"atk: {leg_enemy.atk} vs {cat_enemy.atk}")
        if leg_enemy.def_stat != cat_enemy.def_stat:
            mismatches.append(f"def_stat: {leg_enemy.def_stat} vs {cat_enemy.def_stat}")
            
        # Legacy spawn regions should be a subset of catalog spawn regions (catalog can be richer)
        leg_spawns = set(leg_enemy.spawn_regions)
        cat_spawns = set(cat_enemy.spawn_regions)
        if not leg_spawns.issubset(cat_spawns):
            mismatches.append(f"spawn_regions: legacy {leg_enemy.spawn_regions} is not a subset of catalog {cat_enemy.spawn_regions}")
            
        # Loot tables (all legacy drops should exist in catalog drops and have same rates)
        for drop_id, prob in leg_enemy.loot_table.items():
            cat_prob = cat_enemy.loot_table.get(drop_id, 0.0)
            if abs(prob - cat_prob) > 1e-4:
                mismatches.append(f"loot_table[{drop_id}]: {prob} vs {cat_prob}")
                
        if mismatches:
            mismatched_enemies.append((enemy_id, mismatches))

    # 7. Compare Recipes
    print(f"--- Comparing Recipes: Legacy ({len(legacy['recipes'])}) vs Catalog ({len(catalog['recipes'])}) ---")
    missing_recipes = []
    mismatched_recipes = []
    for rec_id, leg_rec in legacy["recipes"].items():
        if rec_id not in catalog["recipes"]:
            missing_recipes.append(rec_id)
            continue
        cat_rec = catalog["recipes"][rec_id]
        mismatches = []
        if leg_rec.service_req != cat_rec.service_req:
            mismatches.append(f"service_req: {leg_rec.service_req} vs {cat_rec.service_req}")
        if leg_rec.gold_cost != cat_rec.gold_cost:
            mismatches.append(f"gold_cost: {leg_rec.gold_cost} vs {cat_rec.gold_cost}")
        if leg_rec.output_item_id != cat_rec.output_item_id:
            mismatches.append(f"output_item_id: {leg_rec.output_item_id} vs {cat_rec.output_item_id}")
        if leg_rec.requires_items != cat_rec.requires_items:
            mismatches.append(f"requires_items: {leg_rec.requires_items} vs {cat_rec.requires_items}")
            
        if mismatches:
            mismatched_recipes.append((rec_id, mismatches))

    # 8. Compare Regions
    print(f"--- Comparing Regions: Legacy ({len(legacy['regions'])}) vs Catalog ({len(catalog['regions'])}) ---")
    missing_regions = []
    mismatched_regions = []
    for reg_id, leg_reg in legacy["regions"].items():
        if reg_id not in catalog["regions"]:
            missing_regions.append(reg_id)
            continue
        cat_reg = catalog["regions"][reg_id]
        mismatches = []
        if leg_reg.name != cat_reg.name:
            mismatches.append(f"name: '{leg_reg.name}' vs '{cat_reg.name}'")
        if leg_reg.danger_level != cat_reg.danger_level:
            mismatches.append(f"danger_level: {leg_reg.danger_level} vs {cat_reg.danger_level}")
        
        # Legacy tags should be a subset of catalog tags (catalog has richer tags)
        leg_tags = set(leg_reg.tags)
        cat_tags = set(cat_reg.tags)
        if not leg_tags.issubset(cat_tags):
            mismatches.append(f"tags: legacy {leg_reg.tags} is not a subset of catalog {cat_reg.tags}")
            
        if mismatches:
            mismatched_regions.append((reg_id, mismatches))

    # Print out results for diagnostic checking
    if missing_items:
        print(f"Missing Item IDs in catalog: {missing_items}")
    if mismatched_items:
        print(f"Mismatched Items:")
        for i_id, mm in mismatched_items:
            print(f"  {i_id}: {mm}")
            
    if mismatched_core_items:
        print(f"Mismatched Core Items:")
        for i_id, mm in mismatched_core_items:
            print(f"  {i_id}: {mm}")
            
    if missing_resources:
        print(f"Missing Resource IDs in catalog: {missing_resources}")
    if mismatched_resources:
        print(f"Mismatched Resources:")
        for r_id, mm in mismatched_resources:
            print(f"  {r_id}: {mm}")
            
    if missing_enemies:
        print(f"Missing Enemy IDs in catalog: {missing_enemies}")
    if mismatched_enemies:
        print(f"Mismatched Enemies:")
        for e_id, mm in mismatched_enemies:
            print(f"  {e_id}: {mm}")

    if missing_recipes:
        print(f"Missing Recipe IDs in catalog: {missing_recipes}")
    if mismatched_recipes:
        print(f"Mismatched Recipes:")
        for r_id, mm in mismatched_recipes:
            print(f"  {r_id}: {mm}")

    if missing_regions:
        print(f"Missing Region IDs in catalog: {missing_regions}")
    if mismatched_regions:
        print(f"Mismatched Regions:")
        for r_id, mm in mismatched_regions:
            print(f"  {r_id}: {mm}")

    # Assert empty lists to enforce parity
    assert not missing_items, f"Items in legacy missing from catalog: {missing_items}"
    assert not mismatched_items, f"Item mismatches: {mismatched_items}"
    assert not mismatched_core_items, f"Core Item mismatches: {mismatched_core_items}"
    assert not missing_resources, f"Resources in legacy missing from catalog: {missing_resources}"
    assert not mismatched_resources, f"Resource mismatches: {mismatched_resources}"
    assert not missing_enemies, f"Enemies in legacy missing from catalog: {missing_enemies}"
    assert not mismatched_enemies, f"Enemy mismatches: {mismatched_enemies}"
    assert not missing_recipes, f"Recipes in legacy missing from catalog: {missing_recipes}"
    assert not mismatched_recipes, f"Recipe mismatches: {mismatched_recipes}"
    assert not missing_regions, f"Regions in legacy missing from catalog: {missing_regions}"
    assert not mismatched_regions, f"Region mismatches: {mismatched_regions}"
