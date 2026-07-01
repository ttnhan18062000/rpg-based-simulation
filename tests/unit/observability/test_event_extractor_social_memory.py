"""Unit tests for EventExtractor social_memory_created emission (TCK-20260701-SIMQ-EMIT-SOCIAL-MEM).

Verifies that trust_history diff produces social_memory_created events:
- new relationship entry → emit
- significant delta (≥ 0.3) → emit
- small delta (< 0.3) → no emit
- once-per-run gate → no duplicate
- no social component → no crash
"""
from __future__ import annotations
from unittest.mock import MagicMock

import pytest

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor


def _entity(eid: int = 1, trust: dict | None = None, reputation: float = 0.0):
    e = MagicMock()
    e.id = eid
    e.kind = "hero"
    e.combat = MagicMock(); e.combat.hp = 100; e.combat.max_hp = 100
    e.lifecycle = MagicMock(); e.lifecycle.active = True
    e.navigation = MagicMock(); e.navigation.position = (0.0, 0.0)
    e.inventory = MagicMock(); e.inventory.gold = 0.0
    e.identity = MagicMock()
    e.identity.evolution_points = 0; e.identity.evolution_level = 1
    e.identity.learned_skills = frozenset(); e.identity.traits = frozenset()
    e.identity.active_breakthroughs = frozenset(); e.identity.unspent_ap = 0
    e.strategic = MagicMock()
    e.strategic.projects = {}; e.strategic.leads = {}
    e.strategic.current_project_id = None; e.strategic.concerns = {}
    e.strategic.contracts = {}
    e.group_id = None
    e.social = MagicMock()
    e.social.trust_history = dict(trust or {})
    e.social.public_reputation = reputation
    e.social.last_cooperation_decision = None
    return e


def _state(entities: dict, tick: int = 10):
    s = MagicMock()
    s.tick = tick
    s.entities = entities
    s.resource_nodes = {}
    s.regions = {}
    s.factions = {}
    s.world_updates = {}
    s.world_events = []
    return s


def _extract(prior, curr, mode=ObservabilityMode.FULL):
    upds = MagicMock()
    upds.entity_updates = {}
    upds.faction_updates = {}
    upds.resource_node_updates = {}
    upds.world_updates = {}
    return EventExtractor.extract(prior, curr, upds, mode)


@pytest.fixture(autouse=True)
def reset():
    EventExtractor.reset_run_state()
    yield
    EventExtractor.reset_run_state()


# ---------------------------------------------------------------------------
# New trust entry → emit
# ---------------------------------------------------------------------------

def test_new_trust_entry_emits():
    prior_e = _entity(1, trust={})
    curr_e = _entity(1, trust={2: 0.5})
    prior = _state({1: prior_e})
    curr = _state({1: curr_e})
    events = _extract(prior, curr)
    sm = [e for e in events if e.event_type == "social_memory_created"]
    assert len(sm) == 1
    assert sm[0].entity_id == 1
    assert sm[0].payload["other_entity_id"] == 2
    assert sm[0].payload["score"] == pytest.approx(0.5)


def test_new_trust_entry_negative_emits():
    prior_e = _entity(1, trust={})
    curr_e = _entity(1, trust={3: -0.7})
    events = _extract(_state({1: prior_e}), _state({1: curr_e}))
    sm = [e for e in events if e.event_type == "social_memory_created"]
    assert len(sm) == 1
    assert sm[0].payload["other_entity_id"] == 3


# ---------------------------------------------------------------------------
# Significant delta (≥ 0.3) → emit
# ---------------------------------------------------------------------------

def test_significant_delta_emits():
    prior_e = _entity(1, trust={2: 0.1})
    curr_e = _entity(1, trust={2: 0.5})  # delta = 0.4
    events = _extract(_state({1: prior_e}), _state({1: curr_e}))
    sm = [e for e in events if e.event_type == "social_memory_created"]
    assert len(sm) == 1


def test_delta_exactly_at_threshold_emits():
    prior_e = _entity(1, trust={2: 0.0})
    curr_e = _entity(1, trust={2: 0.3})  # delta = 0.3 exactly
    events = _extract(_state({1: prior_e}), _state({1: curr_e}))
    sm = [e for e in events if e.event_type == "social_memory_created"]
    assert len(sm) == 1


# ---------------------------------------------------------------------------
# Small delta (< 0.3) → no emit
# ---------------------------------------------------------------------------

def test_small_delta_no_emit():
    prior_e = _entity(1, trust={2: 0.1})
    curr_e = _entity(1, trust={2: 0.35})  # delta = 0.25
    events = _extract(_state({1: prior_e}), _state({1: curr_e}))
    sm = [e for e in events if e.event_type == "social_memory_created"]
    assert len(sm) == 0


def test_no_change_no_emit():
    prior_e = _entity(1, trust={2: 0.5})
    curr_e = _entity(1, trust={2: 0.5})
    events = _extract(_state({1: prior_e}), _state({1: curr_e}))
    sm = [e for e in events if e.event_type == "social_memory_created"]
    assert len(sm) == 0


# ---------------------------------------------------------------------------
# Once-per-run gate
# ---------------------------------------------------------------------------

def test_once_per_run_no_duplicate():
    prior_e = _entity(1, trust={})
    curr_e = _entity(1, trust={2: 0.5})
    state_a = _state({1: prior_e}, tick=10)
    state_b = _state({1: curr_e}, tick=11)
    # First extraction — entry added
    events1 = _extract(state_a, state_b)
    assert len([e for e in events1 if e.event_type == "social_memory_created"]) == 1

    # Second extraction same pair — already gated
    prior_e2 = _entity(1, trust={2: 0.5})
    curr_e2 = _entity(1, trust={2: 0.9})  # large delta but pair already seen
    events2 = _extract(_state({1: prior_e2}, tick=11), _state({1: curr_e2}, tick=12))
    assert len([e for e in events2 if e.event_type == "social_memory_created"]) == 0


def test_different_pair_not_gated():
    prior_e = _entity(1, trust={})
    curr_e = _entity(1, trust={2: 0.5, 3: 0.6})
    events = _extract(_state({1: prior_e}), _state({1: curr_e}))
    sm = [e for e in events if e.event_type == "social_memory_created"]
    assert len(sm) == 2


# ---------------------------------------------------------------------------
# Multiple entities
# ---------------------------------------------------------------------------

def test_multiple_entities():
    prior_e1 = _entity(1, trust={})
    prior_e2 = _entity(2, trust={})
    curr_e1 = _entity(1, trust={2: 0.4})
    curr_e2 = _entity(2, trust={1: 0.4})
    prior = _state({1: prior_e1, 2: prior_e2})
    curr = _state({1: curr_e1, 2: curr_e2})
    events = _extract(prior, curr)
    sm = [e for e in events if e.event_type == "social_memory_created"]
    assert len(sm) == 2
    eids = {e.entity_id for e in sm}
    assert eids == {1, 2}


# ---------------------------------------------------------------------------
# Missing social component — no crash
# ---------------------------------------------------------------------------

def test_no_social_component_no_crash():
    prior_e = _entity(1, trust={})
    curr_e = _entity(1, trust={2: 0.5})
    del curr_e.social  # simulate missing social
    events = _extract(_state({1: prior_e}), _state({1: curr_e}))
    # Should not crash; no social_memory_created expected
    sm = [e for e in events if e.event_type == "social_memory_created"]
    assert len(sm) == 0
