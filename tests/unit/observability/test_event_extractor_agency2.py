"""Unit tests for EventExtractor AGENCY event emission — pass 2 (TCK-20260701-SIMQ-EMIT-AGENCY2).

Tests for: defer_with_reason, commitment_abandoned, rejection_cascade_tick,
route_family_first_use. Also includes anti-drift guards for property name coupling,
reset mechanism, category string values, and threshold alignment.
"""
from __future__ import annotations
import inspect
from unittest.mock import MagicMock

import pytest

from src.core.strategic import ProjectStatus
from src.domains.commitment.abandonment import AbandonmentCategory
from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor
from src.observability.events import QuestEvent
from src.systems.strategic_systems.intelligence import _MAX_CONSECUTIVE_REJECTIONS


# ── Minimal mock builders ─────────────────────────────────────────────────────

def _entity(eid: int = 1, hp: int = 80, max_hp: int = 100):
    e = MagicMock()
    e.id = eid
    e.kind = "hero"
    e.combat = MagicMock()
    e.combat.hp = hp
    e.combat.max_hp = max_hp
    e.combat.alive = True
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
    e.strategic.contracts = {}
    e.social = MagicMock()
    e.social.public_reputation = 0.0
    e.group_id = None
    return e


def _entity_with_project(eid: int, status: ProjectStatus, hp: int = 80, max_hp: int = 100):
    """Entity with a single project at the given status."""
    e = _entity(eid, hp, max_hp)
    proj = MagicMock()
    proj.status = status
    e.strategic.projects = {"proj_x": proj}
    return e


def _state(entities: dict):
    s = MagicMock()
    s.tick = 5
    s.entities = entities
    s.resource_nodes = {}
    return s


def _update_with_defer(eid: int, reason: str = "no_viable_route"):
    """EntityUpdate carrying a defer signal (what phase.py writes on DEFER_WITH_REASON)."""
    eu = MagicMock()
    eu.property_updates = {"last_defer_reason": reason, "last_defer_tick": 5}
    eu.combat_upd = None
    eu.combat = None
    eu.self_model_bundle_set = None
    eu.intent_results = []
    u = MagicMock()
    u.entity_updates = {eid: eu}
    u.world_updates = {}
    u.faction_updates = []
    u.world_events_add = []
    u.entities_add = []
    u.last_calamity_tick_set = None
    return u


def _update_with_routing(eid: int, family: str):
    eu = MagicMock()
    eu.property_updates = {"last_routing_family": family, "last_routing_tick": 5}
    eu.combat_upd = None
    eu.combat = None
    eu.self_model_bundle_set = None
    eu.intent_results = []
    u = MagicMock()
    u.entity_updates = {eid: eu}
    u.world_updates = {}
    u.faction_updates = []
    u.world_events_add = []
    u.entities_add = []
    u.last_calamity_tick_set = None
    return u


def _update_no_props(eid: int):
    eu = MagicMock()
    eu.property_updates = {}
    eu.combat_upd = None
    eu.combat = None
    eu.self_model_bundle_set = None
    eu.intent_results = []
    u = MagicMock()
    u.entity_updates = {eid: eu}
    u.world_updates = {}
    u.faction_updates = []
    u.world_events_add = []
    u.entities_add = []
    u.last_calamity_tick_set = None
    return u


def _update_with_rejections(entity_ids: list[int], rejections_per_entity: int,
                             reason: str = "INSUFFICIENT_CAPACITY"):
    """Build an update where each entity has `rejections_per_entity` rejected intent_results."""
    entity_updates = {}
    for eid in entity_ids:
        eu = MagicMock()
        eu.property_updates = {}
        eu.combat_upd = None
        eu.combat = None
        eu.self_model_bundle_set = None
        irs = []
        for _ in range(rejections_per_entity):
            ir = MagicMock()
            ir.accepted = False
            ir.reason = reason
            irs.append(ir)
        eu.intent_results = irs
        entity_updates[eid] = eu

    u = MagicMock()
    u.entity_updates = entity_updates
    u.world_updates = {}
    u.faction_updates = []
    u.world_events_add = []
    u.entities_add = []
    u.last_calamity_tick_set = None
    return u


def _update_with_mixed_rejections(entity_ids_a: list[int], entity_ids_b: list[int],
                                   reason_a: str, reason_b: str):
    """Two groups with different rejection reasons."""
    entity_updates = {}
    for eid in entity_ids_a:
        eu = MagicMock()
        eu.property_updates = {}
        eu.combat_upd = None
        eu.combat = None
        eu.self_model_bundle_set = None
        ir = MagicMock()
        ir.accepted = False
        ir.reason = reason_a
        eu.intent_results = [ir, ir]
        entity_updates[eid] = eu
    for eid in entity_ids_b:
        eu = MagicMock()
        eu.property_updates = {}
        eu.combat_upd = None
        eu.combat = None
        eu.self_model_bundle_set = None
        ir = MagicMock()
        ir.accepted = False
        ir.reason = reason_b
        eu.intent_results = [ir]
        entity_updates[eid] = eu
    u = MagicMock()
    u.entity_updates = entity_updates
    u.world_updates = {}
    u.faction_updates = []
    u.world_events_add = []
    u.entities_add = []
    u.last_calamity_tick_set = None
    return u


