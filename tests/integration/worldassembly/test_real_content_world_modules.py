import os
import pytest
from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
from src.worldassembly.resolver import WorldAssemblyResolver


MODULE_MATRIX = [
    "frontier_village_core",
    "wolf_den_near_forest",
    "goblin_camp_conflict",
    "old_mine_resource_loop",
    "bandit_road_trade_pressure",
    "moon_cult_ruins",
    "undead_battlefield"
]


@pytest.fixture(scope="module")
def repos():
    cat = CatalogRepository("data/content")
    cat.load_all()
    
    # Use canonical path
    mod = WorldModuleRepository()
    mod.load_all()
    return cat, mod


def test_real_world_modules_load_from_data_content(repos):
    """Verify that all canonical module files load and pass schema validation."""
    cat, mod = repos
    
    # Verify that the repository found and loaded all files from data/content/world_modules
    assert len(mod.modules) >= len(MODULE_MATRIX)
    for module_id in MODULE_MATRIX:
        assert module_id in mod.modules, f"Module '{module_id}' not found in WorldModuleRepository"
        spec = mod.get_module(module_id)
        assert spec is not None
        assert spec.module_id == module_id


def test_real_world_modules_normalize(repos):
    """Verify that all canonical modules normalize cleanly without errors."""
    cat, mod = repos
    for module_id in MODULE_MATRIX:
        spec = mod.get_module(module_id)
        normalized = WorldModuleAuthoringNormalizer.normalize(spec)
        assert normalized is not None
        assert normalized.module_id == module_id


def test_real_world_modules_preserve_count_maps(repos):
    """Verify that module normalization preserves count maps and structure without data loss."""
    cat, mod = repos
    for module_id in MODULE_MATRIX:
        spec = mod.get_module(module_id)
        normalized = WorldModuleAuthoringNormalizer.normalize(spec)
        
        # Verify region boundaries/lists exist
        assert len(normalized.regions) == len(spec.regions)
        
        # Verify that populations, resources, and buildings are count-preserved
        assert set(spec.populations) == set(normalized.populations)
        
        # resources count-preservation
        if isinstance(spec.resources, dict):
            assert spec.resources == normalized.resources
        
        # buildings count-preservation
        if isinstance(spec.buildings, dict):
            assert spec.buildings == normalized.buildings


def test_real_world_modules_resolve_contributions(repos):
    """Verify that all canonical modules successfully compile and resolve into valid contributions."""
    cat, mod = repos
    resolver = WorldAssemblyResolver(cat, mod)
    
    for module_id in MODULE_MATRIX:
        spec = mod.get_module(module_id)
        normalized = WorldModuleAuthoringNormalizer.normalize(spec)
        
        # Resolve contribution
        contribution = resolver.resolve_module_contribution(normalized)
        assert contribution is not None
        
        # Verify regions, populations, resources, and buildings are mapped in contribution
        assert len(contribution.regions) == len(normalized.regions)
        assert len(contribution.population_refs) == len(normalized.populations)
        assert len(contribution.resource_refs) == len(normalized.resources)
        assert len(contribution.building_refs) == len(normalized.buildings)


def test_real_world_modules_reference_graph_edges_exist(repos):
    """Verify that references and relationships in modules build typed reference edges correctly."""
    cat, mod = repos
    # Check that each module's references can be resolved against the active catalog
    for module_id in MODULE_MATRIX:
        spec = mod.get_module(module_id)
        
        # Verify populations reference valid archetypes/factions
        for pop_id in spec.populations:
            assert (pop_id in cat.populations) or (pop_id in cat.entity_archetypes), f"Module '{module_id}' references invalid population recipe or archetype '{pop_id}'"

        # Verify resources reference valid types
        if isinstance(spec.resources, dict):
            for res_id in spec.resources:
                assert res_id in cat.resources, f"Module '{module_id}' references invalid resource '{res_id}'"

        # Verify buildings reference valid types
        if isinstance(spec.buildings, dict):
            for bld_type in spec.buildings:
                assert bld_type in cat.buildings, f"Module '{module_id}' references invalid building type '{bld_type}'"

        # Verify factions exist
        for faction_id in spec.factions:
            assert faction_id in cat.factions, f"Module '{module_id}' references invalid faction '{faction_id}'"
