"""Unit tests for TCK-20260807-QUEST-EVENT-PUSH-MIGRATION.

Tests the apply-layer (push-based) NarrativeShaper: quest_event (entity-project quest lifecycle,
SOC-241, scored by NarrativeScorer) derived from prior_state + update alone. Also tests the
ENABLE_PUSH_EVENT_SHAPERS_QUEST flag split (QUEST_SHAPER_REGISTRY) that run_shadow_shapers() uses
to keep this shaper's own SHADOW/ON lifecycle independent of ENABLE_PUSH_EVENT_SHAPERS_PHASE2
(which already defaults ON) -- mirrors TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY's own
established pattern for why Phase 2 needed its own flag distinct from Phase 1's.
"""
from __future__ import annotations
from unittest.mock import MagicMock

import pytest

from src.observability.config import ObservabilityMode
from src.observability.event_shapers import (
    NarrativeShaper, QUEST_SHAPER_REGISTRY, run_shadow_shapers,
)
from src.core.quests import QuestState, QuestKind, QuestStatus, RewardState
from src.core.strategic import ProjectStatus


def _quest(qid: str = "q1", status: QuestStatus = QuestStatus.ACTIVE) -> QuestState:
    return QuestState(
        id=qid, kind="quest", quest_kind=QuestKind.HUNT, quest_status=status,
        goal_value=5.0, current_value=0.0,
        reward=RewardState(xp=100, gold=50, items=[]),
        name="Test Quest", created_tick=0,
    )


def _strategic_component(projects=None):
    s = MagicMock()
    s.projects = projects or {}
    return s


def _entity(strategic=None):
    e = MagicMock()
    e.strategic = strategic or _strategic_component()
    return e


def _prior_state(entities: dict, tick: int = 100):
    s = MagicMock()
    s.tick = tick
    s.entities = entities
    s.feature_flags = {}
    return s


def _strategic_update(projects_add_or_update=None, projects_remove=None):
    s = MagicMock()
    s.projects_add_or_update = projects_add_or_update or []
    s.projects_remove = projects_remove or []
    return s


def _entity_update(strategic=None):
    u = MagicMock()
    u.strategic = strategic
    # Explicitly inert for the OTHER shapers run_shadow_shapers() also invokes (Phase 1's
    # Combat/Economy/Faction; Phase 2's Strategy/Progression/WorldDynamics/Social) — MagicMock
    # auto-attributes are truthy/non-None by default, which would otherwise make those shapers
    # try to process this as real combat/intent/identity/property data.
    u.combat = None
    u.intent_results = []
    u.identity = None
    u.property_updates = {}
    u.self_model_bundle_set = None
    u.group_id_set = None
    u.social = None
    return u


def _update(entity_updates: dict):
    u = MagicMock()
    u.entity_updates = entity_updates
    u.faction_updates = []
    u.world_events_add = []
    u.world_updates = {}
    u.building_updates = {}
    u.last_calamity_tick_set = None
    u.entities_add = []
    return u


def _types(events) -> list[str]:
    return [e.event_type for e in events]


# ── Registry / flag wiring ──────────────────────────────────────────────────

def test_quest_registry_contains_narrative_shaper():
    assert "narrative" in QUEST_SHAPER_REGISTRY
    assert any(isinstance(s, NarrativeShaper) for s in QUEST_SHAPER_REGISTRY["narrative"])


def test_run_shadow_shapers_default_includes_quest_events():
    """Post-cutover: the default (no explicit ENABLE_PUSH_EVENT_SHAPERS_QUEST override) delivers
    quest_event, matching ENABLE_PUSH_EVENT_SHAPERS/_PHASE2's own default-ON precedent."""
    quest = _quest()
    prior = _prior_state({1: _entity(_strategic_component(projects={}))})
    upd = _update({1: _entity_update(_strategic_update(projects_add_or_update=[quest]))})
    events = run_shadow_shapers(prior, upd, tick=10)
    assert "quest_event" in _types(events)


def test_run_shadow_shapers_explicit_off_excludes_quest_events():
    """Rollback path: explicitly setting the flag OFF suppresses quest_event from this shaper
    entirely (event_extractor.py's own rollback branch takes over instead)."""
    quest = _quest()
    prior = _prior_state({1: _entity(_strategic_component(projects={}))})
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_QUEST": "OFF"}
    upd = _update({1: _entity_update(_strategic_update(projects_add_or_update=[quest]))})
    events = run_shadow_shapers(prior, upd, tick=10)
    assert "quest_event" not in _types(events)


def test_run_shadow_shapers_shadow_mode_constructs_but_excludes():
    quest = _quest()
    prior = _prior_state({1: _entity(_strategic_component(projects={}))})
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_QUEST": "SHADOW"}
    upd = _update({1: _entity_update(_strategic_update(projects_add_or_update=[quest]))})
    events = run_shadow_shapers(prior, upd, tick=10)
    assert "quest_event" not in _types(events)


