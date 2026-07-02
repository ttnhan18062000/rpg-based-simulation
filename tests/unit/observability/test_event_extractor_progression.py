"""Unit tests for EventExtractor PROGRESSION event emission (TCK-20260701-SIMQ-EMIT-PROGRESSION).

Tests for: skill_unlocked, trait_expressed, pillar_trait_unlocked,
progression_conversion_applied, progression_plateau_detected.
"""
from __future__ import annotations
from unittest.mock import MagicMock

import pytest

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor


def _identity(learned_skills=frozenset(), traits=frozenset(),
              active_breakthroughs=frozenset(), unspent_ap: int = 0,
              evolution_points: int = 0, evolution_level: int = 1):
    i = MagicMock()
    i.learned_skills = learned_skills
    i.traits = traits
    i.active_breakthroughs = active_breakthroughs
    i.unspent_ap = unspent_ap
    i.evolution_points = evolution_points
    i.evolution_level = evolution_level
    return i


def _entity(eid: int = 1, identity=None):
    e = MagicMock()
    e.id = eid
    e.kind = "hero"
    e.combat = MagicMock(); e.combat.hp = 100; e.combat.max_hp = 100
    e.lifecycle = MagicMock(); e.lifecycle.active = True
    e.navigation = MagicMock(); e.navigation.position = (0.0, 0.0)
    e.inventory = MagicMock(); e.inventory.gold = 0.0
    e.identity = identity or _identity()
    e.strategic = MagicMock()
    e.strategic.projects = {}
    e.strategic.leads = {}
    e.strategic.current_project_id = None
    e.strategic.concerns = {}
    e.group_id = None
    return e


def _state(entities: dict, tick: int = 10):
    s = MagicMock()
    s.tick = tick
    s.entities = entities
    s.resource_nodes = {}
    s.regions = {}
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


# ── skill_unlocked ─────────────────────────────────────────────────────────────

class TestSkillUnlocked:
    def test_fires_when_new_skill_added(self):
        prior = _entity(identity=_identity(learned_skills=frozenset()))
        curr = _entity(identity=_identity(learned_skills=frozenset({"archery"})))
        events = EventExtractor.extract(_state({1: prior}), _state({1: curr}), _update(1), ObservabilityMode.NORMAL)
        assert "skill_unlocked" in _types(events)

    def test_payload_contains_skill_id(self):
        prior = _entity(identity=_identity(learned_skills=frozenset()))
        curr = _entity(identity=_identity(learned_skills=frozenset({"archery"})))
        events = EventExtractor.extract(_state({1: prior}), _state({1: curr}), _update(1), ObservabilityMode.NORMAL)
        evt = next(e for e in events if e.event_type == "skill_unlocked")
        assert evt.payload["skill_id"] == "archery"

    def test_not_fired_when_skills_unchanged(self):
        skills = frozenset({"archery"})
        entity = _entity(identity=_identity(learned_skills=skills))
        events = EventExtractor.extract(_state({1: entity}), _state({1: entity}), _update(1), ObservabilityMode.NORMAL)
        assert "skill_unlocked" not in _types(events)

    def test_fires_once_per_new_skill(self):
        prior = _entity(identity=_identity(learned_skills=frozenset()))
        curr = _entity(identity=_identity(learned_skills=frozenset({"archery", "smithing"})))
        events = EventExtractor.extract(_state({1: prior}), _state({1: curr}), _update(1), ObservabilityMode.NORMAL)
        unlocked = [e for e in events if e.event_type == "skill_unlocked"]
        assert len(unlocked) == 2


# ── trait_expressed ────────────────────────────────────────────────────────────

class TestTraitExpressed:
    def test_fires_when_new_trait_appears(self):
        prior = _entity(identity=_identity(traits=frozenset()))
        curr = _entity(identity=_identity(traits=frozenset({"brave"})))
        events = EventExtractor.extract(_state({1: prior}), _state({1: curr}), _update(1), ObservabilityMode.NORMAL)
        assert "trait_expressed" in _types(events)

    def test_payload_contains_trait_id(self):
        prior = _entity(identity=_identity(traits=frozenset()))
        curr = _entity(identity=_identity(traits=frozenset({"brave"})))
        events = EventExtractor.extract(_state({1: prior}), _state({1: curr}), _update(1), ObservabilityMode.NORMAL)
        evt = next(e for e in events if e.event_type == "trait_expressed")
        assert evt.payload["trait_id"] == "brave"

    def test_not_fired_when_traits_unchanged(self):
        entity = _entity(identity=_identity(traits=frozenset({"brave"})))
        events = EventExtractor.extract(_state({1: entity}), _state({1: entity}), _update(1), ObservabilityMode.NORMAL)
        assert "trait_expressed" not in _types(events)


