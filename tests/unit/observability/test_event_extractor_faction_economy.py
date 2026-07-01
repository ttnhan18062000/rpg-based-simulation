"""Unit tests for EventExtractor FACTION-ECONOMY event emission (TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY).

Tests for: paid_info_transaction, conservation_law_verified, alliance_proposed,
resource_seized, scenario_objective_progressed (via scenario_runtime).
social_memory_created and contract_milestone_completed are blocked (missing infrastructure).
"""
from __future__ import annotations
from unittest.mock import MagicMock, patch

import pytest

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor


def _entity(eid: int = 1):
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
    e.group_id = None
    return e


def _state(entities: dict, tick: int = 50, factions: dict | None = None):
    s = MagicMock()
    s.tick = tick
    s.entities = entities
    s.resource_nodes = {}
    s.regions = {}
    s.factions = factions or {}
    return s


def _update(eid: int, intent_src_kind: str | None = None,
            faction_updates=None, world_updates=None, entities_add=None):
    eu = MagicMock()
    eu.property_updates = {}
    eu.combat_upd = None
    eu.self_model_bundle_set = None
    if intent_src_kind:
        ir = MagicMock()
        ir.source_kind = intent_src_kind
        ir.gold_delta = -10.0
        eu.intent_results = [ir]
    else:
        eu.intent_results = []
    u = MagicMock()
    u.entity_updates = {eid: eu}
    u.world_updates = world_updates or {}
    u.last_calamity_tick_set = None
    u.entities_add = entities_add or []
    u.faction_updates = faction_updates or []
    u.world_events_add = []
    return u


def _types(events) -> list[str]:
    return [e.event_type for e in events]


@pytest.fixture(autouse=True)
def reset_extractor():
    EventExtractor.reset_run_state()
    yield
    EventExtractor.reset_run_state()


# ── paid_info_transaction ──────────────────────────────────────────────────────

class TestPaidInfoTransaction:
    def test_fires_on_information_purchase(self):
        entity = _entity()
        events = EventExtractor.extract(
            _state({1: entity}), _state({1: entity}),
            _update(1, intent_src_kind="INFORMATION_PURCHASE"),
            ObservabilityMode.NORMAL,
        )
        assert "paid_info_transaction" in _types(events)

    def test_not_fired_on_other_purchase(self):
        entity = _entity()
        events = EventExtractor.extract(
            _state({1: entity}), _state({1: entity}),
            _update(1, intent_src_kind="TRADE"),
            ObservabilityMode.NORMAL,
        )
        assert "paid_info_transaction" not in _types(events)

    def test_not_fired_without_purchase(self):
        entity = _entity()
        events = EventExtractor.extract(
            _state({1: entity}), _state({1: entity}),
            _update(1), ObservabilityMode.NORMAL,
        )
        assert "paid_info_transaction" not in _types(events)


# ── conservation_law_verified ──────────────────────────────────────────────────

class TestConservationLawVerified:
    def _update_with_economy(self, eid: int):
        # tick%50 guard + need an economy event already emitted in same extraction
        # simplest: provide an INFORMATION_PURCHASE so resource_harvested or similar
        # emits alongside. Actually conservation_law_verified checks tick%50 and
        # presence of economy events in the already-built events list.
        # We need tick divisible by 50 and at least one economy event emitted first.
        return _update(eid, intent_src_kind="INFORMATION_PURCHASE")

    def test_fires_at_tick_multiple_of_50_with_economy_event(self):
        entity = _entity()
        events = EventExtractor.extract(
            _state({1: entity}, tick=50), _state({1: entity}, tick=50),
            self._update_with_economy(1), ObservabilityMode.NORMAL,
        )
        assert "conservation_law_verified" in _types(events)

    def test_not_fired_at_non_multiple_tick(self):
        entity = _entity()
        events = EventExtractor.extract(
            _state({1: entity}, tick=51), _state({1: entity}, tick=51),
            self._update_with_economy(1), ObservabilityMode.NORMAL,
        )
        assert "conservation_law_verified" not in _types(events)

    def test_not_fired_without_economy_events(self):
        entity = _entity()
        events = EventExtractor.extract(
            _state({1: entity}, tick=50), _state({1: entity}, tick=50),
            _update(1), ObservabilityMode.NORMAL,
        )
        assert "conservation_law_verified" not in _types(events)


