"""Unit tests for EventExtractor contract_milestone_completed emission.
(TCK-20260701-SIMQ-EMIT-CONTRACT-MILESTONE)

Strategy: milestones at 25%/50%/75% of contract duration (expiry_tick - created_tick).
Gate: once per (contract_id, milestone_label) per run.
Attributed to contract.source_id.
"""
from __future__ import annotations
from unittest.mock import MagicMock

import pytest

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor


def _contract(cid: str, status: str = "ACTIVE", source_id: int = 1,
               created_tick: int = 0, expiry_tick: int = 100,
               kind: str = "PROTECTION"):
    c = MagicMock()
    c.id = cid
    c.status = MagicMock(); c.status.name = status
    c.source_id = source_id
    c.created_tick = created_tick
    c.expiry_tick = expiry_tick
    c.kind = kind
    return c


def _entity(eid: int = 1, contracts: dict | None = None):
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
    e.strategic.contracts = dict(contracts or {})
    e.group_id = None
    e.social = MagicMock()
    e.social.trust_history = {}
    e.social.public_reputation = 0.0
    e.social.last_cooperation_decision = None
    return e


def _state(entities: dict, tick: int = 50):
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
# Basic milestone firing
# ---------------------------------------------------------------------------

def test_25pct_milestone_fires():
    c = _contract("c1", created_tick=0, expiry_tick=100)
    e_prior = _entity(1, contracts={"c1": c})
    e_curr = _entity(1, contracts={"c1": c})
    # tick=25 → elapsed=25, progress=0.25 → exactly at threshold
    events = _extract(_state({1: e_prior}, tick=24), _state({1: e_curr}, tick=25))
    ms = [e for e in events if e.event_type == "contract_milestone_completed"]
    assert len(ms) == 1
    assert ms[0].payload["milestone"] == "25%"
    assert ms[0].payload["contract_id"] == "c1"


def test_50pct_milestone_fires():
    c = _contract("c1", created_tick=0, expiry_tick=100)
    e_prior = _entity(1, contracts={"c1": c})
    e_curr = _entity(1, contracts={"c1": c})
    events = _extract(_state({1: e_prior}, tick=49), _state({1: e_curr}, tick=50))
    ms = [e for e in events if e.event_type == "contract_milestone_completed"]
    assert any(m.payload["milestone"] == "50%" for m in ms)


def test_75pct_milestone_fires():
    c = _contract("c1", created_tick=0, expiry_tick=100)
    e_prior = _entity(1, contracts={"c1": c})
    e_curr = _entity(1, contracts={"c1": c})
    events = _extract(_state({1: e_prior}, tick=74), _state({1: e_curr}, tick=75))
    ms = [e for e in events if e.event_type == "contract_milestone_completed"]
    assert any(m.payload["milestone"] == "75%" for m in ms)


def test_all_three_milestones_at_tick_past_75pct():
    # First extraction at tick=80 — all 3 thresholds crossed at once
    c = _contract("c1", created_tick=0, expiry_tick=100)
    e = _entity(1, contracts={"c1": c})
    events = _extract(_state({1: e}, tick=79), _state({1: e}, tick=80))
    ms = [e for e in events if e.event_type == "contract_milestone_completed"]
    labels = {m.payload["milestone"] for m in ms}
    assert labels == {"25%", "50%", "75%"}


# ---------------------------------------------------------------------------
# Payload content
# ---------------------------------------------------------------------------

def test_payload_fields():
    c = _contract("cx", source_id=7, kind="LOAN", created_tick=0, expiry_tick=40)
    e = _entity(7, contracts={"cx": c})
    events = _extract(_state({7: e}, tick=9), _state({7: e}, tick=10))
    ms = [ev for ev in events if ev.event_type == "contract_milestone_completed"]
    assert len(ms) == 1
    assert ms[0].entity_id == 7          # attributed to source_id
    assert ms[0].payload["contract_id"] == "cx"
    assert ms[0].payload["milestone"] == "25%"
    assert "LOAN" in ms[0].payload["kind"]


# ---------------------------------------------------------------------------
# Gate: once per (contract, milestone) per run
# ---------------------------------------------------------------------------

