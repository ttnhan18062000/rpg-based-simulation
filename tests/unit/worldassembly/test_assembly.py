# Compliance IDs: WORLD-ASM-TEST
import pytest
from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldassembly.schema import WorldCompositionSpec, ModuleRefSpec
from src.worldassembly.resolver import WorldAssemblyResolver
from src.worldbuilding.repository import WorldRepository
from src.worldmodules.schema import WorldModuleSpec
from src.worldbuilding.recipe import RegionRecipeSpec


@pytest.fixture
def repos():
    cat = CatalogRepository("data/content")
    cat.load_all()
    mod = WorldModuleRepository("data/world_modules")
    mod.load_all()
    return cat, mod


def test_structural_world_assembly_resolver(repos):
    """Verify that WorldAssemblyResolver merges modular regions, populations, and buildings safely."""
    cat, mod = repos

    composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="resolved_asm_test",
        name="Resolved Asm Test",
        module_refs=[
            ModuleRefSpec(module_id="plains_layout", enabled=True, order=0),
            ModuleRefSpec(module_id="standard_villagers", enabled=True, order=1)
        ]
    )

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(composition)

    # 1. Assert Assembled WorldSpec structure is clean worldspec.v1
    spec = bundle.world_spec
    assert spec.schema_version == "worldspec.v1"
    assert len(spec.regions) == 1
    assert spec.regions[0].id == "town_center"

    assert len(spec.entities) == 2
    roles = {e.role for e in spec.entities}
    assert "hero" in roles
    assert "worker" in roles

    # 2. Assert ProvenanceManifest lists origins accurately
    prov = bundle.provenance_manifest
    assert prov.world_id == "resolved_asm_test"
    assert prov.catalog_fingerprint != ""
    assert prov.entity_origins["town_center"] == "plains_layout"
    assert "standard_villagers" in prov.module_fingerprints


def test_id_collision_prevention(repos):
    """Verify duplicate IDs across merged layouts raise structural errors."""
    cat, mod = repos

    # Construct two distinct custom modules contributing duplicate region IDs
    m1 = WorldModuleSpec(
        schema_version="worldmodule.v1",
        module_id="mod1",
        module_type="terrain",
        display_name="Mod 1",
        regions=[
            RegionRecipeSpec(id="dup_region", type="forest", grid_bounds=(0, 0, 5, 5))
        ]
    )
    m2 = WorldModuleSpec(
        schema_version="worldmodule.v1",
        module_id="mod2",
        module_type="terrain",
        display_name="Mod 2",
        regions=[
            RegionRecipeSpec(id="dup_region", type="plain", grid_bounds=(6, 6, 9, 9))
        ]
    )

    # Register in module repo directly
    mod.modules["mod1"] = m1
    mod.raw_data["mod1"] = m1.model_dump()
    mod.modules["mod2"] = m2
    mod.raw_data["mod2"] = m2.model_dump()

    collision_composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="collision_test",
        name="Collision Test",
        module_refs=[
            ModuleRefSpec(module_id="mod1", enabled=True, order=0, namespace=None),
            ModuleRefSpec(module_id="mod2", enabled=True, order=1, namespace=None)
        ]
    )

    resolver = WorldAssemblyResolver(cat, mod)
    with pytest.raises(ValueError) as exc_info:
        resolver.assemble(collision_composition)
    assert "Duplicate region ID collision 'dup_region' detected" in str(exc_info.value)
