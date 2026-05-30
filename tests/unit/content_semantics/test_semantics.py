# Compliance IDs: WORLD-SEM-TEST
import pytest
from src.core.enums import Faction, EntityRole
from src.content.repository import CatalogRepository
from src.content_semantics.faction import FactionSemanticsService
from src.content_semantics.role import RoleSemanticsService
from src.content_semantics.defaults import DefaultSemanticsService
from src.worldbuilding.compiler import get_role_enum, get_faction_enum


@pytest.fixture
def base_repo():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def test_faction_semantics(base_repo):
    service = FactionSemanticsService(base_repo)

    # Buckets mapping
    assert service.get_legacy_faction_bucket("villagers") == Faction.HERO_GUILD
    assert service.get_legacy_faction_bucket("monsters") == Faction.MONSTER_HORDE
    assert service.get_legacy_faction_bucket("town_council") == Faction.TOWN_COUNCIL
    assert service.get_legacy_faction_bucket("unknown") == Faction.NEUTRAL

    # Hostility mappings
    assert service.is_hostile("villagers", "monsters") is True
    assert service.is_hostile("villagers", "town_council") is False
    assert service.is_hostile("villagers", "villagers") is False

    # Alignment checks
    assert service.is_protector("villagers") is True
    assert service.is_invader("monsters") is True
    assert service.is_neutral("neutral") is True


def test_role_semantics(base_repo):
    service = RoleSemanticsService(base_repo)

    assert service.get_legacy_entity_role("hero") == EntityRole.HERO
    assert service.get_legacy_entity_role("worker") == EntityRole.WORKER
    assert service.get_legacy_entity_role("monster") == EntityRole.MONSTER
    assert service.get_legacy_entity_role("unknown") == EntityRole.CITIZEN

    assert service.is_combatant("hero") is True
    assert service.is_worker("worker") is True
    assert service.is_civilian("citizen") is True


def test_default_semantics(base_repo):
    service = DefaultSemanticsService(base_repo)

    combat_def = service.get_entity_combat_defaults()
    assert combat_def["hp"] == 100
    assert combat_def["atk"] == 10

    building_def = service.get_building_durability_defaults()
    assert building_def["hp"] == 500

    resource_def = service.get_resource_harvest_defaults()
    assert resource_def["required_ticks"] == 10

    vault_def = service.get_faction_vault_defaults()
    assert vault_def["starting_gold"] == 1000.0


def test_compiler_adapters_with_catalog(base_repo):
    # Adapter checks utilizing catalog backing
    assert get_role_enum("hero", base_repo) == EntityRole.HERO
    assert get_faction_enum("villagers", base_repo) == Faction.HERO_GUILD

    # Backward compatibility with string fallback when no catalog is supplied
    assert get_role_enum("hero") == EntityRole.HERO
    assert get_faction_enum("villagers") == Faction.HERO_GUILD
