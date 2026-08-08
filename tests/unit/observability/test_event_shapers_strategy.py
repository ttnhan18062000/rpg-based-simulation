"""Unit tests for TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY.

Tests the apply-layer (push-based) StrategyShaper: AGENCY/COGNITION/INFORMATION (+ colocated
SOCIAL cooperation_event) events derived from prior_state + update alone. Also tests the
ENABLE_PUSH_EVENT_SHAPERS_PHASE2 flag split (SHAPER_REGISTRY vs PHASE2_SHAPER_REGISTRY) that
run_shadow_shapers() uses to keep Phase 2 shapers genuinely SHADOW-only even though
ENABLE_PUSH_EVENT_SHAPERS already defaults ON from Phase 1's cutover — see
stored_artifacts/TCK-20260806-PUSH-SHAPER-REGISTRY-STRATEGY/investigation.md's Key finding 2.
"""
from __future__ import annotations
from unittest.mock import MagicMock

import pytest

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import _BELIEF_STALE_TICKS
from src.observability.event_shapers import (
    StrategyShaper, PHASE2_SHAPER_REGISTRY, run_shadow_shapers,
)


# ── Minimal mock builders ─────────────────────────────────────────────────────

def _strategic_component(leads=None, projects=None, concerns=None, current_project_id=None):
    s = MagicMock()
    s.leads = leads or {}
    s.projects = projects or {}
    s.concerns = concerns or {}
    s.current_project_id = current_project_id
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


def _entity_update(property_updates=None, self_model_bundle_set=None, strategic=None):
    u = MagicMock()
    u.property_updates = property_updates or {}
    u.self_model_bundle_set = self_model_bundle_set
    u.strategic = strategic
    # Explicitly inert for the OTHER shapers run_shadow_shapers() also invokes (Phase 1's
    # Combat/Economy/Faction, and — once ENABLE_PUSH_EVENT_SHAPERS_PHASE2 is set — Phase 2's
    # ProgressionShaper too) — MagicMock auto-attributes are truthy/non-None by default, which
    # would otherwise make those shapers try to process this as real combat/intent/identity data.
    u.combat = None
    u.intent_results = []
    u.identity = None
    return u


def _strategic_update(leads_add_or_update=None, leads_remove=None,
                       current_project_id_set=None,
                       projects_add_or_update=None, projects_remove=None,
                       concerns_add_or_update=None, concerns_remove=None):
    u = MagicMock()
    u.leads_add_or_update = leads_add_or_update or []
    u.leads_remove = leads_remove or ()
    u.current_project_id_set = current_project_id_set
    u.projects_add_or_update = projects_add_or_update or []
    u.projects_remove = projects_remove or ()
    u.concerns_add_or_update = concerns_add_or_update or []
    u.concerns_remove = concerns_remove or ()
    return u


def _update(entity_updates: dict | None = None):
    u = MagicMock()
    u.entity_updates = entity_updates or {}
    return u


def _lead(lid: str, certainty: str, discovered_tick: int = 0):
    l = MagicMock()
    l.id = lid
    l.certainty = certainty
    l.discovered_tick = discovered_tick
    return l


def _project(pid: str, kind: str):
    p = MagicMock()
    p.id = pid
    p.kind = kind
    return p


def _concern(cid: str, kind: str, urgency: float):
    c = MagicMock()
    c.id = cid
    c.kind = kind
    c.urgency = urgency
    return c


def _types(events) -> list[str]:
    return [e.event_type for e in events]


@pytest.fixture(autouse=True)
def _reset_shaper_state():
    StrategyShaper.reset_run_state()
    yield
    StrategyShaper.reset_run_state()


# ── Registry / flag-split mechanism ────────────────────────────────────────

def test_phase2_registry_contains_strategy_shaper():
    assert "strategy" in PHASE2_SHAPER_REGISTRY
    assert any(isinstance(s, StrategyShaper) for s in PHASE2_SHAPER_REGISTRY["strategy"])


