import os
import pytest
from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
from src.worldassembly.resolver import WorldAssemblyResolver

pytestmark = pytest.mark.worldassembly

MODULE_MATRIX = [
    "frontier_village_core",
    "wolf_den_near_forest",
    "goblin_camp_conflict",
    "old_mine_resource_loop",
    "bandit_road_trade_pressure",
    "moon_cult_ruins",
    "undead_battlefield",
    # TCK-20260614-WORLDDAT-NEWMODS: new modules demonstrating unified schema capabilities
    "forest_deep_ecology",
    "ruins_mystery_quest",
    "trading_company_hub",
    "scalable_bandit_camp",
    # TCK-20260619-E13B-MODULE-TYPES: terrain and population module types
    "mountain_pass",
    "river_crossing",
    "nomadic_herd",
    "settled_quarter",
    # TCK-20260630-WORLD-TEST-MATRIX: previously untested modules
    "hero_adventurers",
    "orc_clan_territory",
    "forest_warden_grove",
    "sunken_swamp_border",
    "survivor_camp_shelter",
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
        assert set(spec.populations) == set(normalized.population_refs)
        
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
        assert len(contribution.population_refs) == len(normalized.population_refs)
        assert len(contribution.resource_refs) == len(normalized.resources)
        assert len(contribution.building_refs) == len(normalized.buildings)


def test_hazard_kind_survives_module_pipeline(repos):
    """TCK-20260701-HAZARD-KIND-RESOLVER-GAP regression: hazard_kind authored in a real
    module's YAML must survive the full worldcomposition.v1 pipeline (module YAML ->
    WorldModuleAuthoringNormalizer.normalize() -> WorldAssemblyResolver.resolve_module_contribution()
    -> resolved RegionSpec), not just direct object construction. Prior to this fix,
    RegionRecipeSpec had no hazard_kind field at all (extra="forbid" rejected the YAML
    outright), and even after adding the field, the resolver silently dropped it back to
    the "PHYSICAL" default instead of forwarding the authored value.
    """
    cat, mod = repos
    resolver = WorldAssemblyResolver(cat, mod)

    module_id = "wolf_den_near_forest"
    spec = mod.get_module(module_id)
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)

    # The raw module YAML authors hazard_kind="NATURAL_TERRAIN" for both regions.
    normalized_kinds = {r.id: getattr(r, "hazard_kind", None) for r in normalized.regions}
    assert normalized_kinds == {"near_forest": "NATURAL_TERRAIN", "wolf_den": "NATURAL_TERRAIN"}

    contribution = resolver.resolve_module_contribution(normalized)
    resolved_kinds = {r.id: r.hazard_kind for r in contribution.regions}
    assert resolved_kinds == {"near_forest": "NATURAL_TERRAIN", "wolf_den": "NATURAL_TERRAIN"}

    # A module that does not author hazard_kind must still resolve, defaulting to PHYSICAL
    # (i.e. the field is optional end-to-end, not just at the RegionRecipeSpec layer).
    default_module_id = "frontier_village_core"
    default_spec = mod.get_module(default_module_id)
    default_normalized = WorldModuleAuthoringNormalizer.normalize(default_spec)
    default_contribution = resolver.resolve_module_contribution(default_normalized)
    assert all(r.hazard_kind == "PHYSICAL" for r in default_contribution.regions)


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
