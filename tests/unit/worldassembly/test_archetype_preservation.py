import pytest
from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldassembly.resolver import WorldAssemblyResolver, ResolverError
from src.worldassembly.schema import WorldCompositionSpec, ModuleRefSpec

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
            assert entity.race_id == "goblin", f"Expected race_id='goblin', got {entity.race_id!r}"
            assert entity.role_id == "raider", f"Expected role_id='raider', got {entity.role_id!r}"
            assert entity.faction_id == "goblin_warband", f"Expected faction_id='goblin_warband', got {entity.faction_id!r}"

            # Traits: archetype traits first, then race natural_traits not already present
            # goblin_raider: ["humanoid", "tool_user", "opportunistic"]
            # goblin race natural_traits: ["humanoid", "tool_user", "opportunistic", "social_humanoid", "small_body"]
            # merged: ["humanoid", "tool_user", "opportunistic", "social_humanoid", "small_body"]
            assert "humanoid" in entity.traits, f"Expected 'humanoid' in traits, got {entity.traits}"
            assert "tool_user" in entity.traits, f"Expected 'tool_user' in traits, got {entity.traits}"
            assert "opportunistic" in entity.traits, f"Expected 'opportunistic' in traits, got {entity.traits}"

            # Theme from archetype
            assert "goblin" in entity.themes, f"Expected 'goblin' in themes, got {entity.themes}"

            # Profile IDs preserved
            assert entity.combat_profile_id == "opportunist_raider", f"Expected combat_profile_id='opportunist_raider', got {entity.combat_profile_id!r}"
            assert entity.drive_profile_id == "opportunistic_raider", f"Expected drive_profile_id='opportunistic_raider', got {entity.drive_profile_id!r}"

            # Need and sense profiles come from the goblin race defaults
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
