"""
Integration test for WorldEntitySpawner.

Verifies that WorldEntitySpawner.spawn_from_context() converts CompileContext
entity profiles → EntityState objects via the archetype-native path
(ArchetypeEntityFactory) for profiles that carry an archetype_id.
"""

from __future__ import annotations

import inspect

import pytest

from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldassembly.schema import WorldCompositionSpec, ModuleRefSpec
from src.worldassembly.resolver import WorldAssemblyResolver
from src.worldassembly.entity_spawner import WorldEntitySpawner
from src.core.state import EntityState

pytestmark = pytest.mark.worldassembly


@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def module_repo():
    repo = WorldModuleRepository("data/content/world_modules")
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def bundle(catalog, module_repo):
    """
    Assemble a world using wolf_den_near_forest (requires frontier_village_core).
    wolf_pack_small is an archetype-recipe population, so CompileContext will
    have archetype_id-carrying profiles.
    """
    composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="spawner_integration_test",
        name="Spawner Integration Test",
        module_refs=[
            ModuleRefSpec(module_id="frontier_village_core", enabled=True, order=0),
            ModuleRefSpec(module_id="wolf_den_near_forest", enabled=True, order=1),
        ],
    )
    resolver = WorldAssemblyResolver(catalog, module_repo)
    return resolver.assemble(composition)


# ---------------------------------------------------------------------------
# Architecture guard
# ---------------------------------------------------------------------------

def test_world_entity_spawner_imports_archetype_factory():
    """WorldEntitySpawner must import ArchetypeEntityFactory (not bypass it)."""
    from src.worldassembly import entity_spawner as mod
    from src.entities.archetype_factory import ArchetypeEntityFactory
    source = inspect.getsource(mod)
    assert "ArchetypeEntityFactory" in source, (
        "WorldEntitySpawner must reference ArchetypeEntityFactory"
    )


def test_v2_entity_builder_only_in_legacy_guard():
    """
    V2EntityBuilder must only appear inside the legacy guard method,
    not at module level or in the archetype-native path.
    """
    from src.worldassembly import entity_spawner as mod
    source = inspect.getsource(mod)
    # The guard comment must be present
    assert "LEGACY GUARD" in source, (
        "Legacy V2EntityBuilder usage must be explicitly labelled as LEGACY GUARD"
    )
    # V2EntityBuilder must not be imported at module level
    lines = source.splitlines()
    top_level_import_lines = [
        l for l in lines
        if l.startswith("from") or l.startswith("import")
    ]
    for line in top_level_import_lines:
        assert "V2EntityBuilder" not in line, (
            f"V2EntityBuilder must not be imported at module level: {line!r}"
        )


# ---------------------------------------------------------------------------
# Functional tests
# ---------------------------------------------------------------------------

def test_spawn_from_context_produces_entity_states(bundle, catalog):
    """spawn_from_context returns exactly sum(profile.count) EntityState objects --
    TCK-20260911-REGION-DECLARED-POPULATION-SPAWNED-ENTITY-DIVERGENCE: a profile represents
    one population GROUP, not one entity, so this is no longer a 1:1 count."""
    ctx = bundle.compile_context
    assert len(ctx.entities) > 0, "CompileContext must have entity profiles"

    spawner = WorldEntitySpawner()
    entities = spawner.spawn_from_context(ctx, catalog)

    expected_total = sum(profile.count for profile in ctx.entities.values())
    assert expected_total > len(ctx.entities), (
        "Test requires at least one real population with count > 1 to exercise expansion"
    )
    assert len(entities) == expected_total, (
        f"Expected {expected_total} entities (sum of profile.count), got {len(entities)}"
    )
    for eid, state in entities.items():
        assert isinstance(state, EntityState)
        assert state.id == eid