def _update_all_accepted(entity_ids: list[int]):
    entity_updates = {}
    for eid in entity_ids:
        eu = MagicMock()
        eu.property_updates = {}
        eu.combat_upd = None
        eu.combat = None
        eu.self_model_bundle_set = None
        ir = MagicMock()
        ir.accepted = True
        ir.reason = "ok"
        eu.intent_results = [ir]
        entity_updates[eid] = eu
    u = MagicMock()
    u.entity_updates = entity_updates
    u.world_updates = {}
    u.faction_updates = []
    u.world_events_add = []
    u.entities_add = []
    u.last_calamity_tick_set = None
    return u


def _empty_update():
    u = MagicMock()
    u.entity_updates = {}
    u.world_updates = {}
    u.faction_updates = []
    u.world_events_add = []
    u.entities_add = []
    u.last_calamity_tick_set = None
    return u


def _types(events) -> list[str]:
    return [e.event_type for e in events]


# ── Group A: defer_with_reason ─────────────────────────────────────────────────

class TestDeferWithReason:
    def test_defer_with_reason_emitted_when_property_set(self):
        e = _entity()
        state = _state({1: e})
        events = EventExtractor.extract(state, state, _update_with_defer(1, "no_viable_route"), ObservabilityMode.NORMAL)
        assert "defer_with_reason" in _types(events)
        ev = next(x for x in events if x.event_type == "defer_with_reason")
        assert ev.payload["reason"] == "no_viable_route"

    def test_defer_with_reason_not_emitted_without_defer_property(self):
        e = _entity()
        state = _state({1: e})
        events = EventExtractor.extract(state, state, _update_no_props(1), ObservabilityMode.NORMAL)
        assert "defer_with_reason" not in _types(events)

    def test_defer_with_reason_not_emitted_when_routing_present(self):
        e = _entity()
        state = _state({1: e})
        events = EventExtractor.extract(state, state, _update_with_routing(1, "recover"), ObservabilityMode.NORMAL)
        assert "defer_with_reason" not in _types(events)

    def test_defer_with_reason_payload_structure(self):
        e = _entity()
        state = _state({1: e})
        events = EventExtractor.extract(state, state, _update_with_defer(1, "all_blocked"), ObservabilityMode.NORMAL)
        ev = next(x for x in events if x.event_type == "defer_with_reason")
        assert "entity_id" in ev.payload
        assert "reason" in ev.payload
        assert "tick" in ev.payload
        assert ev.event_category == "strategy"


# ── Group B: commitment_abandoned ─────────────────────────────────────────────

def _project_state_update(eid: int, prior_status: ProjectStatus, current_status: ProjectStatus,
                           hp: int = 80, max_hp: int = 100):
    """Build prior and current states with a project transitioning between statuses."""
    prior_proj = MagicMock()
    prior_proj.status = prior_status

    curr_proj = MagicMock()
    curr_proj.status = current_status

    prior_e = _entity(eid, hp, max_hp)
    prior_e.strategic.projects = {"proj_x": prior_proj}

    curr_e = _entity(eid, hp, max_hp)
    curr_e.strategic.projects = {"proj_x": curr_proj}

    prior_state = _state({eid: prior_e})
    curr_state = _state({eid: curr_e})

    u = _update_no_props(eid)
    return prior_state, curr_state, u