# ── alliance_proposed ──────────────────────────────────────────────────────────

class TestAllianceProposed:
    def _diplo_state(self, name: str):
        s = MagicMock(); s.name = name
        return s

    def _faction_update(self, faction_id: str, other_fid: str, new_state_name: str,
                        territory_add=None, tension_delta: float = 0.0):
        fu = MagicMock()
        fu.faction_id = faction_id
        fu.diplomatic_relations_set = {other_fid: self._diplo_state(new_state_name)}
        fu.territory_add = territory_add or []
        fu.tension_delta = tension_delta
        return fu

    def _prior_faction(self, relation_to: str, relation_state: str):
        # prior_state.factions[fid].diplomatic_relations[other_fid].name == relation_state
        rel = MagicMock(); rel.name = relation_state
        f = MagicMock()
        f.diplomatic_relations = {relation_to: rel}
        return f

    def test_fires_on_neutral_to_allied_transition(self):
        entity = _entity()
        prior_faction = self._prior_faction("f2", "NEUTRAL")
        fu = self._faction_update("f1", "f2", "ALLIED")
        events = EventExtractor.extract(
            _state({1: entity}, factions={"f1": prior_faction}),
            _state({1: entity}, factions={"f1": prior_faction}),
            _update(1, faction_updates=[fu]), ObservabilityMode.NORMAL,
        )
        assert "alliance_proposed" in _types(events)

    def test_fires_on_hostile_to_allied_transition(self):
        entity = _entity()
        prior_faction = self._prior_faction("f2", "HOSTILE")
        fu = self._faction_update("f1", "f2", "ALLIED")
        events = EventExtractor.extract(
            _state({1: entity}, factions={"f1": prior_faction}),
            _state({1: entity}, factions={"f1": prior_faction}),
            _update(1, faction_updates=[fu]), ObservabilityMode.NORMAL,
        )
        assert "alliance_proposed" in _types(events)

    def test_not_fired_when_already_allied(self):
        entity = _entity()
        prior_faction = self._prior_faction("f2", "ALLIED")
        fu = self._faction_update("f1", "f2", "ALLIED")
        events = EventExtractor.extract(
            _state({1: entity}, factions={"f1": prior_faction}),
            _state({1: entity}, factions={"f1": prior_faction}),
            _update(1, faction_updates=[fu]), ObservabilityMode.NORMAL,
        )
        assert "alliance_proposed" not in _types(events)


# ── resource_seized ────────────────────────────────────────────────────────────

class TestResourceSeized:
    def _faction_update_seize(self, faction_id: str, tension_delta: float = 0.5,
                              territory_add=None):
        fu = MagicMock()
        fu.faction_id = faction_id
        fu.diplomatic_relations_set = {}
        fu.territory_add = territory_add if territory_add is not None else ["region_north"]
        fu.tension_delta = tension_delta
        return fu

    def test_fires_on_territory_add_with_positive_tension(self):
        entity = _entity()
        fu = self._faction_update_seize("f1", tension_delta=0.5)
        events = EventExtractor.extract(
            _state({1: entity}), _state({1: entity}),
            _update(1, faction_updates=[fu]), ObservabilityMode.NORMAL,
        )
        assert "resource_seized" in _types(events)

    def test_not_fired_without_tension(self):
        entity = _entity()
        fu = self._faction_update_seize("f1", tension_delta=0.0)
        events = EventExtractor.extract(
            _state({1: entity}), _state({1: entity}),
            _update(1, faction_updates=[fu]), ObservabilityMode.NORMAL,
        )
        assert "resource_seized" not in _types(events)

    def test_not_fired_without_territory_add(self):
        entity = _entity()
        fu = self._faction_update_seize("f1", tension_delta=0.5, territory_add=[])
        events = EventExtractor.extract(
            _state({1: entity}), _state({1: entity}),
            _update(1, faction_updates=[fu]), ObservabilityMode.NORMAL,
        )
        assert "resource_seized" not in _types(events)
