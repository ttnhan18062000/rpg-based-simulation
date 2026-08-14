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
    """spawn_from_context returns at least one EntityState per CompileContext entity."""
    ctx = bundle.compile_context
    assert len(ctx.entities) > 0, "CompileContext must have entity profiles"

    spawner = WorldEntitySpawner()
    entities = spawner.spawn_from_context(ctx, catalog)

    assert len(entities) == len(ctx.entities), (
        f"Expected {len(ctx.entities)} entities, got {len(entities)}"
    )
    for eid, state in entities.items():
        assert isinstance(state, EntityState)
        assert state.id == eid


def test_archetype_native_entities_carry_archetype_id(bundle, catalog):
    """
    Profiles with archetype_id produce EntityState objects whose identity.properties
    contain the archetype_id (set by ArchetypeEntityFactory).
    """
    ctx = bundle.compile_context
    archetype_profiles = {
        k: p for k, p in ctx.entities.items() if p.archetype_id
    }
    assert archetype_profiles, "Test requires at least one archetype-backed profile"

    spawner = WorldEntitySpawner()
    entities = spawner.spawn_from_context(ctx, catalog)

    entity_ids = list(entities.keys())
    profile_keys = list(ctx.entities.keys())

    for i, (key, profile) in enumerate(ctx.entities.items()):
        if not profile.archetype_id:
            continue
        eid = entity_ids[i]
        state = entities[eid]
        props = state.identity.properties or {}
        assert props.get("archetype_id") == profile.archetype_id, (
            f"Entity {eid} (profile {key!r}): expected archetype_id="
            f"{profile.archetype_id!r} in identity.properties, got {props!r}"
        )


def test_entity_ids_start_from_base(bundle, catalog):
    """Entity IDs are sequential starting from base_entity_id."""
    ctx = bundle.compile_context
    spawner = WorldEntitySpawner()

    entities = spawner.spawn_from_context(ctx, catalog, base_entity_id=10)
    ids = sorted(entities.keys())
    assert ids[0] == 10
    assert ids == list(range(10, 10 + len(ctx.entities)))


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