class TestCommitmentAbandoned:
    def test_commitment_abandoned_emitted_on_abandoned_project_not_survival(self):
        prior_state, curr_state, u = _project_state_update(
            1, ProjectStatus.ACTIVE, ProjectStatus.ABANDONED, hp=80, max_hp=100
        )
        events = EventExtractor.extract(prior_state, curr_state, u, ObservabilityMode.NORMAL)
        assert "commitment_abandoned" in _types(events)
        ev = next(x for x in events if x.event_type == "commitment_abandoned")
        assert ev.payload["category"] == "voluntary_quit"

    def test_commitment_abandoned_not_emitted_when_survival_category(self):
        prior_state, curr_state, u = _project_state_update(
            1, ProjectStatus.ACTIVE, ProjectStatus.ABANDONED, hp=15, max_hp=100
        )
        events = EventExtractor.extract(prior_state, curr_state, u, ObservabilityMode.NORMAL)
        assert "commitment_abandoned" not in _types(events)

    def test_commitment_abandoned_not_emitted_for_non_abandonment_transitions(self):
        prior_state, curr_state, u = _project_state_update(
            1, ProjectStatus.ACTIVE, ProjectStatus.COMPLETED, hp=80, max_hp=100
        )
        events = EventExtractor.extract(prior_state, curr_state, u, ObservabilityMode.NORMAL)
        assert "commitment_abandoned" not in _types(events)

    def test_commitment_abandoned_payload_uses_typed_category(self):
        prior_state, curr_state, u = _project_state_update(
            1, ProjectStatus.ACTIVE, ProjectStatus.ABANDONED, hp=50, max_hp=100
        )
        events = EventExtractor.extract(prior_state, curr_state, u, ObservabilityMode.NORMAL)
        ev = next(x for x in events if x.event_type == "commitment_abandoned")
        assert isinstance(ev.payload["category"], str)
        assert ev.payload["category"] in {"voluntary_quit", "greedy_desertion"}
        assert "entity_id" in ev.payload
        assert "tick" in ev.payload

    def test_commitment_abandoned_and_quest_event_both_emitted(self):
        prior_state, curr_state, u = _project_state_update(
            1, ProjectStatus.ACTIVE, ProjectStatus.ABANDONED, hp=80, max_hp=100
        )
        events = EventExtractor.extract(prior_state, curr_state, u, ObservabilityMode.NORMAL)
        types = _types(events)
        assert "commitment_abandoned" in types
        quest_events = [e for e in events if isinstance(e, QuestEvent)]
        assert len(quest_events) >= 1


# ── Group C: rejection_cascade_tick ──────────────────────────────────────────

class TestRejectionCascadeTick:
    def test_rejection_cascade_tick_emitted_above_threshold(self):
        entity_ids = list(range(1, 26))  # 25 entities, each with 1 rejection = 25 total
        state = _state({eid: _entity(eid) for eid in entity_ids})
        u = _update_with_rejections(entity_ids, 1)
        events = EventExtractor.extract(state, state, u, ObservabilityMode.NORMAL)
        cascade_events = [e for e in events if e.event_type == "rejection_cascade_tick"]
        assert len(cascade_events) == 1
        assert cascade_events[0].payload["count"] >= 20

    def test_rejection_cascade_tick_not_emitted_below_threshold(self):
        entity_ids = list(range(1, 6))  # 5 entities, 5 total < 20
        state = _state({eid: _entity(eid) for eid in entity_ids})
        u = _update_with_rejections(entity_ids, 1)
        events = EventExtractor.extract(state, state, u, ObservabilityMode.NORMAL)
        assert "rejection_cascade_tick" not in _types(events)

    def test_rejection_cascade_tick_fires_at_most_once_per_tick(self):
        entity_ids = list(range(1, 101))  # 100 entities * 3 rejections = 300 total
        state = _state({eid: _entity(eid) for eid in entity_ids})
        u = _update_with_rejections(entity_ids, 3)
        events = EventExtractor.extract(state, state, u, ObservabilityMode.NORMAL)
        cascade_events = [e for e in events if e.event_type == "rejection_cascade_tick"]
        assert len(cascade_events) == 1

    def test_rejection_cascade_tick_payload_has_dominant_failure_reason(self):
        # 20 entities: each 2 rejections with reason_a (40 total reason_a)
        # 10 entities: each 1 rejection with reason_b (10 total reason_b)
        entity_ids_a = list(range(1, 21))
        entity_ids_b = list(range(21, 31))
        state = _state({eid: _entity(eid) for eid in entity_ids_a + entity_ids_b})
        u = _update_with_mixed_rejections(
            entity_ids_a, entity_ids_b,
            "INSUFFICIENT_CAPACITY", "OUT_OF_STOCK"
        )
        events = EventExtractor.extract(state, state, u, ObservabilityMode.NORMAL)
        ev = next(e for e in events if e.event_type == "rejection_cascade_tick")
        assert ev.payload["dominant_failure_reason"] == "INSUFFICIENT_CAPACITY"

    def test_rejection_cascade_tick_not_emitted_when_all_accepted(self):
        entity_ids = list(range(1, 31))
        state = _state({eid: _entity(eid) for eid in entity_ids})
        u = _update_all_accepted(entity_ids)
        events = EventExtractor.extract(state, state, u, ObservabilityMode.NORMAL)
        assert "rejection_cascade_tick" not in _types(events)


# ── Group D: route_family_first_use ──────────────────────────────────────────

