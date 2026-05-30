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
    
    prov1_dict = bundle1.provenance_manifest.model_dump()
    prov1_dict.pop("created_at")
    dump1_prov = json.dumps(prov1_dict, sort_keys=True)

    # Generate 2
    bundle2 = generator.generate(intent2)
    dump2_spec = json.dumps(bundle2.world_spec.model_dump(), sort_keys=True)
    
    prov2_dict = bundle2.provenance_manifest.model_dump()
    prov2_dict.pop("created_at")
    dump2_prov = json.dumps(prov2_dict, sort_keys=True)

    # Determinism assertion
    assert dump1_spec == dump2_spec
    assert dump1_prov == dump2_prov
    assert bundle1.provenance_manifest.content_fingerprint == bundle2.provenance_manifest.content_fingerprint

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

    # Compile the spec with context
    state, report = WorldCompiler.compile(bundle.world_spec, context=bundle.compile_context, seed=intent.seed)

    # Assert running state properties are correctly loaded
    assert state.seed == 777
    assert len(state.regions) == 3
    assert len(state.buildings) == 3
    assert report["state_hash"] != ""


def test_generated_world_catalog_smoke_simulation(repos):
    """Seed dynamic registries from catalog, generate, compile, and run a smoke simulation."""
    cat, mod = repos
    
    from src.core.registries import seed_phase1_content
    # Seed dynamic registries from content catalog
    seed_phase1_content(cat, required=True)
    
    try:
        intent = GenerationIntentSpec(
            generation_id="gen_smoke_test",
            seed=42,
            target_world_size=(80, 80)
        )
        
        generator = WorldProceduralGenerator(cat, mod)
        bundle = generator.generate(intent)
        
        # Compile generated world using ResolvedWorldBundle's compile_context
        state, report = WorldCompiler.compile(bundle.world_spec, context=bundle.compile_context, seed=intent.seed)
        
        # Execute 5 ticks in simulator kernel
        from src.engine.kernel import Kernel
        from src.config.profiles import RuntimeProfile, HardwareClass
        from src.platform.rng import DeterministicRNG

        profile = RuntimeProfile(
            name="test",
            hardware_class=HardwareClass.CLASS_C,
            max_ram_mb=512,
            max_cpu_percent=50,
            max_worker_count=0,
            max_queue_depth=100,
            max_replay_buffer_kb=1024,
            max_observability_budget_percent=5,
            max_tick_budget_ms=100.0,
            sampling_interval_ticks=1
        )
        rng = DeterministicRNG(state.seed)
        kernel = Kernel(profile, state, rng, flags={"audit_mode": True})
        for _ in range(5):
            kernel.tick_once()
            
        assert kernel.state.tick == 5
    finally:
        # Restore registries to legacy fallback defaults
        seed_phase1_content(None)