def test_run_shadow_shapers_default_includes_phase2_events():
    """Post-TCK-20260806-PUSH-CUTOVER-PHASE2: the default (no explicit
    ENABLE_PUSH_EVENT_SHAPERS_PHASE2 override) now delivers Phase 2 events — the flag flipped
    "OFF"->"ON" at cutover, mirroring ENABLE_PUSH_EVENT_SHAPERS's own Phase 1 default flip."""
    prior = _prior_state({1: _entity()})
    upd = _update({1: _entity_update(property_updates={"last_cooperation_decision": "share"})})
    events = run_shadow_shapers(prior, upd, tick=10)
    assert "cooperation_event" in _types(events)


def test_run_shadow_shapers_explicit_off_excludes_phase2_events():
    """The rollback path: explicitly setting the flag OFF restores pre-cutover behavior (no
    Phase 2 events constructed or delivered)."""
    prior = _prior_state({1: _entity()})
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_PHASE2": "OFF"}
    upd = _update({1: _entity_update(property_updates={"last_cooperation_decision": "share"})})
    events = run_shadow_shapers(prior, upd, tick=10)
    assert "cooperation_event" not in _types(events)


def test_run_shadow_shapers_shadow_mode_constructs_but_excludes():
    prior = _prior_state({1: _entity()})
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_PHASE2": "SHADOW"}
    upd = _update({1: _entity_update(property_updates={"last_cooperation_decision": "share"})})
    events = run_shadow_shapers(prior, upd, tick=10)
    assert "cooperation_event" not in _types(events)


def test_run_shadow_shapers_on_mode_includes_phase2_events():
    prior = _prior_state({1: _entity()})
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_PHASE2": "ON"}
    upd = _update({1: _entity_update(property_updates={"last_cooperation_decision": "share"})})
    events = run_shadow_shapers(prior, upd, tick=10)
    assert "cooperation_event" in _types(events)


# ── property_updates-driven events ─────────────────────────────────────────

def test_route_selected_action_executed_family_first_use():
    prior = _prior_state({1: _entity()})
    upd = _update({1: _entity_update(property_updates={"last_routing_family": "hunt"})})
    events = StrategyShaper().shape(prior, upd, tick=10)
    types = _types(events)
    assert "route_selected" in types
    assert "action_executed" in types
    assert "route_family_first_use" in types


def test_route_family_first_use_not_repeated_same_family():
    prior = _prior_state({1: _entity()})
    upd = _update({1: _entity_update(property_updates={"last_routing_family": "hunt"})})
    StrategyShaper().shape(prior, upd, tick=10)
    events2 = StrategyShaper().shape(prior, upd, tick=11)
    assert "route_family_first_use" not in _types(events2)
    assert "route_selected" in _types(events2)


def test_route_selected_not_emitted_without_routing_family():
    prior = _prior_state({1: _entity()})
    upd = _update({1: _entity_update(property_updates={})})
    events = StrategyShaper().shape(prior, upd, tick=10)
    assert "route_selected" not in _types(events)


def test_defer_with_reason():
    prior = _prior_state({1: _entity()})
    upd = _update({1: _entity_update(property_updates={"last_defer_reason": "no_path"})})
    events = StrategyShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "defer_with_reason")
    assert ev.payload["reason"] == "no_path"


def test_self_model_updated():
    prior = _prior_state({1: _entity()})
    upd = _update({1: _entity_update(self_model_bundle_set=MagicMock())})
    events = StrategyShaper().shape(prior, upd, tick=10)
    assert "self_model_updated" in _types(events)


def test_self_model_updated_not_emitted_when_none():
    prior = _prior_state({1: _entity()})
    upd = _update({1: _entity_update(self_model_bundle_set=None)})
    events = StrategyShaper().shape(prior, upd, tick=10)
    assert "self_model_updated" not in _types(events)


