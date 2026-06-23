import pytest
from src.content.repository import CatalogRepository
from src.core.registries import seed_phase1_content, ItemRegistry, ResourceRegistry, EnemyRegistry, RecipeRegistry, RegionRegistry, ServiceRegistry
from src.core.modes import RuntimeContentMode


@pytest.fixture(autouse=True)
def cleanup_registries():
    """Automatically reset registries to default hardcoded fallback state after each test."""
    yield
    seed_phase1_content(None, mode=RuntimeContentMode.LEGACY_FALLBACK)


def test_production_catalog_cross_references():
    """Verify relational references across the loaded production catalog collections are valid."""
    repo = CatalogRepository("data/content")
    repo.load_all()
    seed_phase1_content(repo)

    # 1. Verify Enemy Projections link to valid Archetypes, Stats, and Items
    for proj_id, proj in repo.legacy_enemy_projections.items():
        # Check Archetype references
        arch = repo.get_entity_archetype(proj.archetype_id)
        assert arch is not None, f"Enemy projection '{proj_id}' references non-existent archetype '{proj.archetype_id}'"
        
        # Check Stats Profile reference through Archetype
        stats = repo.get_stats_profile(arch.stat_profile)
        assert stats is not None, f"Archetype '{arch.id}' references non-existent stats profile '{arch.stat_profile}'"
        
        # Check loot table drops exist in items
        for drop_item_id in proj.loot_table:
            assert drop_item_id in repo.items, f"Enemy projection '{proj_id}' drops non-existent item '{drop_item_id}'"
            
        # Check spawn regions exist in regions
        for spawn_region_id in proj.spawn_regions:
            assert spawn_region_id in repo.regions, f"Enemy projection '{proj_id}' spawns in non-existent region '{spawn_region_id}'"

    # 2. Verify Recipes ingredients and outputs link to valid Items
    for rec_id, rec in repo.recipes.items():
        # Check ingredients
        for ing_id in rec.ingredients:
            assert ing_id in repo.items, f"Recipe '{rec_id}' requires non-existent ingredient item '{ing_id}'"
        
        # Check outputs
        for out_id in rec.outputs:
            assert out_id in repo.items, f"Recipe '{rec_id}' produces non-existent output item '{out_id}'"
            
        # Check required service references existing service
        if rec.required_service:
            # Service can be blacksmith, healer, or exist in repo services
            assert rec.required_service in repo.services or rec.required_service in ("blacksmith", "healer"), \
                f"Recipe '{rec_id}' references non-existent service '{rec.required_service}'"

    # 3. Verify Services provided items link to valid Items
    for service_id, service in repo.services.items():
        for item_id in service.provided_items:
            assert item_id in repo.items, f"Service '{service_id}' provides non-existent item '{item_id}'"

    # 4. Verify Region allowed enemies exist in legacy enemy projections
    for reg_id, reg in repo.regions.items():
        for allowed_enemy in reg.allowed_enemy_ids:
            # Checks if it matches archetype id or legacy enemy id
            enemy_exists = any(
                proj.legacy_enemy_id == allowed_enemy or proj.archetype_id == allowed_enemy
                for proj in repo.legacy_enemy_projections.values()
            )
            assert enemy_exists, f"Region '{reg_id}' allows non-existent enemy reference '{allowed_enemy}'"
