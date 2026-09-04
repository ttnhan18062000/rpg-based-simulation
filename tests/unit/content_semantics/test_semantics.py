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


def test_get_hazard_immunities(base_repo):
    service = FactionSemanticsService(base_repo)

    assert service.get_hazard_immunities("wild_beast_pack") == frozenset({"NATURAL_TERRAIN"})
    assert service.get_hazard_immunities("hero_guild") == frozenset()
    assert service.get_hazard_immunities("nonexistent_faction") == frozenset()


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


def test_relation_projection_clean(base_repo):
    from src.content_semantics.relation import RelationProjectionService, RelationContext

    service = RelationProjectionService(base_repo)

    # 1. Goblin warband projects as enemy from hero perspective.
    proj1 = service.project_relation(
        perspective_id="hero_guild_perspective",
        source_faction_id="hero_guild",
        target_faction_id="goblin_warband",
    )
    assert proj1.label == "enemy"
    assert "perspective:hero_guild_perspective" in proj1.source_records
    assert proj1.confidence == 1.0

    # 2. Wild beast pack projects as contextual threat, not enemy-by-species.
    proj2 = service.project_relation(
        perspective_id="hero_guild_perspective",
        source_faction_id="hero_guild",
        target_faction_id="wild_beast_pack",
    )
    assert proj2.label == "threat"
    assert "perspective:hero_guild_perspective" in proj2.source_records

    # Wild beast pack looking at town council
    proj3 = service.project_relation(
        perspective_id="wild_beast_pack_perspective",
        source_faction_id="wild_beast_pack",
        target_faction_id="town_council",
        context=RelationContext(intruding=True),
    )
    assert proj3.label == "intruder"

    proj4 = service.project_relation(
        perspective_id="wild_beast_pack_perspective",
        source_faction_id="wild_beast_pack",
        target_faction_id="town_council",
        context=RelationContext(intruding=False),
    )
    assert proj4.label == "neutral"

    # 3. Merchant league projects as neutral.
    proj5 = service.project_relation(
        perspective_id="hero_guild_perspective",
        source_faction_id="hero_guild",
        target_faction_id="merchant_league",
    )
    assert proj5.label == "neutral"


def test_relation_projection_fallback(base_repo):
    from src.content_semantics.relation import RelationProjectionService

    service = RelationProjectionService(base_repo)

    # Fallback to legacy is_hostile logic
    proj = service.project_relation(
        perspective_id="unknown_perspective",
        source_faction_id="villagers",
        target_faction_id="monsters",
    )
    assert proj.label == "enemy"
    assert proj.confidence == 0.5
    assert "legacy_fallback" in proj.source_records


def test_is_hostile_compat(base_repo, caplog):
    import logging
    from src.content_semantics.relation import RelationContext

    service = FactionSemanticsService(base_repo)

    # 1. Clean projection matches
    # Goblin warband is hostile to Hero Guild
    assert service.is_hostile_compat("hero_guild", "goblin_warband") is True

    # Wild beast pack is not hostile to Hero Guild by default
    assert service.is_hostile_compat("hero_guild", "wild_beast_pack") is False

    # Wild beast pack becomes hostile under combat engagement
    context_combat = RelationContext(combat_engaged=True)
    assert service.is_hostile_compat("hero_guild", "wild_beast_pack", context=context_combat) is True

    # Wild beast pack becomes hostile if within close proximity
    context_close = RelationContext(distance=3.0)
    assert service.is_hostile_compat("hero_guild", "wild_beast_pack", context=context_close) is True

    # Wild beast pack is not hostile if far away
    context_far = RelationContext(distance=10.0)
    assert service.is_hostile_compat("hero_guild", "wild_beast_pack", context=context_far) is False

    # 2. Legacy fallback works and logs in debug mode
    with caplog.at_level(logging.DEBUG):
        caplog.clear()
        # villagers has no perspective/relationship definitions
        assert service.is_hostile_compat("villagers", "monsters") is True
        # Check that it logged the fallback statement
        assert any(
            "Falling back to legacy hostility semantics" in record.message
            for record in caplog.records
        )