def test_belief_assimilated_and_belief_updated():
    prior = _prior_state({1: _entity()}, tick=50)
    upd = _update({1: _entity_update(property_updates={
        "last_assimilated_tick": 50, "last_assimilated_subject": "bandit_road_danger",
    })})
    events = StrategyShaper().shape(prior, upd, tick=50)
    types = _types(events)
    assert "belief_assimilated" in types
    assert "belief_updated" in types


def test_belief_assimilated_not_emitted_on_different_tick():
    prior = _prior_state({1: _entity()}, tick=50)
    upd = _update({1: _entity_update(property_updates={"last_assimilated_tick": 40})})
    events = StrategyShaper().shape(prior, upd, tick=50)
    assert "belief_assimilated" not in _types(events)


def test_route_new_query():
    prior = _prior_state({1: _entity()}, tick=50)
    upd = _update({1: _entity_update(property_updates={
        "last_routed_query_tick": 50, "last_routed_query_subject": "mine_ownership",
    })})
    events = StrategyShaper().shape(prior, upd, tick=50)
    assert "route_new_query" in _types(events)


def test_cooperation_event():
    prior = _prior_state({1: _entity()})
    upd = _update({1: _entity_update(property_updates={"last_cooperation_decision": "share"})})
    events = StrategyShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "cooperation_event")
    assert ev.event_category == "social"
    assert ev.payload["decision"] == "share"


def test_cooperation_event_not_emitted_when_none():
    prior = _prior_state({1: _entity()})
    upd = _update({1: _entity_update(property_updates={"last_cooperation_decision": None})})
    events = StrategyShaper().shape(prior, upd, tick=10)
    assert "cooperation_event" not in _types(events)


# ── Reconstructed-current-view events (leads/projects/concerns) ───────────

def test_lead_certainty_changed_and_updated():
    prior_lead = _lead("l1", "VAGUE")
    new_lead = _lead("l1", "CONFIRMED")
    prior = _prior_state({1: _entity(_strategic_component(leads={"l1": prior_lead}))})
    strategic_upd = _strategic_update(leads_add_or_update=[new_lead])
    upd = _update({1: _entity_update(strategic=strategic_upd)})
    events = StrategyShaper().shape(prior, upd, tick=10)
    types = _types(events)
    assert "lead_certainty_changed" in types
    assert "lead_certainty_updated" in types
    changed = next(e for e in events if e.event_type == "lead_certainty_changed")
    assert changed.payload["lead_id"] == "l1"


def test_lead_certainty_not_changed_no_event():
    lead = _lead("l1", "VAGUE")
    prior = _prior_state({1: _entity(_strategic_component(leads={"l1": lead}))})
    strategic_upd = _strategic_update(leads_add_or_update=[_lead("l1", "VAGUE")])
    upd = _update({1: _entity_update(strategic=strategic_upd)})
    events = StrategyShaper().shape(prior, upd, tick=10)
    assert "lead_certainty_changed" not in _types(events)


def test_belief_stale_fires_for_aged_vague_lead():
    old_lead = _lead("l1", "VAGUE", discovered_tick=0)
    prior = _prior_state({1: _entity(_strategic_component(leads={"l1": old_lead}))}, tick=0)
    # Entity has SOME update this tick (e.g. an unrelated routing change) so it's visited at all —
    # matches event_extractor.py's own dirty_entity_ids precondition.
    strategic_upd = _strategic_update()
    upd = _update({1: _entity_update(property_updates={"last_defer_reason": "x"}, strategic=strategic_upd)})
    tick = _BELIEF_STALE_TICKS + 1
    events = StrategyShaper().shape(prior, upd, tick=tick)
    stale = next(e for e in events if e.event_type == "belief_stale")
    assert stale.payload["lead_id"] == "l1"