def test_archetype_native_entities_carry_archetype_id(bundle, catalog):
    """
    Profiles with archetype_id produce EntityState objects whose identity.properties
    contain the archetype_id (set by ArchetypeEntityFactory) -- for every individual
    materialized from that profile, not just one.
    """
    ctx = bundle.compile_context
    archetype_profiles = {
        k: p for k, p in ctx.entities.items() if p.archetype_id
    }
    assert archetype_profiles, "Test requires at least one archetype-backed profile"

    spawner = WorldEntitySpawner()
    entities = spawner.spawn_from_context(ctx, catalog)

    # Group spawned entities by their tagged population_id -- the real, correct way to map
    # entities back to their source profile now that a profile can expand into many entities
    # (positional index alignment no longer holds).
    by_population: dict[str, list] = {}
    for state in entities.values():
        pop_id = (state.identity.properties or {}).get("population_id")
        by_population.setdefault(pop_id, []).append(state)

    for key, profile in archetype_profiles.items():
        members = by_population.get(key, [])
        assert len(members) == profile.count, (
            f"Population {key!r}: expected {profile.count} entities tagged population_id="
            f"{key!r}, found {len(members)}"
        )
        for state in members:
            props = state.identity.properties or {}
            assert props.get("archetype_id") == profile.archetype_id, (
                f"Entity {state.id} (profile {key!r}): expected archetype_id="
                f"{profile.archetype_id!r} in identity.properties, got {props!r}"
            )


def test_entity_ids_start_from_base(bundle, catalog):
    """Entity IDs are sequential starting from base_entity_id, one per spawned individual
    (sum of profile.count), not one per profile."""
    ctx = bundle.compile_context
    spawner = WorldEntitySpawner()

    entities = spawner.spawn_from_context(ctx, catalog, base_entity_id=10)
    ids = sorted(entities.keys())
    expected_total = sum(profile.count for profile in ctx.entities.values())
    assert ids[0] == 10
    assert ids == list(range(10, 10 + expected_total))


def test_entity_combat_stats_are_positive(bundle, catalog):
    """Spawned entities have positive hp and atk values."""
    ctx = bundle.compile_context
    spawner = WorldEntitySpawner()
    entities = spawner.spawn_from_context(ctx, catalog)

    for eid, state in entities.items():
        assert state.combat.hp > 0, f"Entity {eid} hp must be > 0"
        assert state.combat.max_hp > 0, f"Entity {eid} max_hp must be > 0"
        assert state.combat.atk > 0, f"Entity {eid} atk must be > 0"


def test_spawned_entities_have_real_nonzero_personality(bundle, catalog):
    """TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY: entities spawned through
    spawn_from_context (archetype-native path) must no longer default to all-zero
    personality."""
    ctx = bundle.compile_context
    spawner = WorldEntitySpawner()
    entities = spawner.spawn_from_context(ctx, catalog)

    non_zero_count = sum(
        1 for state in entities.values()
        if any([
            state.identity.personality.bravery > 0.0,
            state.identity.personality.greed > 0.0,
            state.identity.personality.sociability > 0.0,
            state.identity.personality.industry > 0.0,
        ])
    )
    assert non_zero_count == len(entities), (
        "Every spawned entity should have real, non-zero personality"
    )


def test_spawn_from_context_is_deterministic_given_seed(bundle, catalog):
    """Same (CompileContext, base_entity_id, seed) must produce bit-identical personality
    across repeated calls -- docs/world/assembly_contract.md's own determinism guarantee,
    now parameterized by seed."""
    ctx = bundle.compile_context
    spawner = WorldEntitySpawner()

    entities_1 = spawner.spawn_from_context(ctx, catalog, seed=7)
    entities_2 = spawner.spawn_from_context(ctx, catalog, seed=7)

    for eid in entities_1:
        assert entities_1[eid].identity.personality == entities_2[eid].identity.personality


def test_spawn_from_context_different_seeds_differ(bundle, catalog):
    """Different seeds should (with overwhelming probability) produce different personality
    draws -- confirms seed is actually threaded through, not silently ignored."""
    ctx = bundle.compile_context
    spawner = WorldEntitySpawner()

    entities_a = spawner.spawn_from_context(ctx, catalog, seed=1)
    entities_b = spawner.spawn_from_context(ctx, catalog, seed=2)

    personalities_a = [entities_a[eid].identity.personality for eid in entities_a]
    personalities_b = [entities_b[eid].identity.personality for eid in entities_b]
    assert personalities_a != personalities_b


# ---------------------------------------------------------------------------
# TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION: real per-entity placement
# ---------------------------------------------------------------------------

