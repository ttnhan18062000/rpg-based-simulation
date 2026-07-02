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


# ===========================================================================
# TCK-20260619-E41D-DEFECTION-ESCORT — Defection Mechanics + Escort Behavior
# ===========================================================================

from src.systems.social_systems.party_lifecycle import PartyLifecycleService as _PLS
from src.observability.events import BetrayalDesertionEvent
from src.domains.adventure.schema import RouteFamily


# ---------------------------------------------------------------------------
# AC1 — Betrayal desertion fires when grievance_log length >= 3
# ---------------------------------------------------------------------------

def test_betrayal_desertion_fires_on_high_grievance():
    """
    AC1: Entity 11 in a group with 3 unresolved grievances defects.
    Returns updated_group (11 removed), BetrayalDesertionEvent, EntityUpdate.
    """
    group = _group(
        leader_id=10,
        member_ids={10, 11},
        grievance_log=("g1", "g2", "g3"),
    )
    member = _entity(11, sociability=0.5)
    tick = 50

    updated_group, event, entity_upd = _PLS.check_defection(group, member, tick)

    assert updated_group is not None, "Expected updated GroupRecord on defection"
    assert 11 not in updated_group.member_ids, "Defecting entity should be removed from members"
    assert updated_group.last_updated_tick == tick

    assert event is not None, "Expected a BetrayalDesertionEvent"
    assert isinstance(event, BetrayalDesertionEvent)
    assert event.event_type == "betrayal_desertion"
    assert event.event_category == "social"
    assert event.entity_id == 11
    assert event.group_id == group.id
    assert event.grievance_count == 3

    assert entity_upd is not None, "Expected EntityUpdate with notoriety penalty"
    assert entity_upd.entity_id == 11
    assert entity_upd.social is not None
    assert entity_upd.social.notoriety_delta == pytest.approx(2.0)


# ---------------------------------------------------------------------------
# AC2 — No defection when grievance count < threshold
# ---------------------------------------------------------------------------

def test_betrayal_desertion_no_fire_below_threshold():
    """
    AC2: 2 grievances (threshold is 3) → no defection, all returns None.
    """
    group = _group(
        leader_id=10,
        member_ids={10, 11},
        grievance_log=("g1", "g2"),
    )
    member = _entity(11, sociability=0.5)

    updated_group, event, entity_upd = _PLS.check_defection(group, member, tick=50)

    assert updated_group is None
    assert event is None
    assert entity_upd is None


# ---------------------------------------------------------------------------
# AC3 — Dissolution tick set when group drops to <= 1 member
# ---------------------------------------------------------------------------

def test_betrayal_desertion_dissolution_on_single_member():
    """
    AC3: 2-member group — one defects. Remaining group has 1 member,
    so dissolution_tick must be set.
    """
    group = _group(
        leader_id=10,
        member_ids={10, 11},
        grievance_log=("g1", "g2", "g3"),
    )
    member = _entity(11, sociability=0.5)
    tick = 75

    updated_group, _, _ = _PLS.check_defection(group, member, tick)

    assert updated_group is not None
    assert updated_group.dissolution_tick == tick, (
        "dissolution_tick must be set when only 1 member remains"
    )


# ---------------------------------------------------------------------------
# AC4 — Escort target route scores above OWN_SURVIVAL route
# ---------------------------------------------------------------------------

