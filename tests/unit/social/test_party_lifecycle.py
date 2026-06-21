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


# ===========================================================================
# TCK-20260619-E41C-REWARD-DIST — FairShareProtocol + Class Synergy
# ===========================================================================

from src.systems.social_systems.reward_distribution import (
    compute_fair_share,
    build_reward_transfer_intents,
)
from src.domains.adventure.scoring import AdventureRouteScorer
from src.domains.adventure.schema import RouteFamily, AdventureRouteOption


# ---------------------------------------------------------------------------
# AC1 — Proportional distribution by contribution
# ---------------------------------------------------------------------------

def test_fair_share_protocol_distributes_by_contribution():
    """
    AC1: 70/30 contribution split on a 100-gold reward.
    Entity 10 → 70 gold, entity 11 → 30 gold.  Sum == 100 (conservation).
    """
    group = _group(leader_id=10, member_ids={10, 11})
    shares = compute_fair_share(group, quest_reward=100, contribution_log={10: 0.7, 11: 0.3})

    assert shares[10] == 70
    assert shares[11] == 30
    assert sum(shares.values()) == 100


# ---------------------------------------------------------------------------
# AC2 — Class synergy bonus applied to combat routes
# ---------------------------------------------------------------------------

def test_class_synergy_bonus_applied_to_combat_routes():
    """
    AC2: WARRIOR + MAGE pair in group.roles → HUNT_WEAK_ENEMY score ×1.15.
    """
    from src.core.builder import V2EntityBuilder
    from src.core.enums import EntityRole, Faction

    entity = (
        V2EntityBuilder(10)
        .kind("hero")
        .location(0, 0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .inventory(gold=0)
        .build()
    )

    route = AdventureRouteOption(
        family=RouteFamily.HUNT_WEAK_ENEMY,
        score=0.0,
        confidence=0.8,
        expected_benefit=0.6,
        expected_risk=0.2,
    )

    scored_no_group = AdventureRouteScorer.score(entity, route)
    base_score = scored_no_group.score

    group_with_warrior_mage = _group(
        leader_id=10,
        member_ids={10, 11, 12},
        roles={10: "LEADER", 11: "WARRIOR", 12: "MAGE"},
    )

    scored_with_group = AdventureRouteScorer.score(entity, route, group=group_with_warrior_mage)
    synergy_score = scored_with_group.score

    assert synergy_score == pytest.approx(base_score * 1.15, rel=1e-4)


# ---------------------------------------------------------------------------
# Additional coverage: equal split fallback
# ---------------------------------------------------------------------------

def test_fair_share_equal_split_no_contributions():
    """
    Empty contribution_log → equal split.  3 members, 100 gold.
    Leader receives 34 (33+1 remainder).
    """
    group = _group(leader_id=10, member_ids={10, 11, 12})
    shares = compute_fair_share(group, quest_reward=100, contribution_log={})

    assert sum(shares.values()) == 100
    # Each gets 33; leader gets 34
    non_leader = [mid for mid in shares if mid != 10]
    for mid in non_leader:
        assert shares[mid] == 33
    assert shares[10] == 34


def test_fair_share_conservation_law():
    """Gold is conserved: sum of all shares always equals quest_reward."""
    group = _group(leader_id=10, member_ids={10, 11, 12, 13})
    for reward in [1, 7, 100, 999]:
        shares = compute_fair_share(group, quest_reward=reward, contribution_log={10: 0.5, 11: 0.3})
        assert sum(shares.values()) == reward, f"Conservation failed for reward={reward}"


def test_build_reward_intents_uses_resource_transfer():
    """
    build_reward_transfer_intents wraps each share in a ResourceTransferIntent
    with source_kind=QUEST and transfer_kind=PARTY_REWARD_SHARE.
    """
    from src.core.update_models.resources import ResourceTransferIntent

    shares = {10: 70, 11: 30}
    updates = build_reward_transfer_intents(shares, source_id="quest_abc")

    assert len(updates) == 2
    entity_map = {u.entity_id: u for u in updates}

    for mid, expected_gold in shares.items():
        assert mid in entity_map
        transfers = entity_map[mid].resource_transfers
        assert len(transfers) == 1
        intent = transfers[0]
        assert isinstance(intent, ResourceTransferIntent)
        assert intent.gold_delta == expected_gold
        assert intent.source_kind == "QUEST"
        assert intent.transfer_kind == "PARTY_REWARD_SHARE"


def test_hero_synergy_bonus_applied_to_quest_routes():
    """
    HERO entity scoring QUEST_OPPORTUNITY with group context → score ×1.10.
    """
    from src.core.builder import V2EntityBuilder
    from src.core.enums import EntityRole, Faction

    entity = (
        V2EntityBuilder(10)
        .kind("hero")
        .location(0, 0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .inventory(gold=0)
        .build()
    )

    route = AdventureRouteOption(
        family=RouteFamily.QUEST_OPPORTUNITY,
        score=0.0,
        confidence=0.7,
        expected_benefit=0.8,
        expected_risk=0.1,
    )

    scored_no_group = AdventureRouteScorer.score(entity, route)
    base_score = scored_no_group.score

    group_ctx = _group(leader_id=10, member_ids={10, 11})
    scored_with_group = AdventureRouteScorer.score(entity, route, group=group_ctx)

    assert scored_with_group.score == pytest.approx(base_score * 1.10, rel=1e-4)
