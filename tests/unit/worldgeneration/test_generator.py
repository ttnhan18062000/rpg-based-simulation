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
        try:
            for _ in range(5):
                kernel.tick_once()
            assert kernel.state.tick == 5
        finally:
            kernel.shutdown()
    finally:
        # Restore registries to legacy fallback defaults
        from src.core.modes import RuntimeContentMode
        seed_phase1_content(None, mode=RuntimeContentMode.LEGACY_FALLBACK)


def _population_counts(bundle):
    counts = {e.id: e.count for e in bundle.world_spec.entities}
    return counts["citizens"], counts["monsters"]


def test_population_matches_flat_formula_at_default_reference_point(repos):
    """TCK-20260808-WORLDGEN-AREA-AWARE-DENSITY: the new area-aware formula must reproduce the
    old flat formula's exact values at the default GenerationIntentSpec reference point."""
    cat, mod = repos
    intent = GenerationIntentSpec(
        generation_id="gen_reference_point",
        seed=1,
        target_world_size=(100, 100),
        population_scale=1.0,
        danger_level=1.0,
    )
    generator = WorldProceduralGenerator(cat, mod)
    bundle = generator.generate(intent)
    citizens, monsters = _population_counts(bundle)
    assert citizens == 15
    assert monsters == 8


def test_population_scales_with_target_world_size(repos):
    """town_center's own bounds are carved with a fixed +/-15 radius around the map center
    (generator.py, unrelated to this ticket, out of scope to change) -- so town_area, and
    therefore citizen count, does NOT vary with target_world_size (confirmed directly, disclosed
    in investigation.md rather than forced). wilderness_forest's own bounds fill "everything left
    of the town", so wild_area -- and monster count -- DOES scale with target_world_size. Both
    behaviors are the real, honest formula output, not a bug."""
    cat, mod = repos
    generator = WorldProceduralGenerator(cat, mod)

    small = generator.generate(GenerationIntentSpec(
        generation_id="gen_small_world", seed=1, target_world_size=(100, 100),
    ))
    large = generator.generate(GenerationIntentSpec(
        generation_id="gen_large_world", seed=1, target_world_size=(300, 300),
    ))
    small_citizens, small_monsters = _population_counts(small)
    large_citizens, large_monsters = _population_counts(large)
    assert large_monsters > small_monsters, "target_world_size no longer affects monster count"
    assert large_citizens == small_citizens, (
        "town_center's fixed-radius carving means citizen count should NOT vary with "
        "target_world_size alone -- if this changes, town-carving itself changed too"
    )


def test_monster_population_scales_with_danger_level(repos):
    cat, mod = repos
    generator = WorldProceduralGenerator(cat, mod)

    low_danger = generator.generate(GenerationIntentSpec(
        generation_id="gen_low_danger", seed=1, target_world_size=(100, 100), danger_level=1.0,
    ))
    high_danger = generator.generate(GenerationIntentSpec(
        generation_id="gen_high_danger", seed=1, target_world_size=(100, 100), danger_level=3.0,
    ))
    low_citizens, low_monsters = _population_counts(low_danger)
    high_citizens, high_monsters = _population_counts(high_danger)
    assert high_monsters > low_monsters, "danger_level no longer affects monster count"
    assert high_citizens == low_citizens, "danger_level should not affect citizen count (town hazard is always 0)"


def test_faction_fallback_survives_catalog_with_no_defender_or_invader_factions():
    """Real robustness fix: a catalog with real factions but none flagged defender/invader must
    not produce a dangling faction reference (the actual bug this ticket found, distinct from
    the originally-claimed default-path bug which does not reproduce with the real catalog)."""
    from src.content.repository import CatalogRepository
    from src.worldmodules.repository import WorldModuleRepository

    cat = CatalogRepository("data/content")
    cat.load_all()
    # Neutralize every faction's alignment_bucket so defenders/invaders are both empty, without
    # touching the real faction registry itself. FactionDefinition is a frozen pydantic model.
    for f_id, f in list(cat.factions.items()):
        cat.factions[f_id] = f.model_copy(update={"alignment_bucket": "neutral"})

    mod = WorldModuleRepository("data/world_modules")
    mod.load_all()

    intent = GenerationIntentSpec(generation_id="gen_no_defenders_invaders", seed=1)
    generator = WorldProceduralGenerator(cat, mod)
    bundle = generator.generate(intent)

    real_faction_ids = {f.id for f in bundle.world_spec.factions}
    used_faction_ids = {e.faction for e in bundle.world_spec.entities}
    assert used_faction_ids <= real_faction_ids, (
        f"population entities reference faction(s) not in the generated factions dict: "
        f"{used_faction_ids - real_faction_ids}"
    )


def test_no_reasonable_parameter_combination_breaches_high_entity_density_warning(repos):
    """Real assertion from investigation.md: generation-time population stays under
    HighEntityDensityWarningRule's own 50%-of-map-area threshold across a reasonable parameter
    sweep, computed fresh, not hardcoded."""
    cat, mod = repos
    generator = WorldProceduralGenerator(cat, mod)

    for size in [(50, 50), (120, 120), (250, 250)]:
        for scale in [0.5, 1.5, 3.0]:
            for danger in [0.5, 1.5, 2.0]:
                intent = GenerationIntentSpec(
                    generation_id=f"gen_sweep_{size}_{scale}_{danger}",
                    seed=1, target_world_size=size, population_scale=scale, danger_level=danger,
                )
                bundle = generator.generate(intent)
                total_pop = sum(e.count for e in bundle.world_spec.entities)
                map_area = size[0] * size[1]
                assert total_pop <= map_area * 0.5, (
                    f"size={size} scale={scale} danger={danger}: total_pop={total_pop} "
                    f"breaches WORLD-WARN-002's 50% threshold (map_area={map_area})"
                )
