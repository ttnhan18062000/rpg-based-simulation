# Compliance IDs: SOC-228
"""
Tests for PartyLifecycleService leadership election (TCK-20260619-E41B-LEADERSHIP).

Acceptance criterion: test_leadership_election_picks_highest_sociability must pass.
"""
from __future__ import annotations

from dataclasses import replace
from typing import List

import pytest

from src.core.state import GroupRecord, EntityState
from src.systems.social_systems.party_lifecycle import PartyLifecycleService
from src.observability.events import LeadershipChangedEvent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _group(**kwargs) -> GroupRecord:
    """Minimal GroupRecord for testing."""
    defaults = dict(id=1, leader_id=10, member_ids={10, 11}, anchor=(0.0, 0.0))
    defaults.update(kwargs)
    return GroupRecord(**defaults)


def _entity(eid: int, sociability: float) -> EntityState:
    """EntityState with identity.personality.sociability set for election scoring."""
    from src.core.builder import V2EntityBuilder
    from src.core.enums import EntityRole, Faction
    entity = (
        V2EntityBuilder(eid)
        .kind("hero")
        .location(0, 0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .inventory(gold=0)
        .build()
    )
    # sociability lives at entity.identity.personality.sociability
    new_personality = replace(entity.identity.personality, sociability=sociability)
    new_identity = replace(entity.identity, personality=new_personality)
    return replace(entity, identity=new_identity)


# ---------------------------------------------------------------------------
# AC1 — Election fires when diff >= 0.2 and interval reached
# ---------------------------------------------------------------------------

def test_leadership_election_picks_highest_sociability():
    """
    AC1: Leader has sociability=0.3; member 11 has sociability=0.6.
    Diff = 0.3 >= 0.2 threshold.  New leader must be entity 11.
    """
    group = _group(
        leader_id=10,
        member_ids={10, 11},
        last_leadership_check_tick=0,
    )
    leader = _entity(10, sociability=0.3)
    member = _entity(11, sociability=0.6)

    tick = PartyLifecycleService.LEADERSHIP_CHECK_INTERVAL  # exactly at interval

    updated, event = PartyLifecycleService.check_leadership(
        group, [leader, member], tick
    )

    assert updated is not None, "Expected an updated GroupRecord"
    assert updated.leader_id == 11, "Leader should have changed to entity 11"
    assert updated.last_leadership_check_tick == tick

    assert event is not None, "Expected a LeadershipChangedEvent"
    assert isinstance(event, LeadershipChangedEvent)
    assert event.old_leader_id == 10
    assert event.new_leader_id == 11
    assert event.group_id == 1
    assert event.event_type == "leadership_changed"
    assert event.event_category == "social"


# ---------------------------------------------------------------------------
# AC2 — No election when sociability diff < 0.2
# ---------------------------------------------------------------------------

def test_leadership_no_election_when_diff_below_threshold():
    """
    AC2: Leader sociability=0.5; best member=0.65.  Diff=0.15 < 0.2.
    Leader unchanged; check tick updated; no event.
    """
    group = _group(
        leader_id=10,
        member_ids={10, 11},
        last_leadership_check_tick=0,
    )
    leader = _entity(10, sociability=0.5)
    member = _entity(11, sociability=0.65)

    tick = PartyLifecycleService.LEADERSHIP_CHECK_INTERVAL

    updated, event = PartyLifecycleService.check_leadership(
        group, [leader, member], tick
    )

    assert updated is not None
    assert updated.leader_id == 10, "Leader must remain entity 10"
    assert updated.last_leadership_check_tick == tick
    assert event is None, "No event should be emitted when diff < 0.2"


# ---------------------------------------------------------------------------
# AC3 — Interval gate: skip when not enough ticks have passed
# ---------------------------------------------------------------------------

def test_leadership_skips_before_interval():
    """
    AC3: last_leadership_check_tick=50; tick=100; interval=100.
    Diff = 50 < 100 → skip entirely.
    """
    group = _group(
        leader_id=10,
        member_ids={10, 11},
        last_leadership_check_tick=50,
    )
    leader = _entity(10, sociability=0.1)
    member = _entity(11, sociability=0.9)

    tick = 100  # 100 - 50 = 50 < LEADERSHIP_CHECK_INTERVAL (100)

    updated, event = PartyLifecycleService.check_leadership(
        group, [leader, member], tick
    )

    assert updated is None, "Should return None when interval not yet reached"
    assert event is None


# ---------------------------------------------------------------------------
# AC4 — Leader's own sociability is included in the candidate pool
# ---------------------------------------------------------------------------

def test_leadership_current_leader_is_candidate():
    """
    AC4: Leader sociability=0.9 beats member sociability=0.6.
    No leader change; check tick updated.
    """
    group = _group(
        leader_id=10,
        member_ids={10, 11},
        last_leadership_check_tick=0,
    )
    leader = _entity(10, sociability=0.9)
    member = _entity(11, sociability=0.6)

    tick = PartyLifecycleService.LEADERSHIP_CHECK_INTERVAL

    updated, event = PartyLifecycleService.check_leadership(
        group, [leader, member], tick
    )

    assert updated is not None
    assert updated.leader_id == 10, "Leader should remain entity 10 (highest sociability)"
    assert event is None


# ---------------------------------------------------------------------------
# AC5 — Members absent from entity list are skipped gracefully
# ---------------------------------------------------------------------------

def test_leadership_skips_missing_members():
    """
    AC5: member_ids includes entity 99 not in the provided members list.
    Should not raise; entity 99 silently skipped.
    """
    group = _group(
        leader_id=10,
        member_ids={10, 11, 99},  # entity 99 has no EntityState
        last_leadership_check_tick=0,
    )
    leader = _entity(10, sociability=0.3)
    member = _entity(11, sociability=0.6)
    # entity 99 intentionally omitted from members list

    tick = PartyLifecycleService.LEADERSHIP_CHECK_INTERVAL

    # Must not raise
    updated, event = PartyLifecycleService.check_leadership(
        group, [leader, member], tick
    )

    # Election should still fire based on entities 10 and 11
    assert updated is not None
    assert updated.leader_id == 11


# ---------------------------------------------------------------------------
# AC6 — LeadershipChangedEvent payload is correct
# ---------------------------------------------------------------------------

def test_leadership_event_payload():
    """
    AC6: Verify event payload contains morale_delta, old/new sociability,
    and correct event metadata.
    """
    group = _group(
        leader_id=10,
        member_ids={10, 11},
        last_leadership_check_tick=0,
    )
    leader = _entity(10, sociability=0.2)
    member = _entity(11, sociability=0.8)

    tick = PartyLifecycleService.LEADERSHIP_CHECK_INTERVAL

    _, event = PartyLifecycleService.check_leadership(
        group, [leader, member], tick
    )

    assert event is not None
    assert "morale_delta" in event.payload
    assert "old_sociability" in event.payload
    assert "new_sociability" in event.payload
    assert event.payload["old_sociability"] == pytest.approx(0.2)
    assert event.payload["new_sociability"] == pytest.approx(0.8)
    assert event.source_system == "party_lifecycle_service"
    assert event.entity_id == 11  # new leader
    assert 10 in event.related_entity_ids  # old leader