def test_spawn_position_used_when_profile_has_one(catalog):
    """A profile with a real spawn_position produces an EntityState at that position,
    not the shared default_position."""
    from src.worldassembly.context import CompileContext
    from src.worldassembly.models import ResolvedEntityProfile

    ctx = CompileContext()
    ctx.register_entity(
        "pop_with_position",
        ResolvedEntityProfile(
            legacy_role=0, legacy_faction=0, hp=10, max_hp=10, atk=1, def_stat=1,
            attack_range=1, readiness=1.0, spawn_position=(42.0, 17.0),
        ),
    )
    spawner = WorldEntitySpawner()
    entities = spawner.spawn_from_context(ctx, catalog, default_position=(0.0, 0.0))
    (state,) = entities.values()
    assert state.position == (42.0, 17.0)


def test_spawn_position_falls_back_to_default_when_unset(catalog):
    """A profile with spawn_position=None (the field's own default) falls back to
    default_position -- confirms backward compatibility for profiles built without a
    spawn_region (e.g. hand-constructed test profiles, or the legacy WorldSpec path)."""
    from src.worldassembly.context import CompileContext
    from src.worldassembly.models import ResolvedEntityProfile

    ctx = CompileContext()
    ctx.register_entity(
        "pop_without_position",
        ResolvedEntityProfile(
            legacy_role=0, legacy_faction=0, hp=10, max_hp=10, atk=1, def_stat=1,
            attack_range=1, readiness=1.0,
        ),
    )
    spawner = WorldEntitySpawner()
    entities = spawner.spawn_from_context(ctx, catalog, default_position=(5.0, 9.0))
    (state,) = entities.values()
    assert state.position == (5.0, 9.0)


@pytest.fixture(scope="module")
def two_populations_sharing_one_region_bundle(catalog, module_repo):
    """
    bandit_road_trade_pressure.yaml declares exactly one region (bandit_road) and two
    population refs (bandit_ambush_group, merchant_caravan) -- a real corpus case where
    both necessarily resolve to the same spawn_region (no other region is in scope for
    either population's preferred_regions to point to). This is the direct regression
    test for "collisions are the expected case, not an edge case"
    (staging_artifacts/.../investigation.md).
    """
    composition = WorldCompositionSpec(
        schema_version="worldcomposition.v1",
        world_id="spawner_deconfliction_test",
        name="Spawner De-confliction Test",
        module_refs=[
            ModuleRefSpec(module_id="frontier_village_core", enabled=True, order=0),
            ModuleRefSpec(module_id="bandit_road_trade_pressure", enabled=True, order=1),
        ],
    )
    resolver = WorldAssemblyResolver(catalog, module_repo)
    return resolver.assemble(composition)


def test_populations_sharing_one_spawn_region_get_distinct_deconflicted_positions(
    two_populations_sharing_one_region_bundle,
):
    """Real-corpus regression: two populations resolving to the same spawn_region must not
    collide on the same point."""
    ctx = two_populations_sharing_one_region_bundle.compile_context
    world_spec = two_populations_sharing_one_region_bundle.world_spec

    bandit_road = next(r for r in world_spec.regions if r.id.endswith("bandit_road"))
    min_x, min_y, max_x, max_y = bandit_road.bounds

    # Only the two populations from bandit_road_trade_pressure itself -- frontier_village_core
    # (a required dependency of this module) contributes its own populations resolving to its
    # own "hometown" region, which must be excluded from this bandit_road-specific check.
    shared_region_profiles = [
        p for k, p in ctx.entities.items()
        if k.startswith("bandit_ambush_group_") or k.startswith("merchant_caravan_")
    ]
    # Both populations from this module resolve to the same (namespaced) spawn_region.
    positions = [p.spawn_position for p in shared_region_profiles]
    assert len(positions) >= 2, "Test requires >=2 real profiles with resolved positions"
    assert len(set(positions)) == len(positions), (
        f"Expected distinct de-conflicted positions, got collisions: {positions}"
    )
    for x, y in positions:
        assert min_x <= x <= max_x and min_y <= y <= max_y, (
            f"Position ({x}, {y}) outside region bounds {bandit_road.bounds}"
        )
