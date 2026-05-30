# Compliance IDs: WORLD-GEN-TEST
import pytest
import json
from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldgeneration.schema import GenerationIntentSpec
from src.worldgeneration.generator import WorldProceduralGenerator
from src.worldbuilding.compiler import WorldCompiler


@pytest.fixture
def repos():
    cat = CatalogRepository("data/content")
    cat.load_all()
    mod = WorldModuleRepository("data/world_modules")
    mod.load_all()
    return cat, mod


def test_procedural_generator_valid_world(repos):
    """Verify generated output conforms to worldspec.v1, region bounds are valid, and assets are populated."""
    cat, mod = repos

    intent = GenerationIntentSpec(
        generation_id="gen_valid_test",
        seed=12345,
        target_world_size=(120, 120),
        resource_density=0.8,
        population_scale=1.2
    )

    generator = WorldProceduralGenerator(cat, mod)
    bundle = generator.generate(intent)

    # 1. Assert Schema conforms to worldspec.v1
    spec = bundle.world_spec
    assert spec.schema_version == "worldspec.v1"
    assert spec.world_id == "gen_valid_test"
    assert spec.topology.width == 120
    assert spec.topology.height == 120

    # 2. Assert Region counts and bounds
    assert "town_center" in [r.id for r in spec.regions]
    town = [r for r in spec.regions if r.id == "town_center"][0]
    min_x, min_y, max_x, max_y = town.bounds
    assert min_x >= 0 and max_x < 120
    assert min_y >= 0 and max_y < 120

    # 3. Assert Assets placed
    assert len(spec.buildings) == 3
    assert len(spec.resources) > 0
    assert len(spec.entities) == 2


def test_procedural_generator_determinism(repos):
    """Verify procedural runs are 100% deterministic and different seeds yield different outcomes."""
    cat, mod = repos

    intent1 = GenerationIntentSpec(
        generation_id="gen_det_test",
        seed=42,
        target_world_size=(100, 100)
    )

    intent2 = GenerationIntentSpec(
        generation_id="gen_det_test",
        seed=42,
        target_world_size=(100, 100)
    )

    intent_diff = GenerationIntentSpec(
        generation_id="gen_det_test",
        seed=99,
        target_world_size=(100, 100)
    )

    generator = WorldProceduralGenerator(cat, mod)

    # Generate 1
    bundle1 = generator.generate(intent1)
    dump1_spec = json.dumps(bundle1.world_spec.model_dump(), sort_keys=True)
    dump1_prov = json.dumps(bundle1.provenance_manifest.model_dump(), sort_keys=True)

    # Generate 2
    bundle2 = generator.generate(intent2)
    dump2_spec = json.dumps(bundle2.world_spec.model_dump(), sort_keys=True)
    dump2_prov = json.dumps(bundle2.provenance_manifest.model_dump(), sort_keys=True)

    # Determinism assertion
    assert dump1_spec == dump2_spec
    assert dump1_prov == dump2_prov

    # Seed difference assertion
    bundle_diff = generator.generate(intent_diff)
    dump_diff_spec = json.dumps(bundle_diff.world_spec.model_dump(), sort_keys=True)
    assert dump_diff_spec != dump1_spec


def test_procedural_generator_compile_readiness(repos):
    """Verify that a procedurally generated WorldSpec compiles perfectly into an engine AuthoritativeState."""
    cat, mod = repos

    intent = GenerationIntentSpec(
        generation_id="gen_compile_test",
        seed=777,
        target_world_size=(80, 80)
    )

    generator = WorldProceduralGenerator(cat, mod)
    bundle = generator.generate(intent)

    # Compile the spec
    state, report = WorldCompiler.compile(bundle.world_spec, seed=intent.seed)

    # Assert running state properties are correctly loaded
    assert state.seed == 777
    assert len(state.regions) == 3
    assert len(state.buildings) == 3
    assert report["state_hash"] != ""
