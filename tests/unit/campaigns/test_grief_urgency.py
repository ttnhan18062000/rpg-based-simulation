"""
E43F — GriefUrgencyModifier: detection, decay, and episode-start injection.
E43G — NemesisRelation: detection from interaction history and FORM_PARTY block.

Tickets: TCK-20260628-E43F-GRIEF-URGENCY, TCK-20260628-E43G-NEMESIS-RELATION
"""
from __future__ import annotations

import pytest
from dataclasses import replace as dc_replace

from src.domains.campaigns.state import (
    GriefUrgencyModifier, NarrativeLedgerEntry, CampaignState, NemesisRelation,
)
from src.domains.campaigns.grief_urgency import (
    GriefUrgencyImporter, ALLY_TRUST_THRESHOLD,
    NemesisRelationImporter, NEMESIS_EPISODE_COUNT, NEMESIS_INTERACTION_KINDS,
)
from src.domains.campaigns.social_memory import SocialMemoryRecord, InteractionRecord
from src.core.builder import V2EntityBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _grief_modifier(entity_id: int = 1, dead_ally_id: int = 99, urgency: float = 0.6, episode: int = 0) -> GriefUrgencyModifier:
    return GriefUrgencyModifier(
        entity_id=entity_id,
        dead_ally_id=dead_ally_id,
        episode=episode,
        urgency=urgency,
    )


def _entity(eid: int = 1):
    return V2EntityBuilder(eid).kind("worker").location(0.0, 0.0).combat(hp=80, max_hp=80).build()


def _death_entry(dead_id: int, episode: int = 0, tick: int = 100) -> NarrativeLedgerEntry:
    return NarrativeLedgerEntry(
        episode=episode,
        tick=tick,
        event_type="entity_death",
        subject_id=str(dead_id),
        payload={},
        significance=0.5,
    )


# ---------------------------------------------------------------------------
# GriefUrgencyModifier serialisation
# ---------------------------------------------------------------------------

def test_grief_modifier_round_trip():
    gum = _grief_modifier(entity_id=3, dead_ally_id=77, urgency=0.8, episode=2)
    assert GriefUrgencyModifier.from_dict(gum.to_dict()) == gum


def test_grief_modifier_from_dict_decay_default():
    d = {"entity_id": 1, "dead_ally_id": 2, "episode": 0, "urgency": 0.5}
    gum = GriefUrgencyModifier.from_dict(d)
    assert gum.decay_per_episode == 0.25


# ---------------------------------------------------------------------------
# GriefUrgencyImporter.apply — concern injection
# ---------------------------------------------------------------------------

def test_grief_importer_injects_social_threat_concern():
    entity = _entity(1)
    modifier = _grief_modifier(entity_id=1, dead_ally_id=42, urgency=0.7)
    result = GriefUrgencyImporter.apply(entity, modifier)

    concern_id = "grief_ally_42"
    assert concern_id in result.strategic.concerns
    concern = result.strategic.concerns[concern_id]
    assert concern.kind.value == "social_threat"
    assert concern.urgency == pytest.approx(0.7)


def test_grief_importer_does_not_mutate_original():
    entity = _entity(1)
    modifier = _grief_modifier(entity_id=1, dead_ally_id=55, urgency=0.5)
    _ = GriefUrgencyImporter.apply(entity, modifier)
    assert "grief_ally_55" not in entity.strategic.concerns


def test_grief_importer_overwrites_existing_concern():
    entity = _entity(1)
    mod1 = _grief_modifier(entity_id=1, dead_ally_id=9, urgency=0.6)
    mod2 = _grief_modifier(entity_id=1, dead_ally_id=9, urgency=0.35)
    e1 = GriefUrgencyImporter.apply(entity, mod1)
    e2 = GriefUrgencyImporter.apply(e1, mod2)
    assert e2.strategic.concerns["grief_ally_9"].urgency == pytest.approx(0.35)


def test_grief_concern_source_names_dead_ally():
    entity = _entity(1)
    modifier = _grief_modifier(entity_id=1, dead_ally_id=7, urgency=0.4, episode=1)
    result = GriefUrgencyImporter.apply(entity, modifier)
    concern = result.strategic.concerns["grief_ally_7"]
    assert "7" in concern.source
    assert "ep1" in concern.source


# ---------------------------------------------------------------------------
# _advance_grief_urgencies — orchestrator-level logic (tested via minimal stub)
# ---------------------------------------------------------------------------