# ── pillar_trait_unlocked ──────────────────────────────────────────────────────

class TestPillarTraitUnlocked:
    def test_fires_when_breakthrough_added(self):
        prior = _entity(identity=_identity(active_breakthroughs=frozenset()))
        curr = _entity(identity=_identity(active_breakthroughs=frozenset({"combat_mastery"})))
        events = EventExtractor.extract(_state({1: prior}), _state({1: curr}), _update(1), ObservabilityMode.NORMAL)
        assert "pillar_trait_unlocked" in _types(events)

    def test_payload_contains_trait_id(self):
        prior = _entity(identity=_identity(active_breakthroughs=frozenset()))
        curr = _entity(identity=_identity(active_breakthroughs=frozenset({"combat_mastery"})))
        events = EventExtractor.extract(_state({1: prior}), _state({1: curr}), _update(1), ObservabilityMode.NORMAL)
        evt = next(e for e in events if e.event_type == "pillar_trait_unlocked")
        assert evt.payload["trait_id"] == "combat_mastery"

    def test_not_fired_when_breakthroughs_unchanged(self):
        entity = _entity(identity=_identity(active_breakthroughs=frozenset({"combat_mastery"})))
        events = EventExtractor.extract(_state({1: entity}), _state({1: entity}), _update(1), ObservabilityMode.NORMAL)
        assert "pillar_trait_unlocked" not in _types(events)


# ── progression_conversion_applied ────────────────────────────────────────────

class TestProgressionConversionApplied:
    def test_fires_when_unspent_ap_decreases(self):
        prior = _entity(identity=_identity(unspent_ap=3))
        curr = _entity(identity=_identity(unspent_ap=1))
        events = EventExtractor.extract(_state({1: prior}), _state({1: curr}), _update(1), ObservabilityMode.NORMAL)
        assert "progression_conversion_applied" in _types(events)

    def test_payload_contains_ap_spent(self):
        prior = _entity(identity=_identity(unspent_ap=5))
        curr = _entity(identity=_identity(unspent_ap=2))
        events = EventExtractor.extract(_state({1: prior}), _state({1: curr}), _update(1), ObservabilityMode.NORMAL)
        evt = next(e for e in events if e.event_type == "progression_conversion_applied")
        assert evt.payload["ap_spent"] == 3

    def test_not_fired_when_ap_increases(self):
        prior = _entity(identity=_identity(unspent_ap=1))
        curr = _entity(identity=_identity(unspent_ap=4))
        events = EventExtractor.extract(_state({1: prior}), _state({1: curr}), _update(1), ObservabilityMode.NORMAL)
        assert "progression_conversion_applied" not in _types(events)

    def test_not_fired_when_ap_unchanged(self):
        entity = _entity(identity=_identity(unspent_ap=2))
        events = EventExtractor.extract(_state({1: entity}), _state({1: entity}), _update(1), ObservabilityMode.NORMAL)
        assert "progression_conversion_applied" not in _types(events)


# ── progression_plateau_detected ──────────────────────────────────────────────

class TestProgressionPlateauDetected:
    def test_fires_when_xp_unchanged_for_threshold_ticks(self):
        prior = _entity(identity=_identity(evolution_points=100))
        curr = _entity(identity=_identity(evolution_points=100))
        # tick=60, last_xp_tick not set → age=60 > _XP_PLATEAU_TICKS=50
        events = EventExtractor.extract(
            _state({1: prior}, tick=60),
            _state({1: curr}, tick=60),
            _update(1), ObservabilityMode.NORMAL,
        )
        assert "progression_plateau_detected" in _types(events)

    def test_not_fired_when_xp_recently_changed(self):
        prior = _entity(identity=_identity(evolution_points=90))
        curr = _entity(identity=_identity(evolution_points=100))
        # xp changed → last_xp_tick set to current tick, no plateau
        events = EventExtractor.extract(
            _state({1: prior}, tick=60),
            _state({1: curr}, tick=60),
            _update(1), ObservabilityMode.NORMAL,
        )
        assert "progression_plateau_detected" not in _types(events)

    def test_fires_only_once_per_entity_per_run(self):
        prior = _entity(identity=_identity(evolution_points=100))
        curr = _entity(identity=_identity(evolution_points=100))
        state60 = _state({1: curr}, tick=60)
        update = _update(1)
        evts1 = EventExtractor.extract(_state({1: prior}, tick=60), state60, update, ObservabilityMode.NORMAL)
        evts2 = EventExtractor.extract(state60, state60, update, ObservabilityMode.NORMAL)
        plateau_count = sum(1 for e in evts1 + evts2 if e.event_type == "progression_plateau_detected")
        assert plateau_count == 1
