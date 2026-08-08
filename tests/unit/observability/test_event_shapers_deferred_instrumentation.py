"""Unit tests for TCK-20260806-PUSH-SHAPER-DEFERRED-INSTRUMENTATION.

Tests DeferredInstrumentationShaper (resource-node lifecycle + faction_extinct, closing Phase 1's
own deferrals) and the conservation_law_verified cross-shaper aggregation step in
run_shadow_shapers(). See investigation.md for the corrected "no new instrumentation needed"
finding for resource-node events, and the deliberate faithful-reproduction-of-a-dead-check
decision for faction_extinct.
"""
from __future__ import annotations
from unittest.mock import MagicMock

from src.observability.config import ObservabilityMode
from src.observability.event_shapers import (
    DeferredInstrumentationShaper, PHASE2_SHAPER_REGISTRY, run_shadow_shapers,
)


def _node(remaining_charges, max_charges=10):
    n = MagicMock()
    n.remaining_charges = remaining_charges
    n.max_charges = max_charges
    return n


def _node_update(charges_delta=0):
    u = MagicMock()
    u.charges_delta = charges_delta
    return u


def _identity(faction=None):
    i = MagicMock()
    i.faction = faction
    return i


def _entity(faction=None):
    e = MagicMock()
    e.identity = _identity(faction)
    return e


def _prior_state(entities=None, resource_nodes=None, factions=None, tick=100):
    s = MagicMock()
    s.tick = tick
    s.entities = entities or {}
    s.resource_nodes = resource_nodes or {}
    s.factions = factions or {}
    s.feature_flags = {}
    return s


def _entity_update(identity=None):
    u = MagicMock()
    u.identity = identity
    u.combat = None
    u.intent_results = []
    u.property_updates = {}
    u.self_model_bundle_set = None
    u.strategic = None
    u.social = None
    u.group_id_set = None
    return u


def _identity_update(faction_set=None):
    u = MagicMock()
    u.faction_set = faction_set
    return u


def _update(node_updates=None, entity_updates=None, faction_updates=None,
            entities_add=None, entities_remove=None):
    u = MagicMock()
    u.node_updates = node_updates or {}
    u.entity_updates = entity_updates or {}
    u.faction_updates = faction_updates
    u.entities_add = entities_add or []
    u.entities_remove = entities_remove or []
    return u


def _types(events) -> list[str]:
    return [e.event_type for e in events]


def test_phase2_registry_contains_deferred_instrumentation_shaper():
    assert "deferred_instrumentation" in PHASE2_SHAPER_REGISTRY
    assert any(isinstance(s, DeferredInstrumentationShaper)
               for s in PHASE2_SHAPER_REGISTRY["deferred_instrumentation"])


# ── resource_node_depleted / resource_node_regenerated / node_recharged ────

def test_resource_node_depleted():
    prior = _prior_state(resource_nodes={"n1": _node(remaining_charges=3)})
    upd = _update(node_updates={"n1": _node_update(charges_delta=-3)})
    events = DeferredInstrumentationShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "resource_node_depleted")
    assert ev.payload["node_id"] == "n1"
    assert ev.payload["charges"] == 0


def test_resource_node_regenerated_and_node_recharged():
    prior = _prior_state(resource_nodes={"n1": _node(remaining_charges=0)})
    upd = _update(node_updates={"n1": _node_update(charges_delta=5)})
    events = DeferredInstrumentationShaper().shape(prior, upd, tick=10)
    types = _types(events)
    assert "resource_node_regenerated" in types
    assert "node_recharged" in types
    regen = next(e for e in events if e.event_type == "resource_node_regenerated")
    assert regen.payload["charges"] == 5


def test_no_resource_node_event_on_partial_depletion():
    prior = _prior_state(resource_nodes={"n1": _node(remaining_charges=5)})
    upd = _update(node_updates={"n1": _node_update(charges_delta=-2)})
    events = DeferredInstrumentationShaper().shape(prior, upd, tick=10)
    assert "resource_node_depleted" not in _types(events)


def test_no_resource_node_event_when_prior_node_missing():
    prior = _prior_state(resource_nodes={})
    upd = _update(node_updates={"n1": _node_update(charges_delta=-3)})
    events = DeferredInstrumentationShaper().shape(prior, upd, tick=10)
    assert events == []