def test_escort_target_route_scores_above_survival():
    """
    AC4: Non-target member in group with escort_target_id set.
    PROTECT_TARGET score must exceed OWN_SURVIVAL score.
    Delta: +3.0 vs -1.0 → PROTECT_TARGET is at least 4 points higher.
    """
    from src.core.builder import V2EntityBuilder
    from src.core.enums import EntityRole, Faction

    entity = (
        V2EntityBuilder(11)
        .kind("hero")
        .location(0, 0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .inventory(gold=0)
        .build()
    )

    group_with_escort = _group(
        leader_id=10,
        member_ids={10, 11},
        escort_target_id=10,  # entity 11 is NOT the target → escort rules apply
    )

    protect_route = AdventureRouteOption(
        family=RouteFamily.PROTECT_TARGET,
        score=0.0,
        confidence=0.7,
        expected_benefit=0.5,
        expected_risk=0.1,
    )
    survival_route = AdventureRouteOption(
        family=RouteFamily.OWN_SURVIVAL,
        score=0.0,
        confidence=0.7,
        expected_benefit=0.5,
        expected_risk=0.1,
    )

    scored_protect = AdventureRouteScorer.score(entity, protect_route, group=group_with_escort)
    scored_survival = AdventureRouteScorer.score(entity, survival_route, group=group_with_escort)

    assert scored_protect.score > scored_survival.score, (
        f"PROTECT_TARGET ({scored_protect.score}) should score above "
        f"OWN_SURVIVAL ({scored_survival.score}) when escorting"
    )
    # PROTECT_TARGET gets +3.0 bonus; OWN_SURVIVAL gets -1.0 (floored to 0.0).
    # Since the base score for both routes is identical, the gap is at least 3.0
    # (the PROTECT_TARGET bonus alone), and OWN_SURVIVAL can never be negative.
    assert scored_protect.score - scored_survival.score >= 3.0


# ---------------------------------------------------------------------------
# AC5 — Escort scoring skipped for the escort target itself
# ---------------------------------------------------------------------------

def test_escort_scoring_skipped_for_escort_target_itself():
    """
    AC5: Entity IS the escort target → no escort bonus/penalty applied.
    PROTECT_TARGET and OWN_SURVIVAL scores should be equal (same route params).
    """
    from src.core.builder import V2EntityBuilder
    from src.core.enums import EntityRole, Faction

    target_entity = (
        V2EntityBuilder(10)
        .kind("hero")
        .location(0, 0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .inventory(gold=0)
        .build()
    )

    group_with_escort = _group(
        leader_id=10,
        member_ids={10, 11},
        escort_target_id=10,  # entity 10 IS the target
    )

    protect_route = AdventureRouteOption(
        family=RouteFamily.PROTECT_TARGET,
        score=0.0,
        confidence=0.7,
        expected_benefit=0.5,
        expected_risk=0.1,
    )
    survival_route = AdventureRouteOption(
        family=RouteFamily.OWN_SURVIVAL,
        score=0.0,
        confidence=0.7,
        expected_benefit=0.5,
        expected_risk=0.1,
    )

    scored_protect = AdventureRouteScorer.score(target_entity, protect_route, group=group_with_escort)
    scored_survival = AdventureRouteScorer.score(target_entity, survival_route, group=group_with_escort)

    # Same base params → same score; no escort modifier applied
    assert scored_protect.score == pytest.approx(scored_survival.score, abs=0.001), (
        "Target entity must not receive escort scoring adjustments"
    )


# ---------------------------------------------------------------------------
# AC6 — Escort scoring skipped when no escort_target_id set
# ---------------------------------------------------------------------------

def test_escort_scoring_skipped_when_no_escort_target():
    """
    AC6: Group exists but escort_target_id = None → no bonus/penalty on PROTECT_TARGET.
    """
    from src.core.builder import V2EntityBuilder
    from src.core.enums import EntityRole, Faction

    entity = (
        V2EntityBuilder(11)
        .kind("hero")
        .location(0, 0)
        .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
        .combat(hp=100, max_hp=100, alive=True, readiness=100.0)
        .inventory(gold=0)
        .build()
    )

    group_no_escort = _group(
        leader_id=10,
        member_ids={10, 11},
        escort_target_id=None,
    )

    protect_route = AdventureRouteOption(
        family=RouteFamily.PROTECT_TARGET,
        score=0.0,
        confidence=0.7,
        expected_benefit=0.5,
        expected_risk=0.1,
    )

    # Score with group (no escort) vs without group — should be the same
    scored_with_group = AdventureRouteScorer.score(entity, protect_route, group=group_no_escort)
    scored_no_group = AdventureRouteScorer.score(entity, protect_route, group=None)

    assert scored_with_group.score == pytest.approx(scored_no_group.score, abs=0.001), (
        "No escort bonus should apply when escort_target_id is None"
    )


# ---------------------------------------------------------------------------
# E41G — composition_score adjusts defection threshold (SOC-232)
# ---------------------------------------------------------------------------

def test_effective_threshold_zero_composition():
    """composition_score=0.0 → threshold stays at 3 (baseline)."""
    group = _group(last_leadership_check_tick=0)
    # GroupRecord.composition_score defaults to 0.0
    assert PartyLifecycleService.effective_defection_threshold(group) == 3


def test_effective_threshold_high_composition():
    """composition_score=1.0 → threshold rises to 5 (max bonus=2)."""
    from dataclasses import replace as dc_replace
    group = dc_replace(_group(), composition_score=1.0)
    assert PartyLifecycleService.effective_defection_threshold(group) == 5


def test_effective_threshold_half_composition():
    """composition_score=0.5 → threshold=4 (+1 grievance)."""
    from dataclasses import replace as dc_replace
    group = dc_replace(_group(), composition_score=0.5)
    assert PartyLifecycleService.effective_defection_threshold(group) == 4


def test_high_composition_prevents_defection_at_threshold_3():
    """A high-composition group (score=1.0) does NOT defect with only 3 grievances."""
    from dataclasses import replace as dc_replace
    group = dc_replace(
        _group(grievance_log=("g1", "g2", "g3"), member_ids={10, 11}),
        composition_score=1.0,
    )
    entity = _entity(11, sociability=0.5)
    result, event, update = PartyLifecycleService.check_defection(group, entity, tick=100)
    assert result is None and event is None, (
        "High-composition group should NOT defect at grievance_count=3 "
        "(effective threshold=5)"
    )


def test_low_composition_defects_at_threshold_3():
    """A zero-composition group defects when grievance_log reaches 3."""
    group = _group(grievance_log=("g1", "g2", "g3"), member_ids={10, 11})
    # composition_score defaults to 0.0
    entity = _entity(11, sociability=0.5)
    result, event, update = PartyLifecycleService.check_defection(group, entity, tick=100)
    assert result is not None and event is not None, (
        "Zero-composition group SHOULD defect at grievance_count=3 (threshold=3)"
    )
