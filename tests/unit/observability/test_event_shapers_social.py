"""Unit tests for TCK-20260806-PUSH-SHAPER-REGISTRY-SOCIAL.

Tests the apply-layer (push-based) SocialShaper: trust/reputation/contract/group events derived
from prior_state + update alone. Includes a regression test for the real contract_expired_offer
double-firing bug found via real-kernel verification (see investigation.md's Key finding 2).
"""
from __future__ import annotations
from unittest.mock import MagicMock

import pytest

from src.observability.event_shapers import SocialShaper, PHASE2_SHAPER_REGISTRY


def _social(trust_history=None, public_reputation=1.0):
    s = MagicMock()
    s.trust_history = trust_history or {}
    s.public_reputation = public_reputation
    return s


def _strategic(contracts=None):
    s = MagicMock()
    s.contracts = contracts or {}
    return s


def _entity(group_id=None, social=None, strategic=None):
    e = MagicMock()
    e.group_id = group_id
    e.social = social or _social()
    e.strategic = strategic or _strategic()
    return e


def _prior_state(entities: dict, tick: int = 100):
    s = MagicMock()
    s.tick = tick
    s.entities = entities
    s.feature_flags = {}
    return s


def _contract(cid, status, source_id=1, expiry_tick=200, created_tick=100, kind="TRADE"):
    c = MagicMock()
    c.id = cid
    c.status = status
    c.source_id = source_id
    c.expiry_tick = expiry_tick
    c.created_tick = created_tick
    c.kind = kind
    return c


def _entity_update(group_id_set=None, social=None, strategic=None):
    u = MagicMock()
    u.group_id_set = group_id_set
    u.social = social
    u.strategic = strategic
    u.combat = None
    u.intent_results = []
    u.identity = None
    u.property_updates = {}
    u.self_model_bundle_set = None
    return u


def _social_update(trust_delta=None, reputation_set=None):
    u = MagicMock()
    u.trust_delta = trust_delta or {}
    u.reputation_set = reputation_set
    return u


def _strategic_update(contracts_add_or_update=None, contracts_remove=None,
                       current_project_id_set=None):
    u = MagicMock()
    u.contracts_add_or_update = contracts_add_or_update or []
    u.contracts_remove = contracts_remove or ()
    u.current_project_id_set = current_project_id_set
    return u


def _update(entity_updates: dict | None = None):
    u = MagicMock()
    u.entity_updates = entity_updates or {}
    return u


def _types(events) -> list[str]:
    return [e.event_type for e in events]


@pytest.fixture(autouse=True)
def _reset_shaper_state():
    SocialShaper.reset_run_state()
    yield
    SocialShaper.reset_run_state()


def test_phase2_registry_contains_social_shaper():
    assert "social" in PHASE2_SHAPER_REGISTRY
    assert any(isinstance(s, SocialShaper) for s in PHASE2_SHAPER_REGISTRY["social"])


# ── group_joined / group_expelled (the -1 sentinel) ─────────────────────────

def test_group_joined():
    prior = _prior_state({1: _entity(group_id=None)})
    upd = _update({1: _entity_update(group_id_set=5)})
    events = SocialShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "group_joined")
    assert ev.payload["group_id"] == "5"


def test_group_expelled_via_minus_one_sentinel():
    prior = _prior_state({1: _entity(group_id=5)})
    upd = _update({1: _entity_update(group_id_set=-1)})
    events = SocialShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "group_expelled")
    assert ev.payload["prior_group_id"] == "5"


def test_no_group_event_when_group_id_set_is_none():
    prior = _prior_state({1: _entity(group_id=5)})
    upd = _update({1: _entity_update(group_id_set=None)})
    events = SocialShaper().shape(prior, upd, tick=10)
    assert "group_joined" not in _types(events)
    assert "group_expelled" not in _types(events)


# ── reputation_delta ─────────────────────────────────────────────────────