def test_run_shadow_shapers_on_mode_includes_quest_events():
    quest = _quest()
    prior = _prior_state({1: _entity(_strategic_component(projects={}))})
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_QUEST": "ON"}
    upd = _update({1: _entity_update(_strategic_update(projects_add_or_update=[quest]))})
    events = run_shadow_shapers(prior, upd, tick=10)
    assert "quest_event" in _types(events)


def test_quest_shaper_independent_of_phase2_flag():
    """Reusing ENABLE_PUSH_EVENT_SHAPERS_PHASE2 was deliberately avoided (see module docstring)
    -- confirm setting Phase 2 OFF does not suppress quest_event, and vice versa."""
    quest = _quest()
    prior = _prior_state({1: _entity(_strategic_component(projects={}))})
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_PHASE2": "OFF"}
    upd = _update({1: _entity_update(_strategic_update(projects_add_or_update=[quest]))})
    events = run_shadow_shapers(prior, upd, tick=10)
    assert "quest_event" in _types(events)


# ── NarrativeShaper.shape() direct tests ────────────────────────────────────

def test_quest_started_when_no_prior_quest():
    prior_ent = _entity(_strategic_component(projects={}))
    quest = _quest(qid="q1")
    upd = _entity_update(_strategic_update(projects_add_or_update=[quest]))
    events = NarrativeShaper().shape(
        MagicMock(entities={1: prior_ent}), _update({1: upd}), tick=10,
    )
    assert len(events) == 1
    ev = events[0]
    assert ev.event_type == "quest_event"
    assert ev.status == "started"
    assert ev.payload == {"status": "started"}
    assert ev.quest_id == "q1"


def test_quest_status_transition_emits_event_with_payload():
    prior_quest = _quest(qid="q1", status=QuestStatus.ACTIVE)
    curr_quest = _quest(qid="q1", status=QuestStatus.COMPLETED)
    prior_ent = _entity(_strategic_component(projects={"q1": prior_quest}))
    upd = _entity_update(_strategic_update(projects_add_or_update=[curr_quest]))
    events = NarrativeShaper().shape(
        MagicMock(entities={1: prior_ent}), _update({1: upd}), tick=10,
    )
    assert len(events) == 1
    ev = events[0]
    assert ev.status == "completed"
    assert ev.payload == {"status": "completed"}


def test_no_event_when_quest_status_unchanged():
    quest = _quest(qid="q1", status=QuestStatus.ACTIVE)
    prior_ent = _entity(_strategic_component(projects={"q1": quest}))
    upd = _entity_update(_strategic_update(projects_add_or_update=[quest]))
    events = NarrativeShaper().shape(
        MagicMock(entities={1: prior_ent}), _update({1: upd}), tick=10,
    )
    assert events == []


def test_non_quest_project_produces_no_event():
    """A non-QuestState ProjectState (e.g. an AI strategic goal like town_return) must never be
    mislabeled as a quest_event -- the same bug TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG fixed in
    event_extractor.py's own version of this logic."""
    non_quest = MagicMock()
    non_quest.id = "goal1"
    prior_ent = _entity(_strategic_component(projects={}))
    upd = _entity_update(_strategic_update(projects_add_or_update=[non_quest]))
    events = NarrativeShaper().shape(
        MagicMock(entities={1: prior_ent}), _update({1: upd}), tick=10,
    )
    assert events == []


def test_no_event_when_entity_has_no_strategic_update():
    prior_ent = _entity(_strategic_component(projects={}))
    upd = _entity_update(strategic=None)
    events = NarrativeShaper().shape(
        MagicMock(entities={1: prior_ent}), _update({1: upd}), tick=10,
    )
    assert events == []


def test_no_event_when_prior_entity_missing():
    quest = _quest(qid="q1")
    upd = _entity_update(_strategic_update(projects_add_or_update=[quest]))
    events = NarrativeShaper().shape(
        MagicMock(entities={}), _update({1: upd}), tick=10,
    )
    assert events == []


def test_project_removal_does_not_emit_a_started_event_for_a_different_quest():
    """_current_projects() reconstruction: removing one quest must not spuriously affect another
    quest already present in prior_ent.strategic.projects."""
    other_quest = _quest(qid="q_other", status=QuestStatus.ACTIVE)
    prior_ent = _entity(_strategic_component(projects={"q_removed": _quest(qid="q_removed"), "q_other": other_quest}))
    upd = _entity_update(_strategic_update(projects_remove=["q_removed"]))
    events = NarrativeShaper().shape(
        MagicMock(entities={1: prior_ent}), _update({1: upd}), tick=10,
    )
    assert events == []
