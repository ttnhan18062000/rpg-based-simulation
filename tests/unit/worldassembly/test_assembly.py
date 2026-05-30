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


def test_resolved_bundle_includes_compile_context_and_preserves_profiles(repos):
    """Verify that ResolvedWorldBundle carries CompileContext and preserves explicit population recipe profiles."""
    cat, mod = repos

    from src.worldbuilding.recipe import PopulationRecipeSpec
    from src.content.schema import StatsProfileDefinition

    # Register mock elite_monster stats profile in catalog repo
    cat.stats_profiles["elite_monster"] = StatsProfileDefinition(
        **{
            "id": "elite_monster",
            "display_name": "Elite Monster Stats",
            "description": "Elite stats profile",
            "schema_version": "statsprofiledefinition.v1",
            "hp": 250,
            "max_hp": 250,
            "atk": 25,
            "def": 5,
            "attack_range": 2,
            "readiness": 120.0
        }
    )

    # Create a custom module with explicit population recipe profiles
    m = WorldModuleSpec(
        schema_version="worldmodule.v1",
        module_id="custom_profile_module",
        module_type="population",
        display_name="Custom Profile Module",
        population_recipes=[
            PopulationRecipeSpec(
                id="elite_guard_pop",
                role="guard",
                count=5,
                faction="town_council",
                spawn_region="town_center",
                stats_profile="elite_monster"  # Explicitly override standard role defaults
            )
        ]
    )

    # Register in module repo
    mod.modules["custom_profile_module"] = m
    mod.raw_data["custom_profile_module"] = m.model_dump()

    composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="profile_preservation_test",
        name="Profile Preservation Test",
        module_refs=[
            ModuleRefSpec(module_id="plains_layout", enabled=True, order=0),
            ModuleRefSpec(module_id="custom_profile_module", enabled=True, order=1)
        ]
    )

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(composition)

    # Assert CompileContext exists inside bundle
    assert bundle.compile_context is not None
    
    # Assert validation report exists
    assert bundle.validation_report is not None

    # Assert explicit profile preserved in compile_context
    pop_id = "pop_0"
    assert pop_id in bundle.compile_context.entities
    
    resolved_entity = bundle.compile_context.entities[pop_id]
    
    # "elite_monster" stats profile has hp=250, max_hp=250, atk=25 in standard catalog.
    # Verify the stats match "elite_monster" rather than default commoner/guard (e.g. hp=100)
    assert resolved_entity.hp == 250
    assert resolved_entity.atk == 25


def test_compile_context_serialization(repos):
    """Verify that CompileContext to_dict and from_dict perform lossless JSON-compatible serialization."""
    cat, mod = repos
    
    from src.worldassembly.schema import WorldCompositionSpec, ModuleRefSpec
    from src.worldassembly.resolver import WorldAssemblyResolver
    from src.worldassembly.context import CompileContext

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

    original_ctx = bundle.compile_context
    serialized = original_ctx.to_dict()

    # Verify standard types for JSON output
    assert isinstance(serialized, dict)
    assert "entities" in serialized
    assert "region_ownership" in serialized

    # Deserialize
    deserialized_ctx = CompileContext.from_dict(serialized)

    # Verify identical matching
    assert len(original_ctx.entities) == len(deserialized_ctx.entities)
    assert original_ctx.entities["pop_0"].hp == deserialized_ctx.entities["pop_0"].hp
    assert original_ctx.entities["pop_0"].atk == deserialized_ctx.entities["pop_0"].atk
    assert original_ctx.region_ownership == deserialized_ctx.region_ownership


def test_cli_resolve_and_compile_integration(repos):
    """Verify that handle_resolve and handle_compile execute correctly via programmatic argparse simulation."""
    cat, mod = repos
    import argparse
    import shutil
    import yaml
    from pathlib import Path
    from src.worldbuilding.cli import handle_resolve, handle_compile

    # Create a dynamic mock worldcomposition directory and file under data/worlds
    world_dir = Path("data/worlds/resolved_asm_test")
    world_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = world_dir / "world.yaml"

    composition_data = {
        "schema_version": "worldcomposition.v1",
        "world_id": "resolved_asm_test",
        "name": "Resolved Asm Test",
        "description": "Dynamic integration test composition",
        "global_parameters": {
            "topology_width": 100,
            "topology_height": 100
        },
        "module_refs": [
            {"module_id": "plains_layout", "enabled": True, "order": 0},
            {"module_id": "standard_villagers", "enabled": True, "order": 1}
        ]
    }

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(composition_data, f, sort_keys=False)

    class MockArgs:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    try:
        # Resolve resolved_asm_test
        args_resolve = MockArgs(world_id="resolved_asm_test")
        res_code = handle_resolve(args_resolve)
        assert res_code == 0

        # Ensure resolved files exist on disk
        resolved_dir = world_dir / "resolved"
        assert (resolved_dir / "world.resolved.yaml").is_file()
        assert (resolved_dir / "compile_context.json").is_file()
        assert (resolved_dir / "provenance_manifest.json").is_file()
        assert (resolved_dir / "assembly_report.json").is_file()
        assert (resolved_dir / "validation_report.json").is_file()

        # Compile from resolved assets
        args_compile = MockArgs(
            world_id="resolved_asm_test",
            seed=42,
            strict=False,
            output_report=None,
            from_resolved=True,
            legacy_fallback=False
        )
        comp_code = handle_compile(args_compile)
        assert comp_code == 0

    finally:
        # Clean up temporary test files and directories
        if world_dir.exists():
            shutil.rmtree(world_dir)



