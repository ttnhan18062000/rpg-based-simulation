"""Unit tests for EventExtractor INFORMATION2 event emission (TCK-20260701-SIMQ-EMIT-INFORMATION2).

Tests for: lead_certainty_updated, belief_stale, paid_info_changed_goal,
decision_diverged_by_belief, decision_divergence_detected.
lead_contradiction_resolved is tested in test_information_seeking.py.
"""
from __future__ import annotations
from unittest.mock import MagicMock

import pytest

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor


def _lead(certainty: str = "VAGUE", discovered_tick: int = 0, kind: str = "location"):
    l = MagicMock()
    l.certainty = MagicMock()
    l.certainty.value = certainty
    l.certainty.__str__ = lambda s: certainty
    l.discovered_tick = discovered_tick
    l.kind = kind
    return l


def _entity(eid: int = 1, leads: dict | None = None,
            current_project_id: str | None = None,
            projects: dict | None = None,
            concerns: dict | None = None):
    e = MagicMock()
    e.id = eid
    e.kind = "hero"
    e.combat = MagicMock(); e.combat.hp = 100; e.combat.max_hp = 100
    e.lifecycle = MagicMock(); e.lifecycle.active = True
    e.navigation = MagicMock(); e.navigation.position = (0.0, 0.0)
    e.inventory = MagicMock(); e.inventory.gold = 0.0
    e.identity = MagicMock()
    e.identity.evolution_points = 0
    e.identity.evolution_level = 1
    e.identity.learned_skills = frozenset()
    e.identity.traits = frozenset()
    e.identity.active_breakthroughs = frozenset()
    e.identity.unspent_ap = 0
    e.strategic = MagicMock()
    e.strategic.projects = projects or {}
    e.strategic.leads = leads or {}
    e.strategic.current_project_id = current_project_id
    e.strategic.concerns = concerns or {}
    e.group_id = None
    return e


def _state(entities: dict, tick: int = 100, resource_nodes: dict | None = None,
           regions: dict | None = None):
    s = MagicMock()
    s.tick = tick
    s.entities = entities
    s.resource_nodes = resource_nodes or {}
    s.regions = regions or {}
    return s


def _update(eid: int):
    eu = MagicMock()
    eu.property_updates = {}
    eu.combat_upd = None
    eu.intent_results = []
    eu.self_model_bundle_set = None
    u = MagicMock()
    u.entity_updates = {eid: eu}
    u.world_updates = {}
    u.last_calamity_tick_set = None
    u.entities_add = []
    u.faction_updates = []
    u.world_events_add = []
    return u


def _types(events) -> list[str]:
    return [e.event_type for e in events]


@pytest.fixture(autouse=True)
def reset_extractor():
    EventExtractor.reset_run_state()
    yield
    EventExtractor.reset_run_state()


# ── lead_certainty_updated ─────────────────────────────────────────────────────

class TestLeadCertaintyUpdated:
    def test_fires_on_certainty_increase(self):
        prior_lead = _lead("VAGUE")
        curr_lead = _lead("APPROXIMATE")
        prior = _entity(leads={"l1": prior_lead})
        curr = _entity(leads={"l1": curr_lead}, current_project_id="p1")
        events = EventExtractor.extract(_state({1: prior}), _state({1: curr}), _update(1), ObservabilityMode.NORMAL)
        types = _types(events)
        assert "lead_certainty_updated" in types

    def test_payload_has_positive_delta_on_increase(self):
        prior_lead = _lead("VAGUE")
        curr_lead = _lead("APPROXIMATE")
        prior = _entity(leads={"l1": prior_lead})
        curr = _entity(leads={"l1": curr_lead})
        events = EventExtractor.extract(_state({1: prior}), _state({1: curr}), _update(1), ObservabilityMode.NORMAL)
        evt = next(e for e in events if e.event_type == "lead_certainty_updated")
        assert evt.payload["certainty_delta"] > 0

    def test_payload_has_negative_delta_on_decrease(self):
        prior_lead = _lead("PRECISE")
        curr_lead = _lead("VAGUE")
        prior = _entity(leads={"l1": prior_lead})
        curr = _entity(leads={"l1": curr_lead})
        events = EventExtractor.extract(_state({1: prior}), _state({1: curr}), _update(1), ObservabilityMode.NORMAL)
        evt = next(e for e in events if e.event_type == "lead_certainty_updated")
        assert evt.payload["certainty_delta"] < 0

    def test_not_fired_when_certainty_unchanged(self):
        lead = _lead("VAGUE")
        entity = _entity(leads={"l1": lead})
        events = EventExtractor.extract(_state({1: entity}), _state({1: entity}), _update(1), ObservabilityMode.NORMAL)
        assert "lead_certainty_updated" not in _types(events)


# ── belief_stale ───────────────────────────────────────────────────────────────

