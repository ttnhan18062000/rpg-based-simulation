"""Unit tests for EventExtractor SimQ event emission (TCK-20260629-SIMQ-EMIT-STATE-DIFF).

Tests for: combat_initiated, near_death_survival, xp_granted, level_up,
resource_node_depleted, resource_node_regenerated, demographic_birth, demographic_mortality.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from unittest.mock import MagicMock

import pytest

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor


# ── Minimal mock state builder ────────────────────────────────────────────────

def _combat(hp: int = 100, max_hp: int = 100):
    c = MagicMock()
    c.hp = hp
    c.max_hp = max_hp
    return c


def _identity(evolution_points: int = 0, evolution_level: int = 1):
    i = MagicMock()
    i.evolution_points = evolution_points
    i.evolution_level = evolution_level
    return i


def _lifecycle(active: bool = True):
    lc = MagicMock()
    lc.active = active
    return lc


def _nav(position=(0.0, 0.0)):
    n = MagicMock()
    n.position = position
    return n


def _entity(
    eid: int = 1,
    hp: int = 100,
    max_hp: int = 100,
    active: bool = True,
    xp: int = 0,
    level: int = 1,
    gold: float = 100.0,
    kind: str = "hero",
):
    e = MagicMock()
    e.id = eid
    e.kind = kind
    e.combat = _combat(hp, max_hp)
    e.identity = _identity(xp, level)
    e.lifecycle = _lifecycle(active)
    e.navigation = _nav()
    e.inventory = MagicMock()
    e.inventory.gold = gold
    e.strategic = MagicMock()
    e.strategic.projects = {}
    return e


def _resource_node(remaining: int, max_charges: int = 5):
    n = MagicMock()
    n.remaining_charges = remaining
    n.max_charges = max_charges
    return n


def _state(entities: dict, resource_nodes: dict | None = None):
    s = MagicMock()
    s.tick = 10
    s.entities = entities
    s.resource_nodes = resource_nodes or {}
    return s


def _update(entity_updates: dict | None = None):
    u = MagicMock()
    u.entity_updates = entity_updates or {}
    return u


def _types(events) -> list[str]:
    return [e.event_type for e in events]


# ── combat_initiated ──────────────────────────────────────────────────────────

def test_combat_initiated_emitted_on_first_hit():
    prior = _entity(hp=100, max_hp=100)
    curr = _entity(hp=80, max_hp=100)
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update({1: MagicMock(combat_upd=None)}), ObservabilityMode.NORMAL)
    assert "combat_initiated" in _types(events)


def test_combat_initiated_not_emitted_when_already_damaged():
    prior = _entity(hp=80, max_hp=100)   # already below max
    curr = _entity(hp=70, max_hp=100)
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "combat_initiated" not in _types(events)


def test_combat_initiated_not_emitted_when_dead():
    prior = _entity(hp=100, max_hp=100)
    curr = _entity(hp=0, max_hp=100, active=False)
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "combat_initiated" not in _types(events)


# ── near_death_survival ───────────────────────────────────────────────────────

def test_near_death_survival_emitted_when_hp_crosses_threshold():
    prior = _entity(hp=25, max_hp=100)   # 25% — above 20%
    curr = _entity(hp=15, max_hp=100)    # 15% — below 20%
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "near_death_survival" in _types(events)


def test_near_death_survival_not_emitted_when_already_below_threshold():
    prior = _entity(hp=10, max_hp=100)   # 10% — already below 20%
    curr = _entity(hp=5, max_hp=100)     # 5%
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "near_death_survival" not in _types(events)


def test_near_death_survival_not_emitted_when_dead():
    prior = _entity(hp=25, max_hp=100)
    curr = _entity(hp=0, max_hp=100, active=False)
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "near_death_survival" not in _types(events)


def test_near_death_survival_payload():
    prior = _entity(hp=25, max_hp=100)
    curr = _entity(hp=15, max_hp=100)
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    nd = next(e for e in events if e.event_type == "near_death_survival")
    assert nd.payload["hp"] == 15
    assert nd.payload["max_hp"] == 100


# ── xp_granted ────────────────────────────────────────────────────────────────

def test_xp_granted_emitted_on_xp_increase():
    prior = _entity(xp=100)
    curr = _entity(xp=150)
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "xp_granted" in _types(events)


def test_xp_granted_amount_correct():
    prior = _entity(xp=100)
    curr = _entity(xp=175)
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    xp_event = next(e for e in events if e.event_type == "xp_granted")
    assert xp_event.payload["amount"] == 75


def test_xp_granted_not_emitted_when_xp_unchanged():
    prior = _entity(xp=100)
    curr = _entity(xp=100)
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "xp_granted" not in _types(events)


# ── level_up ──────────────────────────────────────────────────────────────────

def test_level_up_emitted_on_level_increase():
    prior = _entity(level=1)
    curr = _entity(level=2)
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "level_up" in _types(events)


def test_level_up_payload():
    prior = _entity(level=3)
    curr = _entity(level=4)
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    lu = next(e for e in events if e.event_type == "level_up")
    assert lu.payload["new_level"] == 4


def test_level_up_not_emitted_when_level_unchanged():
    prior = _entity(level=2)
    curr = _entity(level=2)
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "level_up" not in _types(events)


# ── resource_node_depleted / resource_node_regenerated ────────────────────────

def test_resource_node_depleted_emitted():
    prior_state = _state({}, {42: _resource_node(remaining=3)})
    curr_state = _state({}, {42: _resource_node(remaining=0)})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "resource_node_depleted" in _types(events)


def test_resource_node_depleted_payload():
    prior_state = _state({}, {42: _resource_node(remaining=3, max_charges=5)})
    curr_state = _state({}, {42: _resource_node(remaining=0, max_charges=5)})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    ev = next(e for e in events if e.event_type == "resource_node_depleted")
    assert ev.payload["node_id"] == 42
    assert ev.payload["charges"] == 0
    assert ev.payload["max_charges"] == 5


def test_resource_node_regenerated_emitted():
    prior_state = _state({}, {7: _resource_node(remaining=0)})
    curr_state = _state({}, {7: _resource_node(remaining=2)})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "resource_node_regenerated" in _types(events)


def test_resource_node_no_event_when_unchanged():
    prior_state = _state({}, {7: _resource_node(remaining=3)})
    curr_state = _state({}, {7: _resource_node(remaining=2)})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "resource_node_depleted" not in _types(events)
    assert "resource_node_regenerated" not in _types(events)


def test_resource_node_new_node_no_event():
    prior_state = _state({}, {})
    curr_state = _state({}, {99: _resource_node(remaining=0)})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "resource_node_depleted" not in _types(events)


# ── demographic_birth / demographic_mortality ──────────────────────────────────

def test_demographic_birth_emitted_on_spawn():
    prior_state = _state({})
    curr = _entity(eid=5)
    curr_state = _state({5: curr})
    curr_state.tick = 10
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "demographic_birth" in _types(events)


def test_demographic_mortality_emitted_on_despawn_no_attacker():
    prior = _entity(eid=5)
    prior_state = _state({5: prior})
    curr_state = _state({})
    curr_state.tick = 10
    upd = _update({5: MagicMock(combat_upd=None)})
    events = EventExtractor.extract(prior_state, curr_state, upd, ObservabilityMode.NORMAL)
    assert "demographic_mortality" in _types(events)


def test_demographic_mortality_not_emitted_on_combat_kill():
    prior = _entity(eid=5)
    prior_state = _state({5: prior})
    curr_state = _state({})
    curr_state.tick = 10
    combat_upd = MagicMock()
    combat_upd.attacker_id = 2  # killed by attacker
    upd = _update({5: MagicMock(combat_upd=combat_upd)})
    events = EventExtractor.extract(prior_state, curr_state, upd, ObservabilityMode.NORMAL)
    assert "demographic_mortality" not in _types(events)