def test_reputation_delta():
    prior = _prior_state({1: _entity(social=_social(public_reputation=1.0))})
    upd = _update({1: _entity_update(social=_social_update(reputation_set=1.2))})
    events = SocialShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "reputation_delta")
    assert round(ev.payload["delta"], 2) == 0.2


def test_reputation_delta_not_emitted_below_threshold():
    prior = _prior_state({1: _entity(social=_social(public_reputation=1.0))})
    upd = _update({1: _entity_update(social=_social_update(reputation_set=1.02))})
    events = SocialShaper().shape(prior, upd, tick=10)
    assert "reputation_delta" not in _types(events)


# ── social_memory_created ────────────────────────────────────────────────

def test_social_memory_created_for_new_pair():
    prior = _prior_state({1: _entity(social=_social(trust_history={}))})
    upd = _update({1: _entity_update(social=_social_update(trust_delta={2: 0.1}))})
    events = SocialShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "social_memory_created")
    assert ev.payload["other_entity_id"] == 2


def test_social_memory_created_for_significant_change():
    prior = _prior_state({1: _entity(social=_social(trust_history={2: 0.2}))})
    upd = _update({1: _entity_update(social=_social_update(trust_delta={2: 0.5}))})
    events = SocialShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "social_memory_created")
    assert round(ev.payload["score"], 2) == 0.7


def test_social_memory_not_created_for_insignificant_change():
    prior = _prior_state({1: _entity(social=_social(trust_history={2: 0.2}))})
    upd = _update({1: _entity_update(social=_social_update(trust_delta={2: 0.05}))})
    events = SocialShaper().shape(prior, upd, tick=10)
    assert "social_memory_created" not in _types(events)


def test_social_memory_not_repeated_for_same_pair():
    prior = _prior_state({1: _entity(social=_social(trust_history={}))})
    upd = _update({1: _entity_update(social=_social_update(trust_delta={2: 0.5}))})
    SocialShaper().shape(prior, upd, tick=10)
    events2 = SocialShaper().shape(prior, upd, tick=11)
    assert "social_memory_created" not in _types(events2)


# ── contract lifecycle events ────────────────────────────────────────────

def test_contract_offer_created():
    prior = _prior_state({1: _entity(strategic=_strategic(contracts={}))})
    new_c = _contract("c1", MagicMock(name="OFFERED"))
    new_c.status.name = "OFFERED"
    upd = _update({1: _entity_update(strategic=_strategic_update(contracts_add_or_update=[new_c]))})
    events = SocialShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "contract_offer_created")
    assert ev.payload["contract_id"] == "c1"


def test_contract_offer_accepted():
    prior_c = _contract("c1", MagicMock())
    prior_c.status.name = "OFFERED"
    prior = _prior_state({1: _entity(strategic=_strategic(contracts={"c1": prior_c}))})
    new_c = _contract("c1", MagicMock())
    new_c.status.name = "ACTIVE"
    upd = _update({1: _entity_update(strategic=_strategic_update(contracts_add_or_update=[new_c]))})
    events = SocialShaper().shape(prior, upd, tick=10)
    assert "contract_offer_accepted" in _types(events)


def test_contract_completed():
    prior_c = _contract("c1", MagicMock())
    prior_c.status.name = "ACTIVE"
    prior = _prior_state({1: _entity(strategic=_strategic(contracts={"c1": prior_c}))})
    new_c = _contract("c1", MagicMock())
    new_c.status.name = "FULFILLED"
    upd = _update({1: _entity_update(strategic=_strategic_update(contracts_add_or_update=[new_c]))})
    events = SocialShaper().shape(prior, upd, tick=10)
    assert "contract_completed" in _types(events)


def test_contract_lapsed():
    prior_c = _contract("c1", MagicMock())
    prior_c.status.name = "ACTIVE"
    prior = _prior_state({1: _entity(strategic=_strategic(contracts={"c1": prior_c}))})
    new_c = _contract("c1", MagicMock())
    new_c.status.name = "EXPIRED"
    upd = _update({1: _entity_update(strategic=_strategic_update(contracts_add_or_update=[new_c]))})
    events = SocialShaper().shape(prior, upd, tick=10)
    assert "contract_lapsed" in _types(events)