class TestRouteFamilyFirstUse:
    def setup_method(self):
        EventExtractor.reset_run_state()

    def test_route_family_first_use_fires_on_first_family(self):
        e = _entity(1)
        state = _state({1: e})
        events = EventExtractor.extract(state, state, _update_with_routing(1, "gather_resource"), ObservabilityMode.NORMAL)
        first_use = [ev for ev in events if ev.event_type == "route_family_first_use"]
        assert len(first_use) == 1
        assert first_use[0].payload["family"] == "gather_resource"
        assert first_use[0].payload["entity_id"] == 1

    def test_route_family_first_use_not_fires_on_repeat_family(self):
        e = _entity(1)
        state = _state({1: e})
        events1 = EventExtractor.extract(state, state, _update_with_routing(1, "gather_resource"), ObservabilityMode.NORMAL)
        events2 = EventExtractor.extract(state, state, _update_with_routing(1, "gather_resource"), ObservabilityMode.NORMAL)
        assert any(ev.event_type == "route_family_first_use" for ev in events1)
        assert not any(ev.event_type == "route_family_first_use" for ev in events2)

    def test_route_family_first_use_fires_for_each_new_family(self):
        e = _entity(1)
        state = _state({1: e})
        events1 = EventExtractor.extract(state, state, _update_with_routing(1, "gather_resource"), ObservabilityMode.NORMAL)
        events2 = EventExtractor.extract(state, state, _update_with_routing(1, "recover"), ObservabilityMode.NORMAL)
        assert any(ev.event_type == "route_family_first_use" for ev in events1)
        assert any(ev.event_type == "route_family_first_use" for ev in events2)

    def test_route_family_first_use_independent_per_entity(self):
        e1 = _entity(1)
        e2 = _entity(2)
        state = _state({1: e1, 2: e2})
        events1 = EventExtractor.extract(state, state, _update_with_routing(1, "gather_resource"), ObservabilityMode.NORMAL)
        events2 = EventExtractor.extract(state, state, _update_with_routing(2, "gather_resource"), ObservabilityMode.NORMAL)
        assert any(ev.event_type == "route_family_first_use" and ev.entity_id == 1 for ev in events1)
        assert any(ev.event_type == "route_family_first_use" and ev.entity_id == 2 for ev in events2)

    def test_route_family_first_use_reset_clears_seen_state(self):
        e = _entity(1)
        state = _state({1: e})
        EventExtractor.extract(state, state, _update_with_routing(1, "gather_resource"), ObservabilityMode.NORMAL)
        EventExtractor.reset_run_state()
        events = EventExtractor.extract(state, state, _update_with_routing(1, "gather_resource"), ObservabilityMode.NORMAL)
        assert any(ev.event_type == "route_family_first_use" for ev in events)


# ── Anti-drift guards ─────────────────────────────────────────────────────────

class TestAntiDriftGuards:
    def test_defer_property_name_constant_matches_phase_and_extractor(self):
        """Guard 1: "last_defer_reason" string must appear in both phase.py and event_extractor.py.
        If either side renames it, event emission silently breaks."""
        from src.domains.adventure import phase as phase_mod
        source = inspect.getsource(phase_mod.AdventureDecisionPhase.apply)
        assert "last_defer_reason" in source
        extractor_source = inspect.getsource(EventExtractor.extract)
        assert "last_defer_reason" in extractor_source

    def test_event_extractor_has_reset_run_state(self):
        """Guard 2: reset_run_state() classmethod must exist and be callable."""
        assert hasattr(EventExtractor, "reset_run_state")
        EventExtractor.reset_run_state()

    def test_commitment_abandoned_and_quest_event_coexist_on_abandoned_transition(self):
        """Guard 3: ACTIVE→ABANDONED must produce both commitment_abandoned and a QuestEvent.
        Ensures commitment_abandoned is additive, not a replacement."""
        prior_state, curr_state, u = _project_state_update(
            1, ProjectStatus.ACTIVE, ProjectStatus.ABANDONED, hp=80, max_hp=100
        )
        events = EventExtractor.extract(prior_state, curr_state, u, ObservabilityMode.NORMAL)
        assert "commitment_abandoned" in _types(events)
        quest_events = [e for e in events if isinstance(e, QuestEvent)]
        assert len(quest_events) >= 1

    def test_abandonment_category_string_values(self):
        """Guard 4: AbandonmentCategory string values must match expected payload strings."""
        assert AbandonmentCategory.SURVIVAL.value == "survival"
        assert AbandonmentCategory.VOLUNTARY_QUIT.value == "voluntary_quit"
        assert AbandonmentCategory.GREEDY_DESERTION.value == "greedy_desertion"

    def test_rejection_cascade_emitter_uses_same_threshold_as_intelligence(self):
        """Guard 5: _MAX_CONSECUTIVE_REJECTIONS imported from intelligence.py == 20."""
        assert _MAX_CONSECUTIVE_REJECTIONS == 20
