"""
Tests for combat target classification using EntityIdentityResolver.

Verifies that:
- EntityIdentityResolver selects the correct identity path
- Combat targeting uses the resolved faction_id from the identity path
- Legacy enum fallback still works
- Projection source is recorded in the task payload
"""

from __future__ import annotations

import pytest
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState
from src.content.repository import CatalogRepository
from src.content_semantics.faction import FactionSemanticsService
from src.content_semantics.relation import RelationContext
from src.entities.identity_resolver import EntityIdentityResolver, IdentityResolutionError
from src.engine.tactical import TacticalDecisionSystem


@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def _make_entity_clean(eid: int, faction_id: str, role_id: str, pos=(0.0, 0.0)):
    """Entity with clean_metadata identity: both faction_id and role_id in properties."""
    base = (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(*pos)
        .properties({"faction_id": faction_id, "role_id": role_id})
        .combat(hp=100, max_hp=100, atk=10, attack_range=1, alive=True, tactical_role="VANGUARD", readiness=100.0)
        .lifecycle(active=True)
        .build()
    )
    return base


def _make_entity_legacy(eid: int, faction: Faction, pos=(0.0, 0.0)):
    """Entity with legacy enum identity (no clean metadata properties)."""
    return (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(*pos)
        .identity(faction=faction)
        .combat(hp=100, max_hp=100, atk=10, attack_range=1, alive=True, tactical_role="VANGUARD", readiness=100.0)
        .lifecycle(active=True)
        .build()
    )


# ---------------------------------------------------------------------------
# EntityIdentityResolver unit tests (no catalog required)
# ---------------------------------------------------------------------------

def test_identity_resolver_clean_metadata():
    """faction_id + role_id in identity.properties → source == clean_metadata."""
    entity = _make_entity_clean(1, "hero_guild", "soldier")
    resolved = EntityIdentityResolver().resolve(entity)
    assert resolved.faction_id == "hero_guild"
    assert resolved.source == "clean_metadata"


def test_identity_resolver_legacy_compat_projection():
    """Legacy Faction enum only → source == compatibility_projection."""
    entity = _make_entity_legacy(1, Faction.HERO_GUILD)
    resolved = EntityIdentityResolver().resolve(entity)
    assert resolved.faction_id == "hero_guild"
    assert resolved.source == "compatibility_projection"


# ---------------------------------------------------------------------------
# Combat relation semantics (catalog required)
# ---------------------------------------------------------------------------

def test_hero_treats_goblin_warband_as_hostile(catalog):
    """hero_guild perspective classifies goblin_warband in hostile_groups → hostile."""
    service = FactionSemanticsService(catalog)
    ctx = RelationContext(distance=2.0, combat_engaged=False, intruding=False)
    assert service.is_hostile_compat("hero_guild", "goblin_warband", ctx)


def test_hero_treats_merchant_league_as_neutral(catalog):
    """hero_guild perspective classifies merchant_league in neutral_groups → not hostile."""
    service = FactionSemanticsService(catalog)
    ctx = RelationContext(distance=2.0, combat_engaged=False, intruding=False)
    assert not service.is_hostile_compat("hero_guild", "merchant_league", ctx)


def test_wild_beast_threat_requires_territory_context(catalog):
    """Wild beast treats town_council as neutral when not intruding; hostile when intruding."""
    service = FactionSemanticsService(catalog)
    non_intruding = RelationContext(distance=3.0, intruding=False, combat_engaged=False)
    intruding = RelationContext(distance=3.0, intruding=True, combat_engaged=False)
    assert not service.is_hostile_compat("wild_beast_pack", "town_council", non_intruding)
    assert service.is_hostile_compat("wild_beast_pack", "town_council", intruding)


def test_legacy_monster_horde_is_hostile_via_fallback(catalog):
    """monster_horde vs hero_guild: no perspective or relationship → legacy bucket hostility."""
    service = FactionSemanticsService(catalog)
    assert service.is_hostile("monster_horde", "hero_guild")


# ---------------------------------------------------------------------------
# Projection source in task payload (end-to-end targeting)
# ---------------------------------------------------------------------------

def test_projection_source_in_attack_payload_clean_metadata():
    """
    Entity with clean_metadata identity selects a goblin as hostile.
    Task payload must include target_identity_source == clean_metadata.
    """
    attacker = _make_entity_clean(1, "hero_guild", "soldier", (0.0, 0.0))
    enemy = _make_entity_clean(2, "goblin_warband", "raider", (1.0, 0.0))

    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: enemy})
    result = TacticalDecisionSystem.evaluate_entity_intent(state, attacker, neighbors=[enemy])

    assert result.task is not None
    assert result.task.payload_set.get("target_id") == 2
    assert result.task.payload_set.get("target_identity_source") == "clean_metadata"


def test_projection_source_in_payload_legacy_entity():
    """
    Legacy enum entity still produces a valid combat decision with target_identity_source present.
    """
    attacker = _make_entity_legacy(1, Faction.HERO_GUILD, (0.0, 0.0))
    enemy = _make_entity_legacy(2, Faction.MONSTER_HORDE, (1.0, 0.0))

    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: enemy})
    result = TacticalDecisionSystem.evaluate_entity_intent(state, attacker, neighbors=[enemy])

    assert result.task is not None
    assert result.task.payload_set.get("target_id") == 2
    assert "target_identity_source" in result.task.payload_set


def test_neutral_entity_not_targeted():
    """
    hero_guild does not target merchant_league (neutral) — no task with merchant as target_id.
    """
    attacker = _make_entity_clean(1, "hero_guild", "soldier", (0.0, 0.0))
    merchant = _make_entity_clean(2, "merchant_league", "merchant", (1.0, 0.0))

    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: merchant})
    result = TacticalDecisionSystem.evaluate_entity_intent(state, attacker, neighbors=[merchant])

    payload = result.task.payload_set if result.task else {}
    assert payload.get("target_id") != 2, "Merchant should not be classified as hostile"
