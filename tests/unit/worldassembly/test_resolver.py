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