class TestBeliefStale:
    def test_fires_for_old_vague_lead(self):
        lead = _lead("VAGUE", discovered_tick=0)
        entity = _entity(leads={"l1": lead})
        events = EventExtractor.extract(
            _state({1: entity}, tick=100),
            _state({1: entity}, tick=100),
            _update(1), ObservabilityMode.NORMAL,
        )
        assert "belief_stale" in _types(events)

    def test_not_fired_for_recent_lead(self):
        lead = _lead("VAGUE", discovered_tick=90)
        entity = _entity(leads={"l1": lead})
        events = EventExtractor.extract(
            _state({1: entity}, tick=100),
            _state({1: entity}, tick=100),
            _update(1), ObservabilityMode.NORMAL,
        )
        assert "belief_stale" not in _types(events)

    def test_not_fired_for_precise_lead(self):
        lead = _lead("PRECISE", discovered_tick=0)
        entity = _entity(leads={"l1": lead})
        events = EventExtractor.extract(
            _state({1: entity}, tick=100),
            _state({1: entity}, tick=100),
            _update(1), ObservabilityMode.NORMAL,
        )
        assert "belief_stale" not in _types(events)

    def test_fires_only_once_per_lead_per_run(self):
        lead = _lead("VAGUE", discovered_tick=0)
        entity = _entity(leads={"l1": lead})
        state = _state({1: entity}, tick=100)
        update = _update(1)
        evts1 = EventExtractor.extract(state, state, update, ObservabilityMode.NORMAL)
        evts2 = EventExtractor.extract(state, state, update, ObservabilityMode.NORMAL)
        stale_count = sum(1 for e in evts1 + evts2 if e.event_type == "belief_stale")
        assert stale_count == 1


# ── decision_diverged_by_belief ────────────────────────────────────────────────

class TestDecisionDivergedByBelief:
    def test_fires_when_vague_lead_and_non_info_project(self):
        lead = _lead("VAGUE", discovered_tick=0)
        proj = MagicMock(); proj.kind = MagicMock(); proj.kind.value = "harvesting"
        entity = _entity(leads={"l1": lead}, current_project_id="p1",
                         projects={"p1": proj})
        events = EventExtractor.extract(
            _state({1: entity}, tick=10),
            _state({1: entity}, tick=10),
            _update(1), ObservabilityMode.NORMAL,
        )
        assert "decision_diverged_by_belief" in _types(events)

    def test_not_fired_when_no_active_project(self):
        lead = _lead("VAGUE", discovered_tick=0)
        entity = _entity(leads={"l1": lead}, current_project_id=None)
        events = EventExtractor.extract(
            _state({1: entity}, tick=10),
            _state({1: entity}, tick=10),
            _update(1), ObservabilityMode.NORMAL,
        )
        assert "decision_diverged_by_belief" not in _types(events)

    def test_not_fired_for_information_project(self):
        lead = _lead("VAGUE", discovered_tick=0)
        proj = MagicMock(); proj.kind = MagicMock(); proj.kind.value = "information"
        entity = _entity(leads={"l1": lead}, current_project_id="p1",
                         projects={"p1": proj})
        events = EventExtractor.extract(
            _state({1: entity}, tick=10),
            _state({1: entity}, tick=10),
            _update(1), ObservabilityMode.NORMAL,
        )
        assert "decision_diverged_by_belief" not in _types(events)


# ── decision_divergence_detected ───────────────────────────────────────────────

class TestDecisionDivergenceDetected:
    def _concern(self, kind: str = "danger", urgency: float = 0.9):
        c = MagicMock()
        c.kind = MagicMock(); c.kind.value = kind
        c.urgency = urgency
        return c

    def test_fires_when_harvesting_during_danger(self):
        concern = self._concern("danger", 0.9)
        proj = MagicMock(); proj.kind = MagicMock(); proj.kind.value = "harvesting"
        entity = _entity(current_project_id="p1", projects={"p1": proj},
                         concerns={"c1": concern})
        events = EventExtractor.extract(
            _state({1: entity}, tick=10),
            _state({1: entity}, tick=10),
            _update(1), ObservabilityMode.NORMAL,
        )
        assert "decision_divergence_detected" in _types(events)

    def test_not_fired_below_urgency_threshold(self):
        concern = self._concern("danger", 0.5)
        proj = MagicMock(); proj.kind = MagicMock(); proj.kind.value = "harvesting"
        entity = _entity(current_project_id="p1", projects={"p1": proj},
                         concerns={"c1": concern})
        events = EventExtractor.extract(
            _state({1: entity}, tick=10),
            _state({1: entity}, tick=10),
            _update(1), ObservabilityMode.NORMAL,
        )
        assert "decision_divergence_detected" not in _types(events)

    def test_not_fired_for_non_danger_concern(self):
        concern = self._concern("hunger", 0.9)
        proj = MagicMock(); proj.kind = MagicMock(); proj.kind.value = "harvesting"
        entity = _entity(current_project_id="p1", projects={"p1": proj},
                         concerns={"c1": concern})
        events = EventExtractor.extract(
            _state({1: entity}, tick=10),
            _state({1: entity}, tick=10),
            _update(1), ObservabilityMode.NORMAL,
        )
        assert "decision_divergence_detected" not in _types(events)