def test_no_duplicate_across_ticks():
    c = _contract("c1", created_tick=0, expiry_tick=100)
    e = _entity(1, contracts={"c1": c})
    # First tick at 25%
    events1 = _extract(_state({1: e}, tick=24), _state({1: e}, tick=25))
    ms1 = [ev for ev in events1 if ev.event_type == "contract_milestone_completed"
           and ev.payload["milestone"] == "25%"]
    assert len(ms1) == 1
    # Second tick — gate already set
    events2 = _extract(_state({1: e}, tick=25), _state({1: e}, tick=26))
    ms2 = [ev for ev in events2 if ev.event_type == "contract_milestone_completed"
           and ev.payload["milestone"] == "25%"]
    assert len(ms2) == 0


def test_gate_per_contract_id_not_shared():
    c1 = _contract("c1", created_tick=0, expiry_tick=100)
    c2 = _contract("c2", created_tick=0, expiry_tick=100)
    e = _entity(1, contracts={"c1": c1, "c2": c2})
    events = _extract(_state({1: e}, tick=24), _state({1: e}, tick=25))
    ms = [ev for ev in events if ev.event_type == "contract_milestone_completed"
          and ev.payload["milestone"] == "25%"]
    assert len(ms) == 2  # one per contract


def test_gate_per_entity_only_once_per_contract():
    # Same contract in two entities' strategic.contracts — should fire ONCE total
    c = _contract("shared", source_id=1, created_tick=0, expiry_tick=100)
    e1 = _entity(1, contracts={"shared": c})
    e2 = _entity(2, contracts={"shared": c})
    events = _extract(
        _state({1: e1, 2: e2}, tick=24),
        _state({1: e1, 2: e2}, tick=25),
    )
    ms = [ev for ev in events if ev.event_type == "contract_milestone_completed"
          and ev.payload["milestone"] == "25%"]
    assert len(ms) == 1


# ---------------------------------------------------------------------------
# Non-ACTIVE contracts — no emit
# ---------------------------------------------------------------------------

def test_offered_contract_no_milestone():
    c = _contract("c1", status="OFFERED", created_tick=0, expiry_tick=100)
    e = _entity(1, contracts={"c1": c})
    events = _extract(_state({1: e}, tick=24), _state({1: e}, tick=25))
    ms = [ev for ev in events if ev.event_type == "contract_milestone_completed"]
    assert len(ms) == 0


def test_fulfilled_contract_no_milestone():
    c = _contract("c1", status="FULFILLED", created_tick=0, expiry_tick=100)
    e = _entity(1, contracts={"c1": c})
    events = _extract(_state({1: e}, tick=24), _state({1: e}, tick=25))
    ms = [ev for ev in events if ev.event_type == "contract_milestone_completed"]
    assert len(ms) == 0


# ---------------------------------------------------------------------------
# No duration (expiry_tick == -1) — no emit
# ---------------------------------------------------------------------------

def test_no_expiry_no_milestone():
    c = _contract("c1", expiry_tick=-1)
    e = _entity(1, contracts={"c1": c})
    events = _extract(_state({1: e}, tick=50), _state({1: e}, tick=51))
    ms = [ev for ev in events if ev.event_type == "contract_milestone_completed"]
    assert len(ms) == 0


# ---------------------------------------------------------------------------
# Non-zero created_tick
# ---------------------------------------------------------------------------

def test_duration_offset_by_created_tick():
    # Contract: created=50, expiry=150, duration=100 → 25% at tick=75
    c = _contract("c1", created_tick=50, expiry_tick=150)
    e = _entity(1, contracts={"c1": c})
    # tick=74 → elapsed=24, progress=0.24 → below threshold
    events_before = _extract(_state({1: e}, tick=74), _state({1: e}, tick=74))
    assert not any(ev.event_type == "contract_milestone_completed" for ev in events_before)
    # tick=75 → elapsed=25, progress=0.25 → at threshold
    events_at = _extract(_state({1: e}, tick=74), _state({1: e}, tick=75))
    ms = [ev for ev in events_at if ev.event_type == "contract_milestone_completed"]
    assert len(ms) == 1
    assert ms[0].payload["milestone"] == "25%"
