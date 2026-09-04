import pytest
from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldassembly.resolver import WorldAssemblyResolver, ResolverError
from src.worldassembly.schema import WorldCompositionSpec, ModuleRefSpec

pytestmark = pytest.mark.worldassembly


@pytest.fixture(scope="module")
def repos():
    cat = CatalogRepository("data/content")
    cat.load_all()
    mod = WorldModuleRepository("data/content/world_modules")
    mod.load_all()
    return cat, mod

def test_resolved_archetype_preserves_identity_metadata(repos):
    """Verify that archetype metadata is fully preserved in the ResolvedEntityProfile inside CompileContext."""
    cat, mod = repos

    # goblin_camp region has bounds [95, 20, 125, 55] so topology must be >= 200x200.
    composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="test_archetype_meta",
        name="Archetype Meta Test",
        global_parameters={"topology_width": 200, "topology_height": 200},
        module_refs=[
            ModuleRefSpec(module_id="goblin_camp_conflict", enabled=True, order=0)
        ]
    )

    resolver = WorldAssemblyResolver(cat, mod)
    bundle = resolver.assemble(composition)

    # goblin_camp_conflict defines 'goblin_raiding_party' which includes 'goblin_raider' (x4).
    # Entities in the CompileContext should have archetype_id and identity metadata populated.
    entity_found = False
    for key, entity in bundle.compile_context.entities.items():
        if "goblin_raider" in key:
            entity_found = True
            # Core identity fields from archetype definition
            assert entity.archetype_id == "goblin_raider", f"Expected archetype_id='goblin_raider', got {entity.archetype_id!r}"
            assert entity.species_id == "goblin", f"Expected species_id='goblin', got {entity.species_id!r}"
            assert entity.role_id == "raider", f"Expected role_id='raider', got {entity.role_id!r}"
            assert entity.faction_id == "goblin_warband", f"Expected faction_id='goblin_warband', got {entity.faction_id!r}"

            # Traits: archetype traits first, then species natural_traits not already present
            # goblin_raider: ["humanoid", "tool_user", "opportunistic"]
            # goblin species natural_traits: ["humanoid", "tool_user", "opportunistic", "social_humanoid", "small_body"]
            # merged: ["humanoid", "tool_user", "opportunistic", "social_humanoid", "small_body"]
            assert "humanoid" in entity.traits, f"Expected 'humanoid' in traits, got {entity.traits}"
            assert "tool_user" in entity.traits, f"Expected 'tool_user' in traits, got {entity.traits}"
            assert "opportunistic" in entity.traits, f"Expected 'opportunistic' in traits, got {entity.traits}"

            # Theme from archetype
            assert "goblin" in entity.themes, f"Expected 'goblin' in themes, got {entity.themes}"

            # Profile IDs preserved
            assert entity.combat_profile_id == "opportunist_raider", f"Expected combat_profile_id='opportunist_raider', got {entity.combat_profile_id!r}"
            assert entity.drive_profile_id == "opportunistic_raider", f"Expected drive_profile_id='opportunistic_raider', got {entity.drive_profile_id!r}"

            # Need and sense profiles come from the goblin species defaults
            assert entity.need_profile_id == "goblin_survival", f"Expected need_profile_id='goblin_survival', got {entity.need_profile_id!r}"
            assert entity.sense_profile_id == "goblin_alert_senses", f"Expected sense_profile_id='goblin_alert_senses', got {entity.sense_profile_id!r}"

    assert entity_found, "Should have resolved at least one goblin_raider entity in the CompileContext"

def test_population_preferred_region_validation_fails_on_missing_region(repos):
    """Verify that using a population recipe with a preferred spawn region missing from the module raises a ResolverError."""
    cat, mod = repos

    from src.worldmodules.schema import WorldModuleSpec
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    from src.worldbuilding.recipe import RegionRecipeSpec

    # wolf_pack_small prefers ["wolf_den", "near_forest"]; our module only declares "goblin_camp"
    # (which is a valid catalog region), so the preferred spawn regions will not be found.
    raw_spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="bad_spawn_module",
        module_type="conflict",
        display_name="Bad Spawn Module",
        regions=[
            RegionRecipeSpec(id="goblin_camp", type="wilderness", grid_bounds=(0, 0, 10, 10), terrain="forest", hazard_level=3.0)
        ],
        populations=["wolf_pack_small"]
    )
    normalized_spec = WorldModuleAuthoringNormalizer.normalize(raw_spec)

    resolver = WorldAssemblyResolver(cat, mod)

    # wolf_pack_small prefers "wolf_den" and "near_forest"; neither is in "goblin_camp" module
    with pytest.raises(ResolverError) as exc_info:
        resolver.resolve_module_contribution(normalized_spec)
    assert "region" in str(exc_info.value)
    assert "wolf_den" in str(exc_info.value) or "near_forest" in str(exc_info.value)


# ===========================================================================
# TCK-20260607-ARCHETYPE-METADATA-EXPLICIT — explicit archetype_id field tests
# ===========================================================================

