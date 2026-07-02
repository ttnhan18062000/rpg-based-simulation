"""Unit tests for EventExtractor ECONOMY event emission (TCK-20260629-SIMQ-EMIT-ECONOMY).

Tests for: resource_harvested, item_crafted, shop_transaction, trade_executed,
quest_reward_dispensed, gold_sink_fired, paid_information_transaction.

Note: resource_transfers are CLEARED by ResourceTransactionPhase (economy.py:274).
All economy events are detected from entity_updates[eid].intent_results which survive.
"""
from __future__ import annotations
from unittest.mock import MagicMock

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor


# ── Builders ──────────────────────────────────────────────────────────────────

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
    e.strategic.leads = {}
    return e


def _state(entities: dict, tick: int = 10):
    s = MagicMock()
    s.tick = tick
    s.entities = entities
    s.resource_nodes = {}
    return s


def _ir(source_kind: str, accepted: bool = True, source_id: str = "src_1"):
    r = MagicMock()
    r.source_kind = source_kind
    r.accepted = accepted
    r.source_id = source_id
    return r


def _update_with_ir(eid: int, intent_results: list):
    eu = MagicMock()
    eu.property_updates = {}
    eu.resource_transfers = []
    eu.intent_results = intent_results
    eu.self_model_bundle_set = None
    eu.combat = None
    u = MagicMock()
    u.entity_updates = {eid: eu}
    u.world_updates = {}
    u.last_calamity_tick_set = None
    u.entities_add = []
    return u


def _types(events) -> list[str]:
    return [e.event_type for e in events]


# ── resource_harvested ────────────────────────────────────────────────────────

def test_resource_harvested_emitted():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("NODE")]), ObservabilityMode.NORMAL)
    assert "resource_harvested" in _types(events)


def test_resource_harvested_node_id_in_payload():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("NODE", source_id="node_42")]), ObservabilityMode.NORMAL)
    ev = next(e for e in events if e.event_type == "resource_harvested")
    assert "node_42" in ev.payload["node_id"]


def test_resource_harvested_not_emitted_when_rejected():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("NODE", accepted=False)]), ObservabilityMode.NORMAL)
    assert "resource_harvested" not in _types(events)


# ── item_crafted ──────────────────────────────────────────────────────────────

def test_item_crafted_emitted():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("CRAFTING")]), ObservabilityMode.NORMAL)
    assert "item_crafted" in _types(events)


def test_item_crafted_not_emitted_when_rejected():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("CRAFTING", accepted=False)]), ObservabilityMode.NORMAL)
    assert "item_crafted" not in _types(events)


# ── shop_transaction + trade_executed ─────────────────────────────────────────

def test_shop_transaction_emitted_for_shop_buy():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("SHOP_BUY")]), ObservabilityMode.NORMAL)
    assert "shop_transaction" in _types(events)


def test_trade_executed_emitted_with_shop_transaction():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("SHOP_SELL")]), ObservabilityMode.NORMAL)
    types = _types(events)
    assert "shop_transaction" in types
    assert "trade_executed" in types


def test_shop_transaction_payload_kind():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("SHOP_BUY")]), ObservabilityMode.NORMAL)
    ev = next(e for e in events if e.event_type == "shop_transaction")
    assert ev.payload["kind"] == "SHOP_BUY"


# ── quest_reward_dispensed ────────────────────────────────────────────────────

def test_quest_reward_dispensed_emitted():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("QUEST", source_id="quest_7")]), ObservabilityMode.NORMAL)
    assert "quest_reward_dispensed" in _types(events)


def test_quest_reward_dispensed_not_emitted_when_rejected():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("QUEST", accepted=False)]), ObservabilityMode.NORMAL)
    assert "quest_reward_dispensed" not in _types(events)


# ── gold_sink_fired ───────────────────────────────────────────────────────────

def test_gold_sink_fired_for_repair_fee():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("REPAIR_FEE")]), ObservabilityMode.NORMAL)
    assert "gold_sink_fired" in _types(events)


def test_gold_sink_fired_for_service_fee():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("SERVICE_FEE")]), ObservabilityMode.NORMAL)
    assert "gold_sink_fired" in _types(events)


def test_gold_sink_fired_for_tax():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("TAX")]), ObservabilityMode.NORMAL)
    assert "gold_sink_fired" in _types(events)


def test_gold_sink_mechanism_in_payload():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("TAX")]), ObservabilityMode.NORMAL)
    ev = next(e for e in events if e.event_type == "gold_sink_fired")
    assert ev.payload["mechanism"] == "TAX"


def test_unknown_source_kind_no_economy_event():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_ir(1, [_ir("UNKNOWN_KIND")]), ObservabilityMode.NORMAL)
    economy_types = [t for t in _types(events) if t in ("resource_harvested", "item_crafted", "shop_transaction", "trade_executed", "quest_reward_dispensed", "gold_sink_fired")]
    assert not economy_types
