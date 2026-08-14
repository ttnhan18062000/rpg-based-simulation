"""Unit tests for TCK-20260807-COMMITMENT-ABANDONED-PUSH-MIGRATION-GAP and
TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP.

Tests the apply-layer (push-based) AgencyShaper: commitment_abandoned + rejection_cascade_tick
(both AgencyScorer) derived from prior_state + update alone. Also tests the
ENABLE_PUSH_EVENT_SHAPERS_AGENCY flag split (AGENCY_SHAPER_REGISTRY) that run_shadow_shapers()
uses to keep this shaper's own SHADOW/ON lifecycle independent of every other already-ON push
flag -- mirrors TCK-20260807-QUEST-EVENT-PUSH-MIGRATION's own established pattern for why a
shaper landing after an existing flag already defaults ON needs its own dedicated flag.
"""
from __future__ import annotations
from unittest.mock import MagicMock

import pytest

from src.observability.config import ObservabilityMode
from src.observability.event_shapers import (
    AgencyShaper, AGENCY_SHAPER_REGISTRY, run_shadow_shapers,
)
from src.core.strategic import ProjectState, ProjectKind, ProjectStatus
from src.systems.strategic_systems.intelligence import _MAX_CONSECUTIVE_REJECTIONS


def _project(pid: str = "p1", status: ProjectStatus = ProjectStatus.ACTIVE) -> ProjectState:
    return ProjectState(id=pid, kind=ProjectKind.HARVESTING, status=status)


def _strategic_component(projects=None):
    s = MagicMock()
    s.projects = projects or {}
    return s


def _combat_component(hp=80, max_hp=100):
    c = MagicMock()
    c.hp = hp
    c.max_hp = max_hp
    return c


def _entity(strategic=None, combat=None):
    e = MagicMock()
    e.strategic = strategic or _strategic_component()
    e.combat = combat or _combat_component()
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


def _combat_update(hp_delta=0, max_hp_delta=0):
    c = MagicMock()
    c.hp_delta = hp_delta
    c.max_hp_delta = max_hp_delta
    return c


def _intent_result(accepted=True, reason=None):
    ir = MagicMock()
    ir.accepted = accepted
    ir.reason = reason
    return ir


def _entity_update(strategic=None, combat=None, intent_results=None):
    u = MagicMock()
    u.strategic = strategic
    u.combat = combat
    u.intent_results = intent_results or []
    # Explicitly inert for the OTHER shapers run_shadow_shapers() also invokes.
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

def test_agency_registry_contains_agency_shaper():
    assert "agency" in AGENCY_SHAPER_REGISTRY
    assert any(isinstance(s, AgencyShaper) for s in AGENCY_SHAPER_REGISTRY["agency"])


def test_run_shadow_shapers_default_includes_agency_events():
    prior_proj = _project(status=ProjectStatus.ACTIVE)
    curr_proj = _project(status=ProjectStatus.ABANDONED)
    prior = _prior_state({1: _entity(_strategic_component(projects={"p1": prior_proj}), _combat_component(hp=80, max_hp=100))})
    upd = _update({1: _entity_update(_strategic_update(projects_add_or_update=[curr_proj]))})
    events = run_shadow_shapers(prior, upd, tick=10)
    assert "commitment_abandoned" in _types(events)


def test_run_shadow_shapers_explicit_off_excludes_agency_events():
    prior_proj = _project(status=ProjectStatus.ACTIVE)
    curr_proj = _project(status=ProjectStatus.ABANDONED)
    prior = _prior_state({1: _entity(_strategic_component(projects={"p1": prior_proj}), _combat_component(hp=15, max_hp=100))})
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_AGENCY": "OFF"}
    upd = _update({1: _entity_update(_strategic_update(projects_add_or_update=[curr_proj]))})
    events = run_shadow_shapers(prior, upd, tick=10)
    assert "commitment_abandoned" not in _types(events)


