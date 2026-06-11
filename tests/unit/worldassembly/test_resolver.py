# Compliance IDs: WORLD-ASM-TEST
import pytest
from src.content.repository import CatalogRepository
from src.worldassembly.resolver import CompileProfileResolver
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.schema import WorldSpec, TopologySpec, RegionSpec, FactionSpec, PopulationSpec, ResourceNodeSpec, BuildingSpec

pytestmark = pytest.mark.worldassembly


@pytest.fixture
def base_repo():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def test_compile_profile_resolver_overrides(base_repo):
    """Verify that profiles properly override and resolve compiled defaults."""
    # 1. Setup mock spec with stats_profile configured
    spec = WorldSpec(
        schema_version="worldspec.v1",
        world_id="asm_test",
        name="Asm Test",
        topology=TopologySpec(width=10, height=10, coordinate_system="grid"),
        regions=[RegionSpec(id="r1", type="town", bounds=(0, 0, 9, 9))],
        factions=[FactionSpec(id="villagers", type="civilian")],
        entities=[
            PopulationSpec(
                id="pop_custom",
                count=1,
                role="hero",
                faction="villagers",
                spawn_region="r1"
            )
        ],
        resources=[
            ResourceNodeSpec(
                id="res_wood",
                resource_type="wood_node",
                count=5,
                region="r1"
            )
        ],
        buildings=[
            BuildingSpec(
                id="bld_shop",
                type="shop",
                region="r1"
            )
        ]
    )

    resolver = CompileProfileResolver(base_repo)
    context = resolver.resolve(spec)

    # Compile the spec WITH the resolved context
    state, report = WorldCompiler.compile(spec, seed=42, context=context)

    # 2. Assert Entity properties resolved from hero_base stats profile
    entity = state.entities[1]
    assert entity.combat.hp == 100
    assert entity.combat.max_hp == 100
    assert entity.combat.atk == 10

    # 3. Assert Resource properties resolved wood_node catalog spec
    node = state.resource_nodes[10000]
    assert node.required_ticks == 10  # from wood_node definition

    # 4. Assert Building properties resolved general_store (shop) catalog spec
    building = state.buildings[20000]
    assert building.hp == 500  # from shop definition


def test_compiler_backward_compatibility():
    """Verify that compiling without a context preserves traditional legacy defaults."""
    spec = WorldSpec(
        schema_version="worldspec.v1",
        world_id="asm_test",
        name="Asm Test",
        topology=TopologySpec(width=10, height=10, coordinate_system="grid"),
        regions=[RegionSpec(id="r1", type="town", bounds=(0, 0, 9, 9))],
        factions=[FactionSpec(id="villagers", type="civilian")],
        entities=[
            PopulationSpec(
                id="pop_custom",
                count=1,
                role="hero",
                faction="villagers",
                spawn_region="r1"
            )
        ],
        resources=[
            ResourceNodeSpec(
                id="res_wood",
                resource_type="wood_node",
                count=5,
                region="r1"
            )
        ],
        buildings=[
            BuildingSpec(
                id="bld_shop",
                type="shop",
                region="r1"
            )
        ]
    )

    # Compile WITHOUT context
    state, report = WorldCompiler.compile(spec, seed=42)

    # Verify standard legacy parameters are correctly defaulted
    entity = state.entities[1]
    assert entity.combat.hp == 100
    assert entity.combat.atk == 10
    
    node = state.resource_nodes[10000]
    assert node.required_ticks == 10

    building = state.buildings[20000]
    assert building.hp == 500


def test_v2_service_refs_assembly_is_documented_gap():
    """Guard test: service_refs is computed in contributions but WorldSpec has no services field.

    If WorldSpec gains a 'services' field, this test will fail — that is the signal to add
    the v2 service merge loop in WorldModuleAssemblyResolver.assemble() and update
    docs/guidelines/v2_intentional_divergences.md (entry 2.19).
    """
    from src.worldassembly.schema import ResolvedModuleContribution
    from src.worldbuilding.schema import WorldSpec

    # service_refs must exist in the contribution schema with the correct type
    fields = ResolvedModuleContribution.model_fields
    assert "service_refs" in fields, "ResolvedModuleContribution must have service_refs field"
    annotation = str(fields["service_refs"].annotation)
    assert "Dict" in annotation or "dict" in annotation, (
        f"service_refs must be Dict[str, int], got {annotation}"
    )

    # WorldSpec must NOT yet have a services field — the gap is intentional and documented
    assert "services" not in WorldSpec.model_fields, (
        "WorldSpec gained a 'services' field — add the v2 service merge loop in "
        "WorldModuleAssemblyResolver.assemble() (parallel to the v2 building loop), "
        "update docs/guidelines/v2_intentional_divergences.md (entry 2.19), "
        "and update docs/parity_ledger/substrate.yaml (SUB-367) to status: verified."
    )


def test_contribution_snapshot_after_normalization(base_repo):
    """Contribution record fields must match the normalized module's structure.

    Uses a minimal empty-field module to assert that resolve_module_contribution
    returns empty collections of the correct types when no content is specified.
    """
    from src.worldmodules.schema import WorldModuleSpec
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    from src.worldmodules.repository import WorldModuleRepository
    from src.worldassembly.resolver import WorldAssemblyResolver

    spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_empty_module",
        module_type="terrain",
        display_name="Test Empty Module",
    )
    normalized = WorldModuleAuthoringNormalizer.normalize(spec)

    module_repo = WorldModuleRepository("data/content/world_modules")
    resolver = WorldAssemblyResolver(base_repo, module_repo)
    contribution = resolver.resolve_module_contribution(normalized)

    # Empty module produces empty collections of the correct types
    assert contribution.resource_refs == {}
    assert contribution.building_refs == {}
    assert contribution.service_refs == {}
    assert isinstance(contribution.resource_refs, dict)
    assert isinstance(contribution.building_refs, dict)
    assert isinstance(contribution.service_refs, dict)
    assert contribution.regions == []
    assert contribution.factions == []
    assert contribution.population_refs == []
    assert contribution.resolved_population_specs == []
    assert contribution.biome_refs == []
    assert contribution.ecology_refs == []
    assert contribution.relationship_refs == []


def test_resolve_module_contribution_rejects_raw_spec(base_repo):
    """resolve_module_contribution must raise TypeError when passed a raw WorldModuleSpec.

    Callers must normalize via WorldModuleAuthoringNormalizer.normalize() first.
    """
    from src.worldmodules.schema import WorldModuleSpec
    from src.worldmodules.repository import WorldModuleRepository
    from src.worldassembly.resolver import WorldAssemblyResolver

    raw_spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="test_raw_spec",
        module_type="terrain",
        display_name="Test Raw Spec",
    )

    module_repo = WorldModuleRepository("data/content/world_modules")
    resolver = WorldAssemblyResolver(base_repo, module_repo)
    with pytest.raises(TypeError, match="resolve_module_contribution requires NormalizedWorldModule"):
        resolver.resolve_module_contribution(raw_spec)