def _make_campaign_state(grief_urgencies=None, social_memories=None, nemesis_relations=None) -> CampaignState:
    return CampaignState(
        campaign_id="test",
        episode_index=0,
        grief_urgencies=grief_urgencies or {},
        social_memories=social_memories or {},
        nemesis_relations=nemesis_relations or {},
    )


class _StubOrchestrator:
    """Minimal stub that exposes _advance_grief_urgencies without full init."""

    def __init__(self, state: CampaignState):
        self._state = state

    _advance_grief_urgencies = __import__(
        "src.domains.campaigns.orchestrator", fromlist=["CampaignOrchestrator"]
    ).CampaignOrchestrator._advance_grief_urgencies


def test_grief_detection_creates_modifier_for_ally():
    mem = SocialMemoryRecord(entity_id=1, relationship_scores={99: 0.8})
    state = _make_campaign_state(social_memories={1: mem})
    from src.domains.campaigns.orchestrator import CampaignOrchestrator

    # Use CampaignOrchestrator with the method directly via instance
    orch = object.__new__(CampaignOrchestrator)
    orch._state = state

    entries = [_death_entry(dead_id=99, episode=0)]
    orch._advance_grief_urgencies(entries, episode_index=0)

    assert 1 in state.grief_urgencies
    gum = state.grief_urgencies[1]
    assert gum.dead_ally_id == 99
    assert gum.urgency == pytest.approx(min(1.0, 0.8 * 0.8), abs=1e-5)


def test_grief_no_modifier_when_trust_below_threshold():
    mem = SocialMemoryRecord(entity_id=1, relationship_scores={99: ALLY_TRUST_THRESHOLD - 0.01})
    state = _make_campaign_state(social_memories={1: mem})
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    orch = object.__new__(CampaignOrchestrator)
    orch._state = state

    entries = [_death_entry(dead_id=99, episode=0)]
    orch._advance_grief_urgencies(entries, episode_index=0)

    assert 1 not in state.grief_urgencies


def test_grief_decay_reduces_urgency_each_episode():
    existing = {1: _grief_modifier(entity_id=1, dead_ally_id=5, urgency=0.6)}
    state = _make_campaign_state(grief_urgencies=existing)
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    orch = object.__new__(CampaignOrchestrator)
    orch._state = state

    orch._advance_grief_urgencies([], episode_index=1)

    assert 1 in state.grief_urgencies
    assert state.grief_urgencies[1].urgency == pytest.approx(0.6 - 0.25, abs=1e-5)


def test_grief_decay_removes_modifier_at_zero():
    existing = {1: _grief_modifier(entity_id=1, dead_ally_id=5, urgency=0.2)}
    state = _make_campaign_state(grief_urgencies=existing)
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    orch = object.__new__(CampaignOrchestrator)
    orch._state = state

    orch._advance_grief_urgencies([], episode_index=1)

    assert 1 not in state.grief_urgencies  # 0.2 - 0.25 = -0.05 → removed


def test_grief_non_death_entry_ignored():
    mem = SocialMemoryRecord(entity_id=1, relationship_scores={99: 0.9})
    state = _make_campaign_state(social_memories={1: mem})
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    orch = object.__new__(CampaignOrchestrator)
    orch._state = state

    non_death = NarrativeLedgerEntry(
        episode=0, tick=50, event_type="quest_completed",
        subject_id="99", payload={}, significance=0.7,
    )
    orch._advance_grief_urgencies([non_death], episode_index=0)
    assert 1 not in state.grief_urgencies


# ---------------------------------------------------------------------------
# CampaignState serialisation with grief_urgencies
# ---------------------------------------------------------------------------

def test_campaign_state_round_trip_with_grief():
    gum = _grief_modifier(entity_id=3, dead_ally_id=12, urgency=0.55, episode=1)
    state = _make_campaign_state(grief_urgencies={3: gum})
    restored = CampaignState.from_dict(state.to_dict())
    assert 3 in restored.grief_urgencies
    assert restored.grief_urgencies[3] == gum


def test_campaign_state_from_dict_missing_grief_urgencies():
    d = {"campaign_id": "x", "episode_index": 0}
    state = CampaignState.from_dict(d)
    assert state.grief_urgencies == {}


# ---------------------------------------------------------------------------
# E43G — NemesisRelation tests
# ---------------------------------------------------------------------------

