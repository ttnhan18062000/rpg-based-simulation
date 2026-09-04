# Compliance IDs: SOC-264
"""
Tests for ClanLifecycleService succession and dissolution
(TCK-20260903-CLAN-LIFECYCLE-SUCCESSION, idea 40/M4).
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.state import ClanState, EntityState
from src.core.updates import ClanUpdate, EntityUpdate, CombatUpdate, StateUpdate
from src.systems.social_systems.clan_lifecycle import ClanLifecycleService
from src.observability.events import ClanSuccessionEvent


def _entity(eid: int, sociability: float, alive: bool = True, active: bool = True) -> EntityState:
    from src.core.builder import V2EntityBuilder
    from src.core.enums import EntityRole, Faction

    entity = (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(0, 0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=alive, readiness=100.0)
        .lifecycle(active=active)
        .inventory(gold=0)
        .build()
    )
    new_personality = replace(entity.identity.personality, sociability=sociability)
    new_identity = replace(entity.identity, personality=new_personality)
    return replace(entity, identity=new_identity)


def _clan(**kwargs) -> ClanState:
    defaults = dict(clan_id="stormfell", leader_entity_id=10, member_entity_ids=(10, 11, 12))
    defaults.update(kwargs)
    return ClanState(**defaults)


# ---------------------------------------------------------------------------
# AC 1 — Succession, no sociability-margin gate
# ---------------------------------------------------------------------------

def test_clan_succession_promotes_highest_sociability_on_leader_death():
    clan = _clan(leader_entity_id=10)
    leader = _entity(10, sociability=0.9, alive=False)
    member1 = _entity(11, sociability=0.3)
    member2 = _entity(12, sociability=0.5)

    update, event = ClanLifecycleService.process_succession(
        clan, [leader, member1, member2], current_update=None, tick=100
    )

    assert update is not None
    assert isinstance(update, ClanUpdate)
    assert update.clan_id == "stormfell"
    assert update.leader_entity_id_set == 12

    assert event is not None
    assert isinstance(event, ClanSuccessionEvent)
    assert event.old_leader_id == 10
    assert event.new_leader_id == 12


def test_clan_succession_lowest_id_tiebreak_on_equal_sociability():
    clan = _clan(leader_entity_id=10)
    leader = _entity(10, sociability=0.9, alive=False)
    member1 = _entity(12, sociability=0.5)
    member2 = _entity(11, sociability=0.5)

    update, event = ClanLifecycleService.process_succession(
        clan, [leader, member1, member2], current_update=None, tick=100
    )

    assert update is not None
    assert update.leader_entity_id_set == 11


def test_clan_succession_no_promotion_when_leader_alive():
    clan = _clan(leader_entity_id=10)
    leader = _entity(10, sociability=0.1, alive=True, active=True)
    member = _entity(11, sociability=0.9)

    update, event = ClanLifecycleService.process_succession(
        clan, [leader, member], current_update=None, tick=100
    )

    assert update is None
    assert event is None


def test_clan_succession_same_tick_death_effective_state():
    """A leader who dies earlier in the same tick (same-tick CombatUpdate(alive_set=False))
    must trigger succession using the same-tick state, not the stale start-of-tick state."""
    clan = _clan(leader_entity_id=10)
    leader = _entity(10, sociability=0.9, alive=True)  # start-of-tick: still alive
    member = _entity(11, sociability=0.5)

    current_update = StateUpdate(
        entity_updates={
            10: EntityUpdate(entity_id=10, combat=CombatUpdate(alive_set=False)),
        }
    )

    update, event = ClanLifecycleService.process_succession(
        clan, [leader, member], current_update=current_update, tick=100
    )

    assert update is not None
    assert update.leader_entity_id_set == 11
    assert event.old_leader_id == 10
    assert event.new_leader_id == 11


def test_clan_succession_no_surviving_members_defers_to_dissolution_check():
    clan = _clan(leader_entity_id=10, member_entity_ids=(10,))
    leader = _entity(10, sociability=0.9, alive=False)

    update, event = ClanLifecycleService.process_succession(
        clan, [leader], current_update=None, tick=100
    )

    assert update is None
    assert event is None


# ---------------------------------------------------------------------------
# AC 2 — Dissolution only when member_entity_ids AND asset_ids both empty
# ---------------------------------------------------------------------------

def test_clan_dissolves_when_members_and_assets_both_empty():
    clan = _clan(member_entity_ids=(), asset_ids=())

    update = ClanLifecycleService.process_dissolution(clan, tick=200)

    assert update is not None
    assert update.clan_id == "stormfell"
    assert update.dissolved_tick_set == 200


def test_clan_does_not_dissolve_when_only_members_empty():
    clan = _clan(member_entity_ids=(), asset_ids=(1,))

    update = ClanLifecycleService.process_dissolution(clan, tick=200)

    assert update is None


def test_clan_does_not_dissolve_when_only_assets_empty():
    clan = _clan(member_entity_ids=(10,), asset_ids=())

    update = ClanLifecycleService.process_dissolution(clan, tick=200)

    assert update is None


def test_clan_does_not_dissolve_when_already_dissolved():
    clan = _clan(member_entity_ids=(), asset_ids=(), dissolved_tick=150)

    update = ClanLifecycleService.process_dissolution(clan, tick=200)

    assert update is None


# ---------------------------------------------------------------------------
# Anti-drift architecture guard
# ---------------------------------------------------------------------------

def test_clan_lifecycle_service_does_not_import_group_lifecycle():
    import ast
    import inspect

    from src.systems.social_systems import clan_lifecycle

    source = inspect.getsource(clan_lifecycle)
    tree = ast.parse(source)
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)

    assert "src.systems.social_systems.party_lifecycle" not in imported_modules
    assert "src.systems.world_systems.groups" not in imported_modules
