"""Unit tests for EventExtractor COGNITION/INFORMATION event emission (TCK-20260629-SIMQ-EMIT-COGNITION).

Tests for: self_model_updated, belief_assimilated, belief_updated,
paid_information_transaction, lead_certainty_changed.
"""
from __future__ import annotations
from unittest.mock import MagicMock

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor


# ── Minimal mock builders ─────────────────────────────────────────────────────

def _entity(eid: int = 1, leads: dict | None = None):
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
    e.strategic.leads = leads or {}
    return e


def _state(entities: dict, tick: int = 10):
    s = MagicMock()
    s.tick = tick
    s.entities = entities
    s.resource_nodes = {}
    return s


def _update_with_bundle(eid: int, bundle=True):
    eu = MagicMock()
    eu.property_updates = {}
    eu.combat_upd = None
    eu.resource_transfers = []
    eu.self_model_bundle_set = object() if bundle else None
    u = MagicMock()
    u.entity_updates = {eid: eu}
    return u


def _update_with_belief(eid: int, tick: int, subject: str = "iron_ore"):
    eu = MagicMock()
    eu.property_updates = {"last_assimilated_tick": tick, "last_assimilated_subject": subject}
    eu.combat_upd = None
    eu.resource_transfers = []
    eu.self_model_bundle_set = None
    u = MagicMock()
    u.entity_updates = {eid: eu}
    return u


def _intent_result(source_kind: str, accepted: bool = True, source_id: str = "provider_1"):
    i = MagicMock()
    i.source_kind = source_kind
    i.accepted = accepted
    i.source_id = source_id
    return i


def _update_with_intent_results(eid: int, results: list):
    eu = MagicMock()
    eu.property_updates = {}
    eu.combat_upd = None
    eu.resource_transfers = []
    eu.intent_results = results
    eu.self_model_bundle_set = None
    u = MagicMock()
    u.entity_updates = {eid: eu}
    u.world_updates = {}
    u.last_calamity_tick_set = None
    u.entities_add = []
    return u


def _empty_update(eid: int):
    eu = MagicMock()
    eu.property_updates = {}
    eu.combat_upd = None
    eu.resource_transfers = []
    eu.self_model_bundle_set = None
    u = MagicMock()
    u.entity_updates = {eid: eu}
    return u


def _lead(certainty: str):
    l = MagicMock()
    l.certainty = certainty
    return l


def _types(events) -> list[str]:
    return [e.event_type for e in events]


# ── self_model_updated ────────────────────────────────────────────────────────

def test_self_model_updated_emitted_when_bundle_set():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_bundle(1, bundle=True), ObservabilityMode.NORMAL)
    assert "self_model_updated" in _types(events)


def test_self_model_updated_not_emitted_when_bundle_not_set():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_bundle(1, bundle=False), ObservabilityMode.NORMAL)
    assert "self_model_updated" not in _types(events)


# ── belief_assimilated / belief_updated ───────────────────────────────────────

def test_belief_assimilated_emitted_when_tick_matches():
    e = _entity()
    state = _state({1: e}, tick=10)
    events = EventExtractor.extract(state, state, _update_with_belief(1, tick=10, subject="iron_ore"), ObservabilityMode.NORMAL)
    assert "belief_assimilated" in _types(events)


def test_belief_updated_emitted_with_belief_assimilated():
    e = _entity()
    state = _state({1: e}, tick=10)
    events = EventExtractor.extract(state, state, _update_with_belief(1, tick=10), ObservabilityMode.NORMAL)
    types = _types(events)
    assert "belief_assimilated" in types
    assert "belief_updated" in types


def test_belief_subject_in_payload():
    e = _entity()
    state = _state({1: e}, tick=10)
    events = EventExtractor.extract(state, state, _update_with_belief(1, tick=10, subject="dark_iron"), ObservabilityMode.NORMAL)
    ev = next(e for e in events if e.event_type == "belief_assimilated")
    assert ev.payload["subject"] == "dark_iron"


def test_belief_not_emitted_when_tick_stale():
    e = _entity()
    state = _state({1: e}, tick=10)
    events = EventExtractor.extract(state, state, _update_with_belief(1, tick=5), ObservabilityMode.NORMAL)
    assert "belief_assimilated" not in _types(events)


# ── paid_information_transaction ──────────────────────────────────────────────

def test_paid_information_transaction_emitted():
    e = _entity()
    state = _state({1: e})
    upd = _update_with_intent_results(1, [_intent_result("INFORMATION_PURCHASE")])
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "paid_information_transaction" in _types(events)


def test_paid_information_source_id_in_payload():
    e = _entity()
    state = _state({1: e})
    upd = _update_with_intent_results(1, [_intent_result("INFORMATION_PURCHASE", source_id="prov_42")])
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    ev = next(e for e in events if e.event_type == "paid_information_transaction")
    assert "prov_42" in ev.payload["source_id"]


def test_paid_information_not_emitted_for_other_intent():
    e = _entity()
    state = _state({1: e})
    upd = _update_with_intent_results(1, [_intent_result("TRADE")])
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "paid_information_transaction" not in _types(events)


def test_paid_information_not_emitted_when_rejected():
    e = _entity()
    state = _state({1: e})
    upd = _update_with_intent_results(1, [_intent_result("INFORMATION_PURCHASE", accepted=False)])
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "paid_information_transaction" not in _types(events)


# ── lead_certainty_changed ────────────────────────────────────────────────────

def test_lead_certainty_changed_emitted_when_certainty_differs():
    prior = _entity(leads={"lead_1": _lead("VAGUE")})
    curr = _entity(leads={"lead_1": _lead("APPROXIMATE")})
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _empty_update(1), ObservabilityMode.NORMAL)
    assert "lead_certainty_changed" in _types(events)


def test_lead_certainty_payload():
    prior = _entity(leads={"lead_x": _lead("VAGUE")})
    curr = _entity(leads={"lead_x": _lead("PRECISE")})
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _empty_update(1), ObservabilityMode.NORMAL)
    ev = next(e for e in events if e.event_type == "lead_certainty_changed")
    assert ev.payload["lead_id"] == "lead_x"
    assert "VAGUE" in ev.payload["from_certainty"]
    assert "PRECISE" in ev.payload["to_certainty"]


def test_lead_certainty_not_emitted_for_new_lead():
    prior = _entity(leads={})
    curr = _entity(leads={"lead_new": _lead("VAGUE")})
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _empty_update(1), ObservabilityMode.NORMAL)
    assert "lead_certainty_changed" not in _types(events)


def test_lead_certainty_not_emitted_when_unchanged():
    prior = _entity(leads={"lead_1": _lead("APPROXIMATE")})
    curr = _entity(leads={"lead_1": _lead("APPROXIMATE")})
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _empty_update(1), ObservabilityMode.NORMAL)
    assert "lead_certainty_changed" not in _types(events)