def _interaction(other_id: int, kind: str, episode: int, tick: int = 100) -> InteractionRecord:
    return InteractionRecord(
        episode=episode, tick=tick, kind=kind,
        other_entity_id=other_id, faction_id=None, magnitude=0.8,
    )


def _nemesis(protagonist_id: int = 1, antagonist_id: int = 9, count: int = 2) -> NemesisRelation:
    return NemesisRelation(
        protagonist_id=protagonist_id,
        antagonist_id=antagonist_id,
        formation_episode=1,
        antagonism_count=count,
        strength=round(min(1.0, count * 0.4), 6),
    )


def test_nemesis_relation_round_trip():
    rel = _nemesis(protagonist_id=3, antagonist_id=7, count=3)
    assert NemesisRelation.from_dict(rel.to_dict()) == rel


def test_nemesis_importer_injects_social_blocker():
    entity = _entity(1)
    rel = _nemesis(protagonist_id=1, antagonist_id=9)
    result = NemesisRelationImporter.apply(entity, rel)
    blocker_id = "nemesis_9"
    assert blocker_id in result.strategic.blockers
    blocker = result.strategic.blockers[blocker_id]
    assert blocker.kind.value == "social"
    assert blocker.subject == "9"


def test_nemesis_importer_does_not_mutate_original():
    entity = _entity(1)
    rel = _nemesis(protagonist_id=1, antagonist_id=5)
    _ = NemesisRelationImporter.apply(entity, rel)
    assert "nemesis_5" not in entity.strategic.blockers


def test_nemesis_detection_creates_relation_at_two_episodes():
    mem = SocialMemoryRecord(
        entity_id=1,
        interaction_history=(
            _interaction(other_id=99, kind="betrayed", episode=0),
            _interaction(other_id=99, kind="conflict", episode=1),
        ),
    )
    state = _make_campaign_state(social_memories={1: mem})
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    orch = object.__new__(CampaignOrchestrator)
    orch._state = state

    orch._advance_nemesis_relations(episode_index=2)

    assert "1:99" in state.nemesis_relations
    rel = state.nemesis_relations["1:99"]
    assert rel.protagonist_id == 1
    assert rel.antagonist_id == 99
    assert rel.antagonism_count == 2
    assert rel.strength == pytest.approx(0.8)


def test_nemesis_not_created_at_one_episode():
    mem = SocialMemoryRecord(
        entity_id=1,
        interaction_history=(
            _interaction(other_id=99, kind="betrayed", episode=0),
        ),
    )
    state = _make_campaign_state(social_memories={1: mem})
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    orch = object.__new__(CampaignOrchestrator)
    orch._state = state

    orch._advance_nemesis_relations(episode_index=1)
    assert "1:99" not in state.nemesis_relations


def test_nemesis_not_created_for_positive_interactions():
    mem = SocialMemoryRecord(
        entity_id=1,
        interaction_history=(
            _interaction(other_id=99, kind="helped", episode=0),
            _interaction(other_id=99, kind="traded", episode=1),
        ),
    )
    state = _make_campaign_state(social_memories={1: mem})
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    orch = object.__new__(CampaignOrchestrator)
    orch._state = state

    orch._advance_nemesis_relations(episode_index=2)
    assert "1:99" not in state.nemesis_relations


def test_nemesis_strength_scales_with_count():
    mem = SocialMemoryRecord(
        entity_id=1,
        interaction_history=(
            _interaction(other_id=99, kind="betrayed", episode=0),
            _interaction(other_id=99, kind="conflict", episode=1),
            _interaction(other_id=99, kind="conflict", episode=2),
        ),
    )
    state = _make_campaign_state(social_memories={1: mem})
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    orch = object.__new__(CampaignOrchestrator)
    orch._state = state

    orch._advance_nemesis_relations(episode_index=3)
    rel = state.nemesis_relations["1:99"]
    assert rel.antagonism_count == 3
    assert rel.strength == pytest.approx(min(1.0, 3 * 0.4))


def test_campaign_state_round_trip_with_nemesis():
    rel = _nemesis(protagonist_id=2, antagonist_id=7, count=2)
    state = _make_campaign_state(nemesis_relations={"2:7": rel})
    restored = CampaignState.from_dict(state.to_dict())
    assert "2:7" in restored.nemesis_relations
    assert restored.nemesis_relations["2:7"] == rel


def test_campaign_state_from_dict_missing_nemesis():
    d = {"campaign_id": "x", "episode_index": 0}
    state = CampaignState.from_dict(d)
    assert state.nemesis_relations == {}
