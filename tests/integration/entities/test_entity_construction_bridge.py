"""
Integration smoke tests for the archetype-native entity construction path:
  catalog archetype → EntityArchetypeResolver → resolved_archetype_to_contract
  → ArchetypeEntityFactory → EntityState
"""

import pytest

from src.content.repository import CatalogRepository
from src.content.resolver import EntityArchetypeResolver
from src.entities.contract_builder import resolved_archetype_to_contract
from src.entities.archetype_factory import ArchetypeEntityFactory, EntitySpawnContext
from src.entities.identity_resolver import EntityIdentityResolver
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction


@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def test_archetype_native_path_produces_valid_entity_state(catalog):
    resolver = EntityArchetypeResolver(catalog)
    arch = resolver.resolve("hungry_wolf")
    contract = resolved_archetype_to_contract(arch)
    entity = ArchetypeEntityFactory().build_entity(
        1, contract, EntitySpawnContext(position=(10.0, 10.0))
    )

    assert entity.id == 1
    assert entity.combat.alive is True
    assert entity.lifecycle.active is True
    assert entity.navigation.position == (10.0, 10.0)
    assert entity.identity.properties["archetype_id"] == "hungry_wolf"
    assert entity.identity.properties["species_id"] == "wolf"


def test_archetype_native_path_combat_values_match_resolved(catalog):
    resolver = EntityArchetypeResolver(catalog)
    arch = resolver.resolve("hungry_wolf")
    contract = resolved_archetype_to_contract(arch)
    entity = ArchetypeEntityFactory().build_entity(
        2, contract, EntitySpawnContext()
    )

    assert entity.combat.hp == arch.stat_profile.hp
    assert entity.combat.max_hp == arch.stat_profile.max_hp
    assert entity.combat.atk == arch.stat_profile.atk
    assert entity.combat.def_stat == arch.stat_profile.def_stat


def test_archetype_native_path_traits_preserved(catalog):
    resolver = EntityArchetypeResolver(catalog)
    arch = resolver.resolve("hungry_wolf")
    contract = resolved_archetype_to_contract(arch)
    entity = ArchetypeEntityFactory().build_entity(
        3, contract, EntitySpawnContext()
    )

    trait_ids = {t.id for t in arch.traits}
    assert trait_ids.issubset(entity.identity.traits)


def test_archetype_identity_resolves_via_clean_metadata(catalog):
    resolver = EntityArchetypeResolver(catalog)
    arch = resolver.resolve("hungry_wolf")
    contract = resolved_archetype_to_contract(arch)
    entity = ArchetypeEntityFactory().build_entity(
        4, contract, EntitySpawnContext()
    )

    identity = EntityIdentityResolver().resolve(entity)
    assert identity.source == "clean_metadata"
    assert identity.faction_id == arch.faction_id
    assert identity.role_id == arch.role_id


def test_entity_is_one_tick_ready(catalog):
    """Entity built via archetype-native path satisfies one-tick prerequisites."""
    resolver = EntityArchetypeResolver(catalog)
    arch = resolver.resolve("hungry_wolf")
    contract = resolved_archetype_to_contract(arch)
    entity = ArchetypeEntityFactory().build_entity(
        5, contract, EntitySpawnContext(position=(5.0, 5.0))
    )

    # One-tick prerequisites: alive, active, valid position, non-zero ATK
    assert entity.combat.alive is True
    assert entity.lifecycle.active is True
    assert entity.navigation.position == (5.0, 5.0)
    assert entity.combat.atk > 0
    assert entity.combat.hp > 0


def test_legacy_v2entitybuilder_path_still_works():
    """Regression guard: legacy construction path remains valid."""
    entity = (
        V2EntityBuilder(99)
        .kind("hero")
        .combat(hp=100, alive=True)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .location(0.0, 0.0)
        .build()
    )
    assert entity.combat.hp == 100
    assert entity.identity.role == EntityRole.HERO


def test_construction_is_deterministic(catalog):
    """Same archetype + same spawn context must produce identical canonical dict."""
    resolver = EntityArchetypeResolver(catalog)
    arch = resolver.resolve("hungry_wolf")
    contract = resolved_archetype_to_contract(arch)
    spawn = EntitySpawnContext(position=(3.0, 3.0))
    factory = ArchetypeEntityFactory()

    entity_a = factory.build_entity(10, contract, spawn)
    entity_b = factory.build_entity(10, contract, spawn)

    assert entity_a.to_canonical_dict() == entity_b.to_canonical_dict()