def test_archetype_id_survives_resolve_module_contribution(repos):
    """archetype_id on every PopulationSpec coming out of resolve_module_contribution is not None
    and matches a key in the catalog's entity_archetypes."""
    cat, mod = repos

    from src.worldmodules.schema import WorldModuleSpec
    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    from src.worldbuilding.recipe import RegionRecipeSpec

    raw_spec = WorldModuleSpec(
        schema_version="worldmodule.v2",
        module_id="wolf_test_module",
        module_type="population",
        display_name="Wolf Test Module",
        regions=[
            RegionRecipeSpec(id="wolf_den", type="wilderness", grid_bounds=(0, 0, 50, 50), terrain="forest", hazard_level=2.0),
            RegionRecipeSpec(id="near_forest", type="wilderness", grid_bounds=(51, 0, 100, 50), terrain="forest", hazard_level=1.0),
        ],
        populations=["wolf_pack_small"]
    )
    normalized_spec = WorldModuleAuthoringNormalizer.normalize(raw_spec)

    resolver = WorldAssemblyResolver(cat, mod)
    contribution = resolver.resolve_module_contribution(normalized_spec)

    assert len(contribution.resolved_population_specs) > 0, "Should resolve at least one population spec"
    for pop_spec in contribution.resolved_population_specs:
        assert pop_spec.archetype_id is not None, (
            f"pop_spec '{pop_spec.id}' has archetype_id=None; expected explicit value"
        )
        assert cat.get_entity_archetype(pop_spec.archetype_id) is not None, (
            f"archetype_id '{pop_spec.archetype_id}' not found in catalog"
        )


def test_archetype_id_carried_into_compile_context_without_string_inference(repos):
    """goblin_camp_conflict entities in CompileContext carry archetype_id from the explicit field,
    not from string suffix inference.

    Uses resolve_module_contribution + CompileProfileResolver directly to avoid triggering
    the global catalog validator (which has a pre-existing failure for moon_cult_ruins).
    """
    cat, mod = repos

    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer
    from src.worldassembly.resolver import CompileProfileResolver
    from src.worldbuilding.schema import WorldSpec, TopologySpec

    module_spec = mod.get_module("goblin_camp_conflict")
    normalized = WorldModuleAuthoringNormalizer.normalize(module_spec)

    resolver = WorldAssemblyResolver(cat, mod)
    contribution = resolver.resolve_module_contribution(normalized)

    # Build a minimal WorldSpec carrying only the resolved population specs
    world_spec = WorldSpec(
        schema_version="worldspec.v1",
        world_id="test_ctx",
        name="Test",
        topology=TopologySpec(width=200, height=200, coordinate_system="grid"),
        entities=list(contribution.resolved_population_specs),
    )

    profile_resolver = CompileProfileResolver(cat)
    ctx = profile_resolver.resolve(world_spec)

    goblin_raider_found = False
    for key, entity in ctx.entities.items():
        if entity.archetype_id is not None:
            assert cat.get_entity_archetype(entity.archetype_id) is not None, (
                f"entity '{key}' has archetype_id='{entity.archetype_id}' not in catalog"
            )
        if "goblin_raider" in key:
            goblin_raider_found = True
            assert entity.archetype_id == "goblin_raider", (
                f"Expected archetype_id='goblin_raider', got {entity.archetype_id!r}"
            )

    assert goblin_raider_found, "goblin_raider entity must be present in compile context"


def test_population_spec_archetype_id_is_not_inferred_from_id_string(repos):
    """Two PopulationSpec instances with the same id string but different archetype_id values
    return the explicitly-set field, not a value derived from the id string."""
    from src.worldbuilding.schema import PopulationSpec

    with_archetype = PopulationSpec(
        id="wolf_pack_small_hungry_wolf",
        count=4,
        role="predator",
        faction="wild_beasts",
        spawn_region="wolf_den",
        archetype_id="hungry_wolf",
    )
    without_archetype = PopulationSpec(
        id="wolf_pack_small_hungry_wolf",
        count=4,
        role="predator",
        faction="wild_beasts",
        spawn_region="wolf_den",
    )

    assert with_archetype.archetype_id == "hungry_wolf"
    assert without_archetype.archetype_id is None


def test_resolve_module_contribution_does_not_use_split_for_archetype_id(repos):
    """Modules whose recipe ID and archetype IDs contain underscores yield pop_specs
    whose archetype_id exists verbatim in the catalog — split truncation would corrupt it.

    Uses resolve_module_contribution directly; goblin_camp_conflict has multi-underscore
    IDs (goblin_raiding_party / goblin_raider) which the old split heuristic could truncate.
    """
    cat, mod = repos

    from src.worldmodules.normalizer import WorldModuleAuthoringNormalizer

    module_spec = mod.get_module("goblin_camp_conflict")
    normalized = WorldModuleAuthoringNormalizer.normalize(module_spec)

    resolver = WorldAssemblyResolver(cat, mod)
    contribution = resolver.resolve_module_contribution(normalized)

    # Every resolved PopulationSpec must carry an archetype_id that exists verbatim in catalog
    assert len(contribution.resolved_population_specs) > 0
    for pop_spec in contribution.resolved_population_specs:
        assert pop_spec.archetype_id is not None, (
            f"pop_spec '{pop_spec.id}' has archetype_id=None"
        )
        assert cat.get_entity_archetype(pop_spec.archetype_id) is not None, (
            f"pop_spec '{pop_spec.id}' has archetype_id='{pop_spec.archetype_id}' "
            f"not found in catalog — likely a string-split truncation regression"
        )
