# Compliance IDs: WORLD-ASM-TEST
import pytest
from src.content.repository import CatalogRepository
from src.worldassembly.resolver import CompileProfileResolver
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.schema import WorldSpec, TopologySpec, RegionSpec, FactionSpec, PopulationSpec, ResourceNodeSpec, BuildingSpec


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
