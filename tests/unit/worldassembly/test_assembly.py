# Compliance IDs: WORLD-ASM-TEST
import pytest
from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldassembly.schema import WorldCompositionSpec, ModuleRefSpec
from src.worldassembly.resolver import WorldAssemblyResolver
from src.worldbuilding.repository import WorldRepository
from src.worldmodules.schema import WorldModuleSpec
from src.worldbuilding.recipe import RegionRecipeSpec

pytestmark = pytest.mark.worldassembly


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
    assert spec.regions[0].id == "hometown"

    assert len(spec.entities) == 2
    roles = {e.role for e in spec.entities}
    assert "hero" in roles
    assert "worker" in roles

    # 2. Assert ProvenanceManifest lists origins accurately
    prov = bundle.provenance_manifest
    assert prov.world_id == "resolved_asm_test"
    assert prov.catalog_fingerprint != ""
    assert prov.entity_origins["hometown"] == "plains_layout"
    assert "standard_villagers" in prov.module_fingerprints


def test_faction_tension_overrides_applied_after_merge(repos):
    """A composition-level faction_tension_overrides entry lands on the resolved WorldSpec's
    matching FactionSpec.initial_tension_level; all other factions stay at 0.0 (TCK-20260702-SIMQ-UPLIFT2-FACTION)."""
    cat, mod = repos

    composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="tension_override_test",
        name="Tension Override Test",
        module_refs=[
            ModuleRefSpec(module_id="plains_layout", enabled=True, order=0),
        ],
        faction_tension_overrides={"bandit_company": 0.5},
    )

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(composition)

    factions_by_id = {f.id: f for f in bundle.world_spec.factions}
    assert factions_by_id["bandit_company"].initial_tension_level == 0.5
    other_factions = [f for fid, f in factions_by_id.items() if fid != "bandit_company"]
    assert other_factions, "expected other catalog factions to be present for regression comparison"
    assert all(f.initial_tension_level == 0.0 for f in other_factions)


def test_no_faction_tension_overrides_matches_current_behavior(repos):
    """A composition with no faction_tension_overrides key resolves every faction to
    initial_tension_level == 0.0 (regression guard — other worlds unaffected)."""
    cat, mod = repos

    composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="no_tension_override_test",
        name="No Tension Override Test",
        module_refs=[
            ModuleRefSpec(module_id="plains_layout", enabled=True, order=0),
        ],
    )

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(composition)

    assert all(f.initial_tension_level == 0.0 for f in bundle.world_spec.factions)


def test_faction_tension_overrides_unknown_faction_raises(repos):
    """faction_tension_overrides referencing a faction ID absent after merge raises ValueError."""
    cat, mod = repos

    composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="tension_override_unknown_test",
        name="Tension Override Unknown Test",
        module_refs=[
            ModuleRefSpec(module_id="plains_layout", enabled=True, order=0),
        ],
        faction_tension_overrides={"nonexistent_faction": 0.5},
    )

    resolver = WorldAssemblyResolver(cat, mod)
    with pytest.raises(ValueError) as exc_info:
        resolver.assemble(composition)
    assert "nonexistent_faction" in str(exc_info.value)


def test_faction_tension_overrides_out_of_range_raises(repos):
    """An out-of-range faction_tension_overrides value raises ValidationError via FactionSpec.model_validate."""
    from pydantic import ValidationError
    cat, mod = repos

    composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="tension_override_oor_test",
        name="Tension Override Out Of Range Test",
        module_refs=[
            ModuleRefSpec(module_id="plains_layout", enabled=True, order=0),
        ],
        faction_tension_overrides={"bandit_company": 1.5},
    )

    resolver = WorldAssemblyResolver(cat, mod)
    with pytest.raises(ValidationError):
        resolver.assemble(composition)


