"""Unit tests for EventExtractor AGENCY event emission (TCK-20260629-SIMQ-EMIT-AGENCY).

Tests for: route_selected, action_executed.
Documents the DEFER gap (defer_with_reason cannot be emitted via state diff).
"""
from __future__ import annotations
from unittest.mock import MagicMock

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor


# ── Minimal mock builders ─────────────────────────────────────────────────────

def _entity(eid: int = 1):
    e = MagicMock()
    e.id = eid
    e.kind = "hero"
    e.combat = MagicMock()
    e.combat.hp = 100
    e.combat.max_hp = 100
    e.lifecycle = MagicMock()
    e.lifecycle.active = True
    e.navigation = MagicMock()
    e.navigation.position = (0.0, 0.0)
    e.inventory = MagicMock()
    e.inventory.gold = 0.0
    e.identity = MagicMock()
    e.identity.evolution_points = 0
    e.identity.evolution_level = 1
    e.strategic = MagicMock()
    e.strategic.projects = {}
    return e


def _state(entities: dict):
    s = MagicMock()
    s.tick = 5
    s.entities = entities
    s.resource_nodes = {}
    return s


def _update_with_routing(eid: int, family: str):
    eu = MagicMock()
    eu.property_updates = {"last_routing_family": family, "last_routing_tick": 5}
    eu.combat_upd = None
    u = MagicMock()
    u.entity_updates = {eid: eu}
    return u


def _update_no_routing(eid: int):
    eu = MagicMock()
    eu.property_updates = {}
    eu.combat_upd = None
    u = MagicMock()
    u.entity_updates = {eid: eu}
    return u


def _types(events) -> list[str]:
    return [e.event_type for e in events]


# ── route_selected ────────────────────────────────────────────────────────────

def test_route_selected_emitted_when_property_set():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_routing(1, "gather_resource"), ObservabilityMode.NORMAL)
    assert "route_selected" in _types(events)


def test_route_selected_payload_family():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_routing(1, "hunt_weak_enemy"), ObservabilityMode.NORMAL)
    ev = next(e for e in events if e.event_type == "route_selected")
    assert ev.payload["family"] == "hunt_weak_enemy"


def test_route_selected_not_emitted_without_routing_property():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_no_routing(1), ObservabilityMode.NORMAL)
    assert "route_selected" not in _types(events)


# ── action_executed ───────────────────────────────────────────────────────────

def test_action_executed_emitted_when_route_committed():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_routing(1, "recover"), ObservabilityMode.NORMAL)
    assert "action_executed" in _types(events)


def test_action_executed_payload_family():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_routing(1, "take_easy_quest"), ObservabilityMode.NORMAL)
    ev = next(e for e in events if e.event_type == "action_executed")
    assert ev.payload["family"] == "take_easy_quest"


def test_action_executed_not_emitted_without_routing_property():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_no_routing(1), ObservabilityMode.NORMAL)
    assert "action_executed" not in _types(events)


def test_both_route_and_action_emitted_together():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_routing(1, "sell_loot_for_gold"), ObservabilityMode.NORMAL)
    types = _types(events)
    assert "route_selected" in types
    assert "action_executed" in types


# ── defer gap documentation ───────────────────────────────────────────────────

def test_defer_gap_no_update_means_no_agency_event():
    """DEFER_WITH_REASON causes 'continue' in AdventureDecisionPhase — no EntityUpdate created.
    Neither route_selected nor action_executed can be emitted without a routing property.
    This test documents the gap: defer_with_reason events require phase-level hooks."""
    e = _entity()
    state = _state({1: e})
    # No entity_update for this entity = DEFER happened or entity was skipped
    u = MagicMock()
    u.entity_updates = {}
    events = EventExtractor.extract(state, state, u, ObservabilityMode.NORMAL)
    assert "route_selected" not in _types(events)
    assert "action_executed" not in _types(events)
    assert "defer_with_reason" not in _types(events)