# ── faction_extinct ──────────────────────────────────────────────────────

def test_faction_extinct_when_last_member_removed():
    dying = _entity(faction=1)
    prior = _prior_state(
        entities={1: dying},
        factions={1: MagicMock()},
    )
    upd = _update(
        faction_updates=[MagicMock()],  # non-empty gates the check
        entities_remove=[1],
    )
    events = DeferredInstrumentationShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "faction_extinct")
    assert ev.payload["faction_id"] == "1"


def test_faction_not_extinct_when_member_remains():
    alive1 = _entity(faction=1)
    alive2 = _entity(faction=1)
    prior = _prior_state(
        entities={1: alive1, 2: alive2},
        factions={1: MagicMock()},
    )
    upd = _update(faction_updates=[MagicMock()], entities_remove=[1])
    events = DeferredInstrumentationShaper().shape(prior, upd, tick=10)
    assert "faction_extinct" not in _types(events)


def test_faction_extinct_not_checked_without_faction_updates():
    dying = _entity(faction=1)
    prior = _prior_state(entities={1: dying}, factions={1: MagicMock()})
    upd = _update(faction_updates=None, entities_remove=[1])
    events = DeferredInstrumentationShaper().shape(prior, upd, tick=10)
    assert "faction_extinct" not in _types(events)


def test_faction_extinct_not_fired_if_faction_was_already_extinct():
    prior = _prior_state(entities={}, factions={1: MagicMock()})
    upd = _update(faction_updates=[MagicMock()], entities_remove=[])
    events = DeferredInstrumentationShaper().shape(prior, upd, tick=10)
    assert "faction_extinct" not in _types(events)


def test_faction_extinct_via_faction_reassignment():
    """Faithfully reproduces the old extractor's actual behavior: an entity's faction_set
    reassignment this tick counts against its OLD faction's living count, same as removal
    would."""
    switching = _entity(faction=1)
    prior = _prior_state(
        entities={1: switching},
        factions={1: MagicMock()},
    )
    upd = _update(
        faction_updates=[MagicMock()],
        entity_updates={1: _entity_update(identity=_identity_update(faction_set=2))},
    )
    events = DeferredInstrumentationShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "faction_extinct")
    assert ev.payload["faction_id"] == "1"


# ── conservation_law_verified (cross-shaper aggregation in run_shadow_shapers) ──

def test_conservation_law_verified_fires_when_economy_event_present():
    prior = _prior_state()
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_PHASE2": "ON"}
    # Build an update with a real economy intent_result so Phase 1's EconomyShaper fires
    ir = MagicMock(accepted=True, source_kind="NODE", source_id="n1")
    e_upd = _entity_update()
    e_upd.intent_results = [ir]
    upd = _update(entity_updates={1: e_upd})
    events = run_shadow_shapers(prior, upd, tick=50, mode=ObservabilityMode.LIGHT)
    assert "conservation_law_verified" in _types(events)


def test_conservation_law_verified_not_fired_off_interval():
    prior = _prior_state()
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_PHASE2": "ON"}
    ir = MagicMock(accepted=True, source_kind="NODE", source_id="n1")
    e_upd = _entity_update()
    e_upd.intent_results = [ir]
    upd = _update(entity_updates={1: e_upd})
    events = run_shadow_shapers(prior, upd, tick=51, mode=ObservabilityMode.LIGHT)
    assert "conservation_law_verified" not in _types(events)


def test_conservation_law_verified_not_fired_without_economy_activity():
    prior = _prior_state()
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_PHASE2": "ON"}
    upd = _update(entity_updates={})
    events = run_shadow_shapers(prior, upd, tick=50, mode=ObservabilityMode.LIGHT)
    assert "conservation_law_verified" not in _types(events)


def test_conservation_law_verified_not_delivered_in_shadow_mode():
    prior = _prior_state()
    prior.feature_flags = {"ENABLE_PUSH_EVENT_SHAPERS_PHASE2": "SHADOW"}
    ir = MagicMock(accepted=True, source_kind="NODE", source_id="n1")
    e_upd = _entity_update()
    e_upd.intent_results = [ir]
    upd = _update(entity_updates={1: e_upd})
    events = run_shadow_shapers(prior, upd, tick=50, mode=ObservabilityMode.LIGHT)
    assert "conservation_law_verified" not in _types(events)