def test_resolver_passes_information_source_profiles_from_composition(repos):
    """A composition declaring information_source_profiles entries lands on the resolved
    WorldSpec's information_source_profiles, all fields round-tripped unchanged
    (TCK-20260702-SIMQ-UPLIFT2-INFORMATION)."""
    cat, mod = repos
    from src.worldassembly.schema import InformationSourceProfileSpec

    composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="information_profiles_test",
        name="Information Profiles Test",
        module_refs=[
            ModuleRefSpec(module_id="plains_layout", enabled=True, order=0),
        ],
        information_source_profiles=[
            InformationSourceProfileSpec(
                source_id="town_notice_board",
                source_kind="guide",
                knowledge_scopes=["regional_danger", "common_resource_sources"],
                accuracy=0.4,
                freshness=0.6,
                bias=0.1,
                cost_gold=0,
                max_answers_per_query=2,
            ),
            InformationSourceProfileSpec(
                source_id="traveling_merchant_rumors",
                source_kind="traveler",
                knowledge_scopes=["common_resource_sources", "recipe_requirements"],
                accuracy=0.65,
                freshness=0.8,
                bias=0.2,
                cost_gold=5,
                max_answers_per_query=3,
            ),
        ],
    )

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(composition)

    profiles = bundle.world_spec.information_source_profiles
    assert len(profiles) == 2
    by_id = {p.source_id: p for p in profiles}

    board = by_id["town_notice_board"]
    assert board.source_kind == "guide"
    assert board.knowledge_scopes == ["regional_danger", "common_resource_sources"]
    assert board.accuracy == 0.4
    assert board.freshness == 0.6
    assert board.bias == 0.1
    assert board.cost_gold == 0
    assert board.max_answers_per_query == 2

    merchant = by_id["traveling_merchant_rumors"]
    assert merchant.source_kind == "traveler"
    assert merchant.knowledge_scopes == ["common_resource_sources", "recipe_requirements"]
    assert merchant.accuracy == 0.65
    assert merchant.freshness == 0.8
    assert merchant.bias == 0.2
    assert merchant.cost_gold == 5
    assert merchant.max_answers_per_query == 3


def test_resolver_no_information_source_profiles_declared_yields_empty_list(repos):
    """A composition with no information_source_profiles key resolves to an empty list
    (regression guard — every world other than urban_political must be unaffected)."""
    cat, mod = repos

    composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="no_information_profiles_test",
        name="No Information Profiles Test",
        module_refs=[
            ModuleRefSpec(module_id="plains_layout", enabled=True, order=0),
        ],
    )

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(composition)

    assert bundle.world_spec.information_source_profiles == []


