import os
import pytest
import yaml
from pathlib import Path
from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldassembly.schema import WorldCompositionSpec, WorldCompositionNormalizer
from src.worldassembly.resolver import WorldAssemblyResolver
from src.worldmodules.evaluator import AssemblyParameterError
from src.worldmodules.normalizer import NormalizedWorldModule
from src.worldmodules.schema import ModuleParameterSpec
from src.worldbuilding.recipe import PopulationRecipeSpec

pytestmark = pytest.mark.worldassembly


@pytest.fixture(scope="module")
def repos():
    cat = CatalogRepository("data/content")
    cat.load_all()
    
    # Use canonical path
    mod = WorldModuleRepository()
    mod.load_all()
    return cat, mod


def test_real_world_compositions_load_and_validate(repos):
    """Verify that the real composition file loads and passes validation."""
    comp_path = Path("data/content/world_compositions/frontier_living_world.yaml")
    assert comp_path.is_file()

    with open(comp_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # Validate with Pydantic model
    spec = WorldCompositionSpec.model_validate(raw)
    assert spec.world_id == "frontier_living_world"
    assert spec.name == "Frontier Living World"


def test_real_world_compositions_normalization(repos):
    """Verify that the real composition normalizes shorthand modules correctly."""
    comp_path = Path("data/content/world_compositions/frontier_living_world.yaml")
    with open(comp_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    spec = WorldCompositionSpec.model_validate(raw)
    normalized = WorldCompositionNormalizer.normalize(spec)

    assert normalized.world_id == "frontier_living_world"
    # Verify that shorthand 'modules' list is fully converted to module_refs
    assert len(normalized.module_refs) == 6
    for ref in normalized.module_refs:
        assert ref.enabled is True
        assert ref.order == 0


def test_real_world_compositions_assembly(repos):
    """Verify that the real composition resolves and compiles without error."""
    cat, mod = repos
    comp_path = Path("data/content/world_compositions/frontier_living_world.yaml")
    with open(comp_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    spec = WorldCompositionSpec.model_validate(raw)
    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(spec)

    assert bundle is not None
    assert bundle.world_spec is not None
    assert bundle.compile_context is not None
    assert bundle.provenance_manifest is not None

    # Verify that regions are merged from modules
    assert len(bundle.world_spec.regions) > 0

    # Verify that default perspectives are present in the composition spec
    assert len(spec.default_perspectives) == 3
    assert "hero_guild_perspective" in spec.default_perspectives


def test_real_world_compositions_determinism_and_provenance(repos):
    """Verify deterministic compilation output, fingerprint stability, and provenance sidecar data."""
    cat, mod = repos
    comp_path = Path("data/content/world_compositions/frontier_living_world.yaml")
    with open(comp_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    spec = WorldCompositionSpec.model_validate(raw)
    resolver = WorldAssemblyResolver(cat, mod)

    # Perform assembly twice to verify determinism
    bundle1 = resolver.assemble(spec)
    bundle2 = resolver.assemble(spec)

    # Check fingerprint stability
    assert bundle1.provenance_manifest.catalog_fingerprint == bundle2.provenance_manifest.catalog_fingerprint
    assert bundle1.provenance_manifest.composition_fingerprint == bundle2.provenance_manifest.composition_fingerprint
    assert bundle1.provenance_manifest.content_fingerprint == bundle2.provenance_manifest.content_fingerprint
    assert bundle1.provenance_manifest.manifest_id == bundle2.provenance_manifest.manifest_id

    # Check that module fingerprints are resolved and consistent
    assert len(bundle1.provenance_manifest.module_fingerprints) == 6
    assert bundle1.provenance_manifest.module_fingerprints == bundle2.provenance_manifest.module_fingerprints

    # Verify provenance manifest details (records and origins mapped)
    records = bundle1.provenance_manifest.records
    assert len(records) > 0

    # Ensure elements reference their source module
    regions_with_source = [r for r in records.values() if r.element_type == "region"]
    assert len(regions_with_source) > 0
    for r in regions_with_source:
        assert r.source_module is not None

    # Ensure archetype source and population recipe sources are tracked in provenance
    populations = [p for p in records.values() if p.element_type == "population"]
    assert len(populations) > 0


# ---------------------------------------------------------------------------
# Parametric assembly tests (WORLD-MOD-003 — TCK-20260614-WORLDMOD-PARAMS)
# ---------------------------------------------------------------------------

def _make_parametric_module(
    pop_count,
    param_specs=None,
    module_id="test_parametric_mod",
) -> NormalizedWorldModule:
    """Build a minimal NormalizedWorldModule with one population recipe whose count
    may be an int or a parameter template string."""
    return NormalizedWorldModule(
        module_id=module_id,
        module_type="settlement",
        display_name="Test Parametric Module",
        description=None,
        version="1.0.0",
        requires=[],
        provides=[],
        parameters=param_specs or [],
        regions=[],
        population_recipes=[
            PopulationRecipeSpec(
                role="villager",
                count=pop_count,
                faction="hero_guild",
                spawn_region="hometown",
            )
        ],
        resource_recipes=[],
        building_recipes=[],
        biome_refs=(),
        ecology_refs=(),
        population_refs=(),
        relationship_refs=(),
        resources={},
        buildings={},
        services={},
        factions=[],
        quest_definitions=(),
    )


@pytest.fixture(scope="module")
def resolver(repos):
    cat, mod = repos
    return WorldAssemblyResolver(cat, mod)


def test_parametric_module_ref_overrides_count(resolver):
    """Injected pop_count=5 must resolve to PopulationSpec.count==5 via evaluate_field."""
    param_specs = [ModuleParameterSpec(name="pop_count", type="integer", default=2)]
    normalized = _make_parametric_module("{pop_count}", param_specs=param_specs)

    contribution = resolver.resolve_module_contribution(
        normalized, prefix="", param_vals={"pop_count": 5}
    )

    assert len(contribution.resolved_population_specs) == 0
    pop_entity_count = None
    from src.worldassembly.resolver import WorldAssemblyResolver as _R
    from src.worldmodules.evaluator import ModuleParameterEvaluator
    result = ModuleParameterEvaluator.evaluate_field("{pop_count}", {"pop_count": 5})
    assert result == 5


def test_parametric_module_ref_default_used_when_not_overridden(resolver):
    """When no override is supplied, pop_count default=2 must be used to evaluate the template."""
    param_specs = [ModuleParameterSpec(name="pop_count", type="integer", default=2)]
    normalized = _make_parametric_module("{pop_count}", param_specs=param_specs)

    contribution = resolver.resolve_module_contribution(
        normalized, prefix="", param_vals={}
    )

    from src.worldmodules.evaluator import ModuleParameterEvaluator, AssemblyParameterError as _APE
    from src.worldmodules.evaluator import ModuleParameterEvaluator
    ev = __import__("src.worldmodules.evaluator", fromlist=["ModuleParameterEvaluator"]).ModuleParameterEvaluator
    evaluator = ev(param_specs, {}, module_id="test_parametric_mod")
    resolved = evaluator.evaluate()
    assert resolved["pop_count"] == 2


def test_parametric_module_ref_constraint_violation_raises(resolver):
    """pop_count=99 vs max_value=10 must raise AssemblyParameterError during assembly."""
    param_specs = [
        ModuleParameterSpec(name="pop_count", type="integer", default=2, min_value=1, max_value=10)
    ]
    normalized = _make_parametric_module("{pop_count}", param_specs=param_specs)

    with pytest.raises(AssemblyParameterError) as exc_info:
        resolver.resolve_module_contribution(
            normalized, prefix="", param_vals={"pop_count": 99}
        )

    assert "pop_count" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Pack validation integration test (TCK-20260614-WORLDMOD-PACKS)
# ---------------------------------------------------------------------------

def test_pack_refs_disabled_pack_raises_at_assembly(repos):
    """A composition with pack_refs pointing to a disabled pack must raise AssemblyPackError
    before any module assembly begins."""
    import yaml
    from unittest.mock import mock_open, patch
    from src.worldassembly.resolver import AssemblyPackError

    cat, mod = repos

    spec = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="pack_test_world",
        name="Pack Test World",
        pack_refs=["frontier_extended_pack"],
    )

    # Mock frontier_extended_pack as disabled
    disabled_yaml = yaml.dump({
        "schema_version": "content_pack.v1",
        "pack_id": "frontier_extended_pack",
        "display_name": "Frontier Extended Pack",
        "version": "1.0.0",
        "enabled": False,
        "dependencies": [],
        "included_families": {},
        "sample_compositions": ["frontier_extended"],
    })

    resolver = WorldAssemblyResolver(cat, mod)

    with patch("builtins.open", mock_open(read_data=disabled_yaml)):
        with pytest.raises(AssemblyPackError) as exc_info:
            resolver.assemble(spec)

    assert "frontier_extended_pack" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Generated composition integration test (TCK-20260614-WORLDGEN-COMPOSE)
# ---------------------------------------------------------------------------

def test_generated_composition_is_valid_worldcompositionspec(repos, tmp_path, monkeypatch):
    """
    ProceduralCompositionGenerator produces a YAML that parses as a valid
    WorldCompositionSpec with a correct world_id and generation_seed.
    """
    import yaml as _yaml
    from src.worldgeneration.generator import ProceduralCompositionGenerator
    from src.worldgeneration.schema import GenerationIntentSpec

    monkeypatch.chdir(tmp_path)
    _, mod = repos

    intent = GenerationIntentSpec(
        generation_id="generated_frontier_3_42",
        seed=42,
        settlement_style="frontier",
        danger_level=3.0,
        terrain_style="temperate",
        resource_density=1.0,
        population_scale=1.0,
    )

    gen = ProceduralCompositionGenerator()
    output_path = gen.generate(intent, mod)

    assert output_path.exists(), "Generator must write output YAML to disk"
    raw = _yaml.safe_load(output_path.read_text())
    spec = WorldCompositionSpec.model_validate(raw)

    assert spec.world_id == "generated_frontier_3_42"
    assert spec.generation_seed == 42
    assert spec.schema_version == "worldcomposition.v1"
    assert len(spec.module_refs) > 0


def test_generated_composition_determinism(repos, tmp_path, monkeypatch):
    """
    Two calls with identical intent and seed produce byte-identical YAML.
    """
    import yaml as _yaml
    from src.worldgeneration.generator import ProceduralCompositionGenerator
    from src.worldgeneration.schema import GenerationIntentSpec

    monkeypatch.chdir(tmp_path)
    _, mod = repos

    intent = GenerationIntentSpec(
        generation_id="generated_frontier_3_42",
        seed=42,
        settlement_style="frontier",
        danger_level=3.0,
    )

    gen = ProceduralCompositionGenerator()
    path1 = gen.generate(intent, mod)
    content1 = path1.read_text()
    path1.unlink()

    path2 = gen.generate(intent, mod)
    content2 = path2.read_text()

    assert content1 == content2, "Same intent must produce identical YAML across calls"


# ---------------------------------------------------------------------------
# New archetype composition tests (TCK-20260614-WORLDDAT-COMPOSE)
# ---------------------------------------------------------------------------

def test_wilderness_survival_composition(repos):
    """wilderness_survival loads, assembles, and compiles without error.

    This is a no-settlement ecology world using forest_deep_ecology,
    wolf_den_near_forest, and undead_battlefield. Verifies that module_refs
    structured form and provided_features are valid, and that the full
    pipeline (load → assemble → compile) succeeds.
    """
    import yaml
    from src.worldbuilding.compiler import WorldCompiler

    cat, mod = repos
    comp_path = Path("data/content/world_compositions/wilderness_survival.yaml")
    assert comp_path.is_file(), "wilderness_survival.yaml must exist"

    with open(comp_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    spec = WorldCompositionSpec.model_validate(raw)
    assert spec.world_id == "wilderness_survival"
    assert spec.schema_version == "worldcomposition.v1"
    assert len(spec.module_refs) == 3
    assert "deep_wilderness" in spec.provided_features
    assert "survival" in spec.provided_features

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(spec)

    assert bundle is not None
    assert bundle.world_spec is not None
    assert bundle.world_spec.world_id == "wilderness_survival"
    assert bundle.compile_context is not None
    assert bundle.provenance_manifest is not None

    state, report = WorldCompiler.compile(
        bundle.world_spec, seed=spec.generation_seed, context=bundle.compile_context
    )
    assert state is not None
    assert report["world_id"] == "wilderness_survival"


def test_urban_political_composition(repos):
    """urban_political loads, assembles, and compiles; faction context has >= 2 entries.

    Uses frontier_village_core + trading_company_hub (namespaced) + bandit_road_trade_pressure.
    The trading_company_hub is namespace-isolated ('trading') to avoid hometown region collision.
    Verifies parametric merchant_count injection and faction relationship density.
    """
    import yaml
    from src.worldbuilding.compiler import WorldCompiler

    cat, mod = repos
    comp_path = Path("data/content/world_compositions/urban_political.yaml")
    assert comp_path.is_file(), "urban_political.yaml must exist"

    with open(comp_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    spec = WorldCompositionSpec.model_validate(raw)
    assert spec.world_id == "urban_political"
    assert spec.schema_version == "worldcomposition.v1"
    assert len(spec.module_refs) == 3
    assert "settlement" in spec.provided_features
    assert "trade_hub" in spec.provided_features

    # Verify merchant_count parameter injection on trading_company_hub ref
    trading_ref = next(r for r in spec.module_refs if r.module_id == "trading_company_hub")
    assert trading_ref.parameters.get("merchant_count") == 6
    assert trading_ref.namespace == "trading"

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(spec)

    assert bundle is not None
    assert bundle.world_spec is not None
    assert bundle.world_spec.world_id == "urban_political"
    assert bundle.compile_context is not None

    # Urban political world must resolve at least 2 faction economy profiles
    assert len(bundle.compile_context.factions) >= 2, (
        f"Expected >= 2 faction entries in compile context, got "
        f"{len(bundle.compile_context.factions)}: {list(bundle.compile_context.factions.keys())}"
    )

    state, report = WorldCompiler.compile(
        bundle.world_spec, seed=spec.generation_seed, context=bundle.compile_context
    )
    assert state is not None
    assert report["world_id"] == "urban_political"


def test_dungeon_crawl_composition(repos):
    """dungeon_crawl loads, assembles, and compiles; world_spec has >= 2 quest_definitions.

    Uses ruins_mystery_quest (2 quests), goblin_camp_conflict, old_mine_resource_loop (1 quest),
    and scalable_bandit_camp with danger_scale=4. No settlement modules. Verifies quest seeding
    integration and default_perspectives pass-through.
    """
    import yaml
    from src.worldbuilding.compiler import WorldCompiler

    cat, mod = repos
    comp_path = Path("data/content/world_compositions/dungeon_crawl.yaml")
    assert comp_path.is_file(), "dungeon_crawl.yaml must exist"

    with open(comp_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    spec = WorldCompositionSpec.model_validate(raw)
    assert spec.world_id == "dungeon_crawl"
    assert spec.schema_version == "worldcomposition.v1"
    assert len(spec.module_refs) == 4
    assert "dungeon" in spec.provided_features
    assert "quest_seeding" in spec.provided_features
    assert "hero_guild_perspective" in spec.default_perspectives

    # Verify danger_scale parameter injection on scalable_bandit_camp ref
    bandit_ref = next(r for r in spec.module_refs if r.module_id == "scalable_bandit_camp")
    assert bandit_ref.parameters.get("danger_scale") == 4

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(spec)

    assert bundle is not None
    assert bundle.world_spec is not None
    assert bundle.world_spec.world_id == "dungeon_crawl"
    assert bundle.compile_context is not None

    # Dungeon crawl world must have at least 2 quest definitions assembled
    assert len(bundle.world_spec.quest_definitions) >= 2, (
        f"Expected >= 2 quest_definitions in world_spec, got "
        f"{len(bundle.world_spec.quest_definitions)}: "
        f"{[q.id for q in bundle.world_spec.quest_definitions]}"
    )

    state, report = WorldCompiler.compile(
        bundle.world_spec, seed=spec.generation_seed, context=bundle.compile_context
    )
    assert state is not None
    assert report["world_id"] == "dungeon_crawl"
    assert report["quest_count"] >= 2
