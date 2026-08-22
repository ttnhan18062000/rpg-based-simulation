"""TCK-20260821-WOLF-DEN-NOISE-MIGRATION: real-content proof that wolf_den_near_forest's
terrain_variants migration compiles per-tile variation correctly, that wolf_den (declared
second in the module's regions: list) wins the intra-module overlap box exactly as
Decision 3 documents, and that recompiling the same world+seed is bit-identical.

Uses a minimal synthetic composition (frontier_village_core + wolf_den_near_forest) instead
of a real shipping composition (e.g. wilderness_survival.yaml), because every other real
composition that includes wolf_den_near_forest also includes at least one other module whose
own region bounds overlap near_forest/wolf_den (survivor_camp_shelter, bandit_road_trade_pressure,
goblin_camp_conflict — see investigation.md Decision 3b), which would make these tests
entangled with a separate, already-documented cross-module overlap concern instead of
isolating the intra-module overlap this ticket's own AC targets.
"""
import pytest

from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldassembly.resolver import WorldAssemblyResolver
from src.worldassembly.schema import WorldCompositionSpec
from src.worldbuilding.compiler import WorldCompiler
from src.platform.rng import DeterministicRNG
from src.core.enums import Domain

pytestmark = pytest.mark.worldassembly

GENERATION_SEED = 4242


def _make_comp():
    return WorldCompositionSpec.model_validate({
        "schema_version": "worldcomposition.v1",
        "world_id": "wolf_den_noise_migration_test",
        "name": "Wolf Den Noise Migration Test",
        "modules": ["frontier_village_core", "wolf_den_near_forest"],
        "generation_seed": GENERATION_SEED,
    })


@pytest.fixture(scope="module")
def compiled_state():
    cat = CatalogRepository("data/content")
    cat.load_all()
    mod = WorldModuleRepository()
    mod.load_all()
    spec = _make_comp()
    bundle = WorldAssemblyResolver(cat, mod).assemble(spec)
    state, report = WorldCompiler.compile(
        bundle.world_spec, seed=spec.generation_seed, context=bundle.compile_context
    )
    return state


def test_wolf_den_near_forest_compiles_with_per_tile_terrain_variation(compiled_state):
    state = compiled_state

    # Base fill outside any region.
    assert state.terrain[(0, 0)] == "PLAIN"

    # frontier_village_core's hometown region (x:[10,40], y:[10,40]) does not overlap
    # either wolf-den region and declares no terrain_variants, so it keeps its own flat
    # "plain" fill untouched by this migration.
    for x in range(10, 41):
        for y in range(10, 41):
            assert state.terrain[(x, y)] == "plain"

    # near_forest's own variation, excluding the wolf_den overlap box (x:[70,90], y:[30,55])
    # so this check is isolated to tiles where near_forest is guaranteed the last writer.
    near_forest_own_terrains = set()
    for x in range(45, 91):
        for y in range(10, 56):
            if x < 70 or y < 30 or y > 55:
                near_forest_own_terrains.add(state.terrain[(x, y)])
    assert near_forest_own_terrains - {"forest"}, (
        "expected at least one non-forest tile in near_forest's own (non-overlap) bounds"
    )

    # wolf_den's own variation across its full bounds (always the last writer for every
    # tile in its own bounds in this 2-module composition).
    wolf_den_terrains = set()
    for x in range(70, 106):
        for y in range(30, 71):
            wolf_den_terrains.add(state.terrain[(x, y)])
    assert wolf_den_terrains - {"forest"}, (
        "expected at least one non-forest tile in wolf_den's bounds"
    )


def _expected_wolf_den_terrain(rng, x, y):
    region_hash = 0
    for ch in "wolf_den":
        region_hash = (region_hash * 31 + ord(ch)) & 0xFFFFFFFF
    tile_offset = ((x & 0xFFFF) << 16) | (y & 0xFFFF)
    entity_id = (region_hash ^ tile_offset) & 0xFFFFFFFF
    return rng.weighted_choice(
        Domain.INIT, tick=0, entity_id=entity_id,
        seq=["forest", "swamp"], weights=[3.0, 1.0], sub_id=1,
    )


def test_wolf_den_overlap_box_resolves_to_wolf_den_terrain(compiled_state):
    state = compiled_state
    rng = DeterministicRNG(GENERATION_SEED)  # must match _make_comp()'s generation_seed
    for x in range(70, 91):
        for y in range(30, 56):
            assert state.terrain[(x, y)] == _expected_wolf_den_terrain(rng, x, y)


def test_wolf_den_near_forest_recompile_same_seed_is_bit_identical():
    cat = CatalogRepository("data/content")
    cat.load_all()
    mod = WorldModuleRepository()
    mod.load_all()

    spec = _make_comp()

    bundle_a = WorldAssemblyResolver(cat, mod).assemble(spec)
    state_a, report_a = WorldCompiler.compile(
        bundle_a.world_spec, seed=spec.generation_seed, context=bundle_a.compile_context
    )

    bundle_b = WorldAssemblyResolver(cat, mod).assemble(spec)
    state_b, report_b = WorldCompiler.compile(
        bundle_b.world_spec, seed=spec.generation_seed, context=bundle_b.compile_context
    )

    assert state_a.terrain == state_b.terrain
    assert report_a["state_hash"] == report_b["state_hash"]

    other_seed_spec = WorldCompositionSpec.model_validate({
        "schema_version": "worldcomposition.v1",
        "world_id": "wolf_den_noise_migration_test",
        "name": "Wolf Den Noise Migration Test",
        "modules": ["frontier_village_core", "wolf_den_near_forest"],
        "generation_seed": 9999,
    })
    bundle_c = WorldAssemblyResolver(cat, mod).assemble(other_seed_spec)
    state_c, report_c = WorldCompiler.compile(
        bundle_c.world_spec, seed=other_seed_spec.generation_seed, context=bundle_c.compile_context
    )

    def _wolf_den_region_tiles(state):
        return {
            (x, y): state.terrain[(x, y)]
            for x in range(45, 106)
            for y in range(10, 71)
        }

    assert _wolf_den_region_tiles(state_a) != _wolf_den_region_tiles(state_c)