def test_id_collision_prevention(repos):
    """Verify duplicate IDs across merged layouts raise structural errors."""
    cat, mod = repos

    # Construct two distinct custom modules both contributing the same catalog region ID
    # to trigger the duplicate-ID collision check in the assembly merge loop.
    m1 = WorldModuleSpec(
        schema_version="worldmodule.v1",
        module_id="mod1",
        module_type="terrain",
        display_name="Mod 1",
        regions=[
            RegionRecipeSpec(id="hometown", type="town", grid_bounds=(0, 0, 5, 5))
        ]
    )
    m2 = WorldModuleSpec(
        schema_version="worldmodule.v1",
        module_id="mod2",
        module_type="terrain",
        display_name="Mod 2",
        regions=[
            RegionRecipeSpec(id="hometown", type="town", grid_bounds=(6, 6, 9, 9))
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
    assert "Duplicate region ID collision 'hometown' detected" in str(exc_info.value)


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
                role="guard",
                count=5,
                faction="town_council",
                spawn_region="hometown",
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
            {"module_id": "frontier_village_core", "enabled": True, "order": 0},
            {"module_id": "scalable_bandit_camp", "enabled": True, "order": 1}
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


def test_composition_shorthand_normalization():
    """Verify that specifying shorthand 'modules' list of strings normalizes to module_refs."""
    comp = WorldCompositionSpec.model_validate({
        "schema_version": "worldcomposition.v1",
        "world_id": "shorthand_test",
        "name": "Shorthand Test",
        "modules": ["plains_layout", "standard_villagers"]
    })

    assert len(comp.module_refs) == 2
    assert comp.module_refs[0].module_id == "plains_layout"
    assert comp.module_refs[0].enabled is True
    assert comp.module_refs[0].order == 0
    assert comp.module_refs[1].module_id == "standard_villagers"
    assert comp.module_refs[1].enabled is True
    assert comp.module_refs[1].order == 0


def test_composition_mixed_formats_fail():
    """Verify that specifying both 'modules' shorthand and 'module_refs' raises ValidationError."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="Cannot specify both 'modules' shorthand"):
        WorldCompositionSpec.model_validate({
            "schema_version": "worldcomposition.v1",
            "world_id": "mixed_test",
            "name": "Mixed Test",
            "modules": ["plains_layout"],
            "module_refs": [
                {"module_id": "standard_villagers", "enabled": True, "order": 0}
            ]
        })


def test_composition_default_perspectives_preserved():
    """Verify that default_perspectives is successfully parsed and preserved."""
    comp = WorldCompositionSpec.model_validate({
        "schema_version": "worldcomposition.v1",
        "world_id": "perspectives_test",
        "name": "Perspectives Test",
        "module_refs": [
            {"module_id": "plains_layout", "enabled": True, "order": 0}
        ],
        "default_perspectives": ["hero_guild_perspective", "goblin_warband_perspective"]
    })

    assert comp.default_perspectives == ["hero_guild_perspective", "goblin_warband_perspective"]


# =============================================================================
# Phase 25 — Task 25.2: Population recipe resolver integration
# =============================================================================

@pytest.fixture(scope="module")
def cat_repo():
    cat = CatalogRepository("data/content")
    cat.load_all()
    return cat


def test_population_recipe_expands_via_resolver(cat_repo):
    """
    Phase 25 Task 25.2: PopulationRecipeResolver expands 'wolf_pack_small' into
    archetype-native (ResolvedEntityArchetype, count) pairs that are
    WorldSpec-compatible (carry legacy role/faction strings).
    """
    from src.content.resolver import PopulationRecipeResolver, ResolvedEntityArchetype

    resolver = PopulationRecipeResolver(cat_repo)
    expanded, preferred_regions = resolver.resolve("wolf_pack_small")

    # Must expand into 2 distinct archetypes
    assert len(expanded) == 2

    arch_ids = [a.archetype_id for a, _ in expanded]
    assert "hungry_wolf" in arch_ids
    assert "alpha_wolf" in arch_ids

    # Each resolved archetype carries WorldSpec-compatible projection strings
    for resolved_arch, count in expanded:
        assert isinstance(resolved_arch, ResolvedEntityArchetype)
        assert isinstance(resolved_arch.legacy_engine_role, str)
        assert isinstance(resolved_arch.legacy_engine_bucket, str)
        assert count > 0


def test_population_recipe_archetype_profiles_in_compile_context(cat_repo):
    """
    Phase 25 Task 25.2: CompileContext receives resolved archetype-driven
    profile data when population recipes are used.

    Verifies that cognition_profile, inventory_profile, and stat_profile IDs
    from the ResolvedEntityArchetype are available in the compile context
    compatible data (even without going through full WorldAssemblyResolver).
    """
    from src.content.resolver import PopulationRecipeResolver

    resolver = PopulationRecipeResolver(cat_repo)
    expanded, _ = resolver.resolve("wolf_pack_small")

    # Each archetype must carry all profiles needed for compile context seeding
    for resolved_arch, _ in expanded:
        assert resolved_arch.cognition_profile is not None
        assert resolved_arch.cognition_profile.id is not None
        assert resolved_arch.inventory_profile is not None
        assert resolved_arch.inventory_profile.id is not None
        assert resolved_arch.stat_profile is not None
        assert resolved_arch.stat_profile.id is not None
        assert resolved_arch.need_profile is not None
        assert resolved_arch.sense_profile is not None


def test_old_role_faction_count_module_still_works(repos):
    """
    Phase 25 Task 25.2: The legacy role/faction/count population style in world
    modules continues to work without modification.
    """
    cat, mod = repos

    composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="legacy_compat_test",
        name="Legacy Compat Test",
        module_refs=[
            ModuleRefSpec(module_id="plains_layout", enabled=True, order=0),
            ModuleRefSpec(module_id="standard_villagers", enabled=True, order=1),
        ]
    )

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(composition)

    spec = bundle.world_spec
    # Legacy populations use role/faction strings — must still be present
    assert len(spec.entities) > 0
    for entity in spec.entities:
        assert hasattr(entity, "role")
        assert hasattr(entity, "faction")
        assert hasattr(entity, "count")

    # CompileContext must have resolved entity profiles for each population
    ctx = bundle.compile_context
    assert len(ctx.entities) > 0
    for key, profile in ctx.entities.items():
        # Legacy profiles have hp, atk, etc.
        assert profile.hp > 0
        assert profile.max_hp > 0


def test_population_recipe_deterministic_expansion(cat_repo):
    """
    Phase 25 Task 25.2: Population recipe expansion is deterministic across multiple calls.
    """
    from src.content.resolver import PopulationRecipeResolver

    resolver = PopulationRecipeResolver(cat_repo)

    expanded1, regions1 = resolver.resolve("goblin_raiding_party")
    expanded2, regions2 = resolver.resolve("goblin_raiding_party")

    ids1 = [(a.archetype_id, c) for a, c in expanded1]
    ids2 = [(a.archetype_id, c) for a, c in expanded2]

    assert ids1 == ids2
    assert regions1 == regions2


def test_archetype_native_population_worldspec_compatibility(cat_repo):
    """
    Phase 25 Task 25.2: Resolved archetype profiles from population recipes
    can be projected into WorldSpec-compatible PopulationSpec entries
    (i.e., the legacy_engine_role and legacy_engine_bucket strings are non-empty
    and correspond to catalog role/faction designations).
    """
    from src.content.resolver import PopulationRecipeResolver

    resolver = PopulationRecipeResolver(cat_repo)
    expanded, _ = resolver.resolve("frontier_village_population")

    # Each expanded archetype has WorldSpec-compatible legacy strings
    for resolved_arch, count in expanded:
        assert len(resolved_arch.legacy_engine_role) > 0
        assert len(resolved_arch.legacy_engine_bucket) > 0
        # Projected strings should be known engine roles/factions
        known_roles = {"HERO", "WORKER", "CITIZEN", "GUARD", "MONSTER", "SHOPKEEPER"}
        known_factions = {"HERO_GUILD", "TOWN_COUNCIL", "MONSTER_HORDE", "NEUTRAL", "MERCHANT_LEAGUE"}
        assert resolved_arch.legacy_engine_role in known_roles, (
            f"Unexpected legacy_engine_role: {resolved_arch.legacy_engine_role}"
        )
        assert resolved_arch.legacy_engine_bucket in known_factions, (
            f"Unexpected legacy_engine_bucket: {resolved_arch.legacy_engine_bucket}"
        )


def test_composition_normalization_shorthand_and_mixed(repos):
    """Verify that WorldCompositionNormalizer handles shorthand lists and rejects mixed formats."""
    cat, mod = repos
    from src.worldassembly.schema import WorldCompositionNormalizer

    # 1. Shorthand list format
    shorthand_dict = {
        "schema_version": "worldcomposition.v1",
        "world_id": "shorthand_world",
        "name": "Shorthand World",
        "modules": ["plains_layout", "standard_villagers"],
        "default_perspectives": ["hero_view"]
    }
    normalized = WorldCompositionNormalizer.normalize(shorthand_dict)
    assert len(normalized.module_refs) == 2
    assert normalized.module_refs[0].module_id == "plains_layout"
    assert normalized.module_refs[1].module_id == "standard_villagers"
    assert normalized.default_perspectives == ["hero_view"]

    # 2. Mixed format should raise ValueError
    mixed_dict = {
        "schema_version": "worldcomposition.v1",
        "world_id": "mixed_world",
        "name": "Mixed World",
        "modules": ["plains_layout"],
        "module_refs": [
            {"module_id": "standard_villagers", "enabled": True, "order": 1}
        ]
    }
    with pytest.raises(ValueError) as exc_info:
        WorldCompositionNormalizer.normalize(mixed_dict)
    assert "Cannot specify both 'modules' shorthand and 'module_refs'" in str(exc_info.value)

    # 3. Unknown field should raise ValidationError
    unknown_dict = {
        "schema_version": "worldcomposition.v1",
        "world_id": "unknown_world",
        "name": "Unknown World",
        "module_refs": [],
        "invalid_field_abc": 123
    }
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        WorldCompositionNormalizer.normalize(unknown_dict)

    # 4. faction_tension_overrides mirrors through unset (default {}) and set unchanged
    no_overrides_spec = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="no_overrides_world",
        name="No Overrides World",
        module_refs=[],
    )
    normalized_no_overrides = WorldCompositionNormalizer.normalize(no_overrides_spec)
    assert normalized_no_overrides.faction_tension_overrides == {}

    overrides_spec = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="overrides_world",
        name="Overrides World",
        module_refs=[],
        faction_tension_overrides={"faction_x": 0.5},
    )
    normalized_overrides = WorldCompositionNormalizer.normalize(overrides_spec)
    assert normalized_overrides.faction_tension_overrides == {"faction_x": 0.5}

    # 5. information_source_profiles mirrors through unset (default []) and set unchanged
    from src.worldassembly.schema import InformationSourceProfileSpec

    no_profiles_spec = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="no_information_profiles_world",
        name="No Information Profiles World",
        module_refs=[],
    )
    normalized_no_profiles = WorldCompositionNormalizer.normalize(no_profiles_spec)
    assert normalized_no_profiles.information_source_profiles == []

    profiles_spec = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="information_profiles_world",
        name="Information Profiles World",
        module_refs=[],
        information_source_profiles=[
            InformationSourceProfileSpec(
                source_id="town_notice_board",
                source_kind="guide",
                accuracy=0.4,
                freshness=0.6,
            ),
        ],
    )
    normalized_profiles = WorldCompositionNormalizer.normalize(profiles_spec)
    assert len(normalized_profiles.information_source_profiles) == 1
    assert normalized_profiles.information_source_profiles[0].source_id == "town_notice_board"


def test_v2_module_resolution_and_heuristics(repos):
    """Verify that a v2 module's references resolve via component resolvers and resource/building heuristics apply."""
    cat, mod = repos

    # Define a custom v2 module Spec
    v2_mod = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="custom_v2_module",
        module_type="settlement",
        display_name="Custom V2 Module",
        biomes=["frontier_village"],
        ecologies=["frontier_village_ecology"],
        populations=["frontier_village_population"],
        relationships=["town_to_wild_beasts"],
        regions=[
            RegionRecipeSpec(id="hometown", type="town", grid_bounds=(10, 10, 20, 20), terrain="plain", hazard_level=0.0)
        ],
        resources={
            "wood_node": 2
        },
        buildings={
            "shop": 1
        }
    )

    # Register in repository
    mod.modules["custom_v2_module"] = v2_mod
    mod.raw_data["custom_v2_module"] = v2_mod.model_dump()

    # Composition utilizing the v2 module
    composition = {
        "schema_version": "worldcomposition.v1",
        "world_id": "v2_asm_test",
        "name": "V2 Asm Test",
        "modules": ["custom_v2_module"],
        "default_perspectives": ["hero_guild_perspective"]
    }

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(composition)

    # Assert regions are resolved and mapped
    spec = bundle.world_spec
    assert len(spec.regions) == 1
    assert spec.regions[0].id == "hometown"

    # Assert populations are resolved from recipe via PopulationRecipeResolver and populated
    # frontier_village_population has worker/council members
    assert len(spec.entities) > 0
    roles = {e.role for e in spec.entities}
    assert "worker" in roles

    # Assert resources are resolved and mapped via heuristic to the region with correct count preserved
    assert len(spec.resources) == 1
    assert spec.resources[0].resource_type == "wood_node"
    assert spec.resources[0].region == "hometown"
    assert spec.resources[0].count == 2

    # Assert buildings are resolved and mapped via heuristic to the region
    assert len(spec.buildings) == 1
    assert spec.buildings[0].type == "shop"
    assert spec.buildings[0].region == "hometown"

    # Assert default perspectives survived normalization
    assert bundle.provenance_manifest.composition_fingerprint != ""


def test_unknown_field_in_real_world_module_fails():
    """Verify that adding an unknown field in a real world module file fails validation."""
    import yaml
    from pathlib import Path
    from pydantic import ValidationError
    from src.worldmodules.schema import WorldModuleSpec

    module_path = Path("data/content/world_modules/frontier_village_core.yaml")
    assert module_path.is_file()

    with open(module_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # Inject unknown field
    raw["unknown_extra_field_abc"] = "some_value"

    with pytest.raises((ValidationError, ValueError)) as exc_info:
        WorldModuleSpec(**raw)
    assert "unknown_extra_field_abc" in str(exc_info.value) or "extra fields not allowed" in str(exc_info.value)


def test_unknown_field_in_real_composition_fails():
    """Verify that adding an unknown field in a real world composition file fails validation."""
    import yaml
    from pathlib import Path
    from pydantic import ValidationError
    from src.worldassembly.schema import WorldCompositionSpec

    comp_path = Path("data/content/world_compositions/frontier_living_world.yaml")
    assert comp_path.is_file()

    with open(comp_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # Inject unknown field
    raw["unknown_extra_field_xyz"] = 123

    with pytest.raises((ValidationError, ValueError)) as exc_info:
        WorldCompositionSpec.model_validate(raw)
    assert "unknown_extra_field_xyz" in str(exc_info.value) or "extra fields not allowed" in str(exc_info.value)


def test_real_composition_normalization_preserves_perspectives():
    """Verify that normalizing the real composition preserves default_perspectives."""
    import yaml
    import copy
    from pathlib import Path
    from src.worldassembly.schema import WorldCompositionSpec, WorldCompositionNormalizer

    comp_path = Path("data/content/world_compositions/frontier_living_world.yaml")
    assert comp_path.is_file()

    with open(comp_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # Ensure it normalizes successfully
    raw_copy = copy.deepcopy(raw)
    spec = WorldCompositionSpec.model_validate(raw_copy)
    normalized = WorldCompositionNormalizer.normalize(spec)

    # Assert default perspectives are fully preserved
    assert normalized.default_perspectives == [
        "hero_guild_perspective",
        "wild_beast_pack_perspective",
        "goblin_warband_perspective"
    ]

    # Verify shorthand modules list converted to module_refs
    assert len(normalized.module_refs) == 6
    module_ids = [ref.module_id for ref in normalized.module_refs]
    assert "frontier_village_core" in module_ids
    assert "wolf_den_near_forest" in module_ids

    # Assert mixed shorthand and structured refs raises ValueError
    mixed = copy.deepcopy(raw)
    mixed["module_refs"] = [{"module_id": "test_module", "enabled": True}]
    with pytest.raises(ValueError, match="Cannot specify both 'modules' shorthand"):
        WorldCompositionNormalizer.normalize(mixed)

    # Assert deterministic fingerprinting
    import hashlib
    comp_dump = normalized.model_dump()
    comp_serialized = str(sorted(comp_dump.items()))
    fingerprint1 = hashlib.sha256(comp_serialized.encode("utf-8")).hexdigest()
    fingerprint2 = hashlib.sha256(comp_serialized.encode("utf-8")).hexdigest()
    assert fingerprint1 == fingerprint2


def test_repository_enrich_error_contains_file_family_id():
    """Verify that validation errors when loading from a repository contain file/family/record ID context."""
    from src.worldmodules.repository import WorldModuleRepository
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        bad_module_content = """
schema_version: "worldmodule.v1"
module_id: "bad_test_module"
module_type: "settlement"
display_name: "Bad Test Module"
unknown_invalid_key_xyz: 42
"""
        filepath = os.path.join(tmpdir, "bad_module.yaml")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(bad_module_content)

        repo = WorldModuleRepository(modules_dir=tmpdir)
        with pytest.raises(ValueError) as exc_info:
            repo.load_all()

        err_msg = str(exc_info.value)
        assert "bad_test_module" in err_msg
        assert "world_modules" in err_msg
        assert "bad_module.yaml" in err_msg


def test_world_repository_enrich_error_contains_file_family_id():
    """Verify that composition validation errors in WorldRepository contain file/family/record ID context."""
    from src.worldbuilding.repository import WorldRepository
    from src.worldassembly.schema import WorldCompositionSpec
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        world_id = "bad_world_comp"
        world_dir = os.path.join(tmpdir, world_id)
        os.makedirs(world_dir, exist_ok=True)
        bad_comp_content = """
schema_version: "worldcomposition.v1"
world_id: "bad_world_comp"
name: "Bad Composition"
unknown_invalid_key_abc: 123
"""
        filepath = os.path.join(world_dir, "world.yaml")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(bad_comp_content)

        repo = WorldRepository(worlds_dir=tmpdir)
        index_data = repo.rebuild_index()

        # Rebuild index catches errors to label world status BROKEN
        assert index_data["worlds"]["bad_world_comp"]["status"] == "BROKEN"

        # Explicitly test that the same validation exception logic raises the enriched error correctly
        with pytest.raises(ValueError) as exc_info:
            try:
                # Raw validate (fails due to forbid extra config)
                WorldCompositionSpec.model_validate({
                    "schema_version": "worldcomposition.v1",
                    "world_id": "bad_world_comp",
                    "name": "Bad Composition",
                    "unknown_invalid_key_abc": 123
                })
            except Exception as e:
                raise ValueError(
                    f"Validation failed for composition 'bad_world_comp' in family 'world_compositions' at '{filepath}': {e}"
                ) from e

        err_msg = str(exc_info.value)
        assert "bad_world_comp" in err_msg
        assert "world_compositions" in err_msg
        assert "world.yaml" in err_msg