def test_belief_stale_not_repeated_for_same_lead():
    old_lead = _lead("l1", "VAGUE", discovered_tick=0)
    prior = _prior_state({1: _entity(_strategic_component(leads={"l1": old_lead}))}, tick=0)
    strategic_upd = _strategic_update()
    upd = _update({1: _entity_update(property_updates={"last_defer_reason": "x"}, strategic=strategic_upd)})
    tick = _BELIEF_STALE_TICKS + 1
    StrategyShaper().shape(prior, upd, tick=tick)
    events2 = StrategyShaper().shape(prior, upd, tick=tick + 1)
    assert "belief_stale" not in _types(events2)


def test_belief_stale_not_fired_for_fresh_lead():
    fresh_lead = _lead("l1", "VAGUE", discovered_tick=0)
    prior = _prior_state({1: _entity(_strategic_component(leads={"l1": fresh_lead}))}, tick=0)
    strategic_upd = _strategic_update()
    upd = _update({1: _entity_update(property_updates={"last_defer_reason": "x"}, strategic=strategic_upd)})
    events = StrategyShaper().shape(prior, upd, tick=5)
    assert "belief_stale" not in _types(events)


def test_decision_diverged_by_belief():
    lead = _lead("l1", "VAGUE")
    proj = _project("p1", "harvesting")
    prior = _prior_state({1: _entity(_strategic_component(
        leads={"l1": lead}, projects={"p1": proj}, current_project_id="p1",
    ))})
    strategic_upd = _strategic_update(current_project_id_set="p1")
    upd = _update({1: _entity_update(strategic=strategic_upd)})
    events = StrategyShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "decision_diverged_by_belief")
    assert ev.payload["project_kind"] == "harvesting"


def test_decision_diverged_by_belief_not_fired_for_information_project():
    lead = _lead("l1", "VAGUE")
    proj = _project("p1", "information")
    prior = _prior_state({1: _entity(_strategic_component(
        leads={"l1": lead}, projects={"p1": proj}, current_project_id="p1",
    ))})
    strategic_upd = _strategic_update(current_project_id_set="p1")
    upd = _update({1: _entity_update(strategic=strategic_upd)})
    events = StrategyShaper().shape(prior, upd, tick=10)
    assert "decision_diverged_by_belief" not in _types(events)


def test_decision_divergence_detected():
    proj = _project("p1", "harvesting")
    concern = _concern("c1", "danger", urgency=0.9)
    prior = _prior_state({1: _entity(_strategic_component(
        projects={"p1": proj}, concerns={"c1": concern}, current_project_id="p1",
    ))})
    strategic_upd = _strategic_update(current_project_id_set="p1")
    upd = _update({1: _entity_update(strategic=strategic_upd)})
    events = StrategyShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "decision_divergence_detected")
    assert ev.payload["concern_kind"] == "danger"
    assert ev.payload["project_kind"] == "harvesting"


def test_decision_divergence_not_detected_below_urgency_threshold():
    proj = _project("p1", "harvesting")
    concern = _concern("c1", "danger", urgency=0.5)
    prior = _prior_state({1: _entity(_strategic_component(
        projects={"p1": proj}, concerns={"c1": concern}, current_project_id="p1",
    ))})
    strategic_upd = _strategic_update(current_project_id_set="p1")
    upd = _update({1: _entity_update(strategic=strategic_upd)})
    events = StrategyShaper().shape(prior, upd, tick=10)
    assert "decision_divergence_detected" not in _types(events)


def test_no_events_when_entity_has_no_strategic_update():
    prior = _prior_state({1: _entity()})
    upd = _update({1: _entity_update()})
    events = StrategyShaper().shape(prior, upd, tick=10)
    assert events == []


def test_no_events_when_prior_entity_missing():
    prior = _prior_state({})
    upd = _update({1: _entity_update(property_updates={"last_routing_family": "hunt"})})
    events = StrategyShaper().shape(prior, upd, tick=10)
    assert events == []