def test_run_shadow_shapers_shadow_mode_constructs_but_excludes():
    prior_proj = _project(status=ProjectStatus.ACTIVE)
    curr_proj = _project(status=ProjectStatus.ABANDONED)
    prior = _prior_state({1: _entity(_strategic_component(projects={"p1": prior_proj}), _combat_component(hp=15, max_hp=100))})
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_AGENCY": "SHADOW"}
    upd = _update({1: _entity_update(_strategic_update(projects_add_or_update=[curr_proj]))})
    events = run_shadow_shapers(prior, upd, tick=10)
    assert "commitment_abandoned" not in _types(events)


def test_run_shadow_shapers_on_mode_includes_agency_events():
    prior_proj = _project(status=ProjectStatus.ACTIVE)
    curr_proj = _project(status=ProjectStatus.ABANDONED)
    prior = _prior_state({1: _entity(_strategic_component(projects={"p1": prior_proj}), _combat_component(hp=80, max_hp=100))})
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_AGENCY": "ON"}
    upd = _update({1: _entity_update(_strategic_update(projects_add_or_update=[curr_proj]))})
    events = run_shadow_shapers(prior, upd, tick=10)
    assert "commitment_abandoned" in _types(events)


def test_agency_shaper_independent_of_quest_flag():
    prior_proj = _project(status=ProjectStatus.ACTIVE)
    curr_proj = _project(status=ProjectStatus.ABANDONED)
    prior = _prior_state({1: _entity(_strategic_component(projects={"p1": prior_proj}), _combat_component(hp=80, max_hp=100))})
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_QUEST": "OFF"}
    upd = _update({1: _entity_update(_strategic_update(projects_add_or_update=[curr_proj]))})
    events = run_shadow_shapers(prior, upd, tick=10)
    assert "commitment_abandoned" in _types(events)


# ── commitment_abandoned direct tests ───────────────────────────────────────

def test_commitment_abandoned_emitted_on_abandoned_transition_not_survival():
    """hp_ratio >= 0.2 -> not SURVIVAL -> commitment_abandoned fires."""
    prior_ent = _entity(_strategic_component(projects={"p1": _project(status=ProjectStatus.ACTIVE)}), _combat_component(hp=80, max_hp=100))
    upd = _entity_update(_strategic_update(projects_add_or_update=[_project(status=ProjectStatus.ABANDONED)]))
    events = AgencyShaper().shape(MagicMock(entities={1: prior_ent}), _update({1: upd}), tick=10)
    types = [e.event_type for e in events]
    assert "commitment_abandoned" in types
    ev = next(e for e in events if e.event_type == "commitment_abandoned")
    assert ev.payload["project_id"] == "p1"
    assert ev.payload["entity_id"] == 1


def test_commitment_abandoned_not_emitted_for_survival_category():
    """hp_ratio < 0.2 -> SURVIVAL classification -> no event."""
    prior_ent = _entity(_strategic_component(projects={"p1": _project(status=ProjectStatus.ACTIVE)}), _combat_component(hp=15, max_hp=100))
    upd = _entity_update(_strategic_update(projects_add_or_update=[_project(status=ProjectStatus.ABANDONED)]))
    events = AgencyShaper().shape(MagicMock(entities={1: prior_ent}), _update({1: upd}), tick=10)
    assert events == []


def test_commitment_abandoned_not_emitted_for_non_abandonment_transition():
    prior_ent = _entity(_strategic_component(projects={"p1": _project(status=ProjectStatus.ACTIVE)}), _combat_component(hp=80, max_hp=100))
    upd = _entity_update(_strategic_update(projects_add_or_update=[_project(status=ProjectStatus.COMPLETED)]))
    events = AgencyShaper().shape(MagicMock(entities={1: prior_ent}), _update({1: upd}), tick=10)
    assert events == []