def test_contract_expired_offer_status_transition():
    prior_c = _contract("c1", MagicMock())
    prior_c.status.name = "OFFERED"
    prior = _prior_state({1: _entity(strategic=_strategic(contracts={"c1": prior_c}))})
    new_c = _contract("c1", MagicMock())
    new_c.status.name = "EXPIRED"
    upd = _update({1: _entity_update(strategic=_strategic_update(contracts_add_or_update=[new_c]))})
    events = SocialShaper().shape(prior, upd, tick=10)
    assert "contract_expired_offer" in _types(events)


def test_contract_expired_offer_reap_path():
    prior_c = _contract("c1", MagicMock())
    prior_c.status.name = "OFFERED"
    prior = _prior_state({1: _entity(strategic=_strategic(contracts={"c1": prior_c}))})
    upd = _update({1: _entity_update(strategic=_strategic_update(contracts_remove=["c1"]))})
    events = SocialShaper().shape(prior, upd, tick=10)
    assert "contract_expired_offer" in _types(events)


def test_contract_expired_offer_not_double_fired_when_both_signals_present():
    """Regression test for the real bug found via kernel verification: a contract can be
    BOTH status-transitioned to EXPIRED (contracts_add_or_update) AND reaped
    (contracts_remove) in the SAME tick — must fire exactly once, not twice."""
    prior_c = _contract("c1", MagicMock())
    prior_c.status.name = "OFFERED"
    prior = _prior_state({1: _entity(strategic=_strategic(contracts={"c1": prior_c}))})
    new_c = _contract("c1", MagicMock())
    new_c.status.name = "EXPIRED"
    upd = _update({1: _entity_update(strategic=_strategic_update(
        contracts_add_or_update=[new_c], contracts_remove=["c1"],
    ))})
    events = SocialShaper().shape(prior, upd, tick=10)
    expired_events = [e for e in events if e.event_type == "contract_expired_offer"]
    assert len(expired_events) == 1


# ── contract_milestone_completed ─────────────────────────────────────────

def test_contract_milestone_completed_fires_at_threshold():
    active_c = _contract("c1", MagicMock(), created_tick=0, expiry_tick=100)
    active_c.status.name = "ACTIVE"
    prior = _prior_state({1: _entity(strategic=_strategic(contracts={"c1": active_c}))}, tick=0)
    upd = _update({1: _entity_update(strategic=_strategic_update())})
    events = SocialShaper().shape(prior, upd, tick=25)
    ev = next(e for e in events if e.event_type == "contract_milestone_completed")
    assert ev.payload["milestone"] == "25%"


def test_contract_milestone_not_repeated_for_same_threshold():
    active_c = _contract("c1", MagicMock(), created_tick=0, expiry_tick=100)
    active_c.status.name = "ACTIVE"
    prior = _prior_state({1: _entity(strategic=_strategic(contracts={"c1": active_c}))}, tick=0)
    upd = _update({1: _entity_update(strategic=_strategic_update())})
    SocialShaper().shape(prior, upd, tick=25)
    events2 = SocialShaper().shape(prior, upd, tick=26)
    assert "contract_milestone_completed" not in _types(events2)


def test_contract_milestone_not_fired_for_non_active_contract():
    offered_c = _contract("c1", MagicMock(), created_tick=0, expiry_tick=100)
    offered_c.status.name = "OFFERED"
    prior = _prior_state({1: _entity(strategic=_strategic(contracts={"c1": offered_c}))}, tick=0)
    upd = _update({1: _entity_update(strategic=_strategic_update())})
    events = SocialShaper().shape(prior, upd, tick=25)
    assert "contract_milestone_completed" not in _types(events)