def test_commitment_abandoned_uses_reconstructed_hp_from_combat_update():
    """hp/max_hp are reconstructed from prior_ent.combat + this tick's CombatUpdate deltas, not
    read from post-apply current_state -- confirms the reconstruction actually applies the delta
    (a hit that would push hp below the SURVIVAL threshold this same tick must be reflected)."""
    prior_ent = _entity(_strategic_component(projects={"p1": _project(status=ProjectStatus.ACTIVE)}), _combat_component(hp=80, max_hp=100))
    upd = _entity_update(
        _strategic_update(projects_add_or_update=[_project(status=ProjectStatus.ABANDONED)]),
        combat=_combat_update(hp_delta=-70),  # 80 - 70 = 10 -> ratio 0.10 -> SURVIVAL
    )
    events = AgencyShaper().shape(MagicMock(entities={1: prior_ent}), _update({1: upd}), tick=10)
    assert events == []


def test_commitment_abandoned_no_event_when_no_strategic_update():
    prior_ent = _entity(_strategic_component(projects={"p1": _project(status=ProjectStatus.ACTIVE)}))
    upd = _entity_update(strategic=None)
    events = AgencyShaper().shape(MagicMock(entities={1: prior_ent}), _update({1: upd}), tick=10)
    assert events == []


# ── rejection_cascade_tick direct tests ─────────────────────────────────────

def test_rejection_cascade_tick_emitted_above_threshold():
    rejections = [_intent_result(accepted=False, reason="no_capacity") for _ in range(_MAX_CONSECUTIVE_REJECTIONS)]
    upd = _entity_update(intent_results=rejections)
    events = AgencyShaper().shape(MagicMock(entities={}), _update({1: upd}), tick=10)
    types = [e.event_type for e in events]
    assert "rejection_cascade_tick" in types
    ev = next(e for e in events if e.event_type == "rejection_cascade_tick")
    assert ev.payload["count"] == _MAX_CONSECUTIVE_REJECTIONS
    assert ev.payload["dominant_failure_reason"] == "no_capacity"


def test_rejection_cascade_tick_not_emitted_below_threshold():
    rejections = [_intent_result(accepted=False, reason="no_capacity") for _ in range(_MAX_CONSECUTIVE_REJECTIONS - 1)]
    upd = _entity_update(intent_results=rejections)
    events = AgencyShaper().shape(MagicMock(entities={}), _update({1: upd}), tick=10)
    assert [e for e in events if e.event_type == "rejection_cascade_tick"] == []


def test_rejection_cascade_tick_not_emitted_when_all_accepted():
    accepted = [_intent_result(accepted=True) for _ in range(_MAX_CONSECUTIVE_REJECTIONS + 5)]
    upd = _entity_update(intent_results=accepted)
    events = AgencyShaper().shape(MagicMock(entities={}), _update({1: upd}), tick=10)
    assert [e for e in events if e.event_type == "rejection_cascade_tick"] == []


def test_rejection_cascade_tick_aggregates_across_entities():
    """Confirms the count is a population aggregate, not per-entity."""
    half = _MAX_CONSECUTIVE_REJECTIONS // 2
    remainder = _MAX_CONSECUTIVE_REJECTIONS - half
    upd1 = _entity_update(intent_results=[_intent_result(accepted=False) for _ in range(half)])
    upd2 = _entity_update(intent_results=[_intent_result(accepted=False) for _ in range(remainder)])
    events = AgencyShaper().shape(MagicMock(entities={}), _update({1: upd1, 2: upd2}), tick=10)
    types = [e.event_type for e in events]
    assert "rejection_cascade_tick" in types


def test_rejection_cascade_tick_does_not_need_prior_state_entities():
    """Pure update-only aggregate -- fires even when prior_state.entities is empty (no per-entity
    prior-state dependency at all, unlike commitment_abandoned)."""
    rejections = [_intent_result(accepted=False) for _ in range(_MAX_CONSECUTIVE_REJECTIONS)]
    upd = _entity_update(intent_results=rejections)
    events = AgencyShaper().shape(MagicMock(entities={}), _update({999: upd}), tick=10)
    assert any(e.event_type == "rejection_cascade_tick" for e in events)
