"""Unit tests for TCK-20260806-PUSH-SHAPER-REGISTRY-PROGRESSION.

Tests the apply-layer (push-based) ProgressionShaper: XP/level/skill/trait/AP events derived from
prior_state + update alone, plus progression_plateau_detected's cross-tick shaper-local state. See
stored_artifacts/TCK-20260806-PUSH-SHAPER-REGISTRY-PROGRESSION/investigation.md's "Key finding" for
the any-update-vs-identity-update gating fix this file's plateau tests specifically exercise.
"""
from __future__ import annotations
from unittest.mock import MagicMock

import pytest

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import _XP_PLATEAU_TICKS
from src.observability.event_shapers import ProgressionShaper, PHASE2_SHAPER_REGISTRY


def _identity(evolution_level=1, evolution_points=0, learned_skills=None):
    i = MagicMock()
    i.evolution_level = evolution_level
    i.evolution_points = evolution_points
    i.learned_skills = learned_skills or set()
    return i


def _entity(identity=None, kind="goblin"):
    e = MagicMock()
    e.identity = identity or _identity()
    e.kind = kind
    return e


def _prior_state(entities: dict, tick: int = 100):
    s = MagicMock()
    s.tick = tick
    s.entities = entities
    s.feature_flags = {}
    return s


def _identity_update(evolution_points_delta=0, evolution_level_set=None,
                      learned_skills=None, traits_add=None, breakthroughs_add=None,
                      unspent_ap_delta=0):
    u = MagicMock()
    u.evolution_points_delta = evolution_points_delta
    u.evolution_level_set = evolution_level_set
    u.learned_skills = learned_skills or []
    u.traits_add = traits_add or []
    u.breakthroughs_add = breakthroughs_add or []
    u.unspent_ap_delta = unspent_ap_delta
    return u


def _entity_update(identity=None, kind_set="goblin"):
    u = MagicMock()
    u.identity = identity
    u.combat = None
    u.intent_results = []
    u.property_updates = {}
    u.self_model_bundle_set = None
    u.strategic = None
    u.kind_set = kind_set
    return u


def _update(entity_updates: dict | None = None):
    u = MagicMock()
    u.entity_updates = entity_updates or {}
    return u


def _types(events) -> list[str]:
    return [e.event_type for e in events]


@pytest.fixture(autouse=True)
def _reset_shaper_state():
    ProgressionShaper.reset_run_state()
    yield
    ProgressionShaper.reset_run_state()


def test_phase2_registry_contains_progression_shaper():
    assert "progression" in PHASE2_SHAPER_REGISTRY
    assert any(isinstance(s, ProgressionShaper) for s in PHASE2_SHAPER_REGISTRY["progression"])


# ── Direct field-read events ────────────────────────────────────────────────

def test_xp_granted():
    prior = _prior_state({1: _entity(_identity(evolution_points=100))})
    upd = _update({1: _entity_update(_identity_update(evolution_points_delta=25))})
    events = ProgressionShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "xp_granted")
    assert ev.payload["amount"] == 25


def test_xp_granted_not_emitted_when_zero_or_negative():
    prior = _prior_state({1: _entity(_identity())})
    upd = _update({1: _entity_update(_identity_update(evolution_points_delta=0))})
    events = ProgressionShaper().shape(prior, upd, tick=10)
    assert "xp_granted" not in _types(events)


def test_level_up():
    prior = _prior_state({1: _entity(_identity(evolution_level=2))})
    upd = _update({1: _entity_update(_identity_update(evolution_level_set=3))})
    events = ProgressionShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "level_up")
    assert ev.payload["new_level"] == 3


def test_level_up_not_emitted_when_not_increased():
    prior = _prior_state({1: _entity(_identity(evolution_level=3))})
    upd = _update({1: _entity_update(_identity_update(evolution_level_set=3))})
    events = ProgressionShaper().shape(prior, upd, tick=10)
    assert "level_up" not in _types(events)


def test_entity_evolved():
    prior = _prior_state({1: _entity(kind="goblin")})
    upd = _update({1: _entity_update(kind_set="goblin_warrior")})
    events = ProgressionShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "entity_evolved")
    assert ev.payload == {"previous_kind": "goblin", "new_kind": "goblin_warrior"}


def test_entity_evolved_not_emitted_when_kind_unchanged():
    """EvolutionSystem always writes kind_set (unchanged when the entity did not evolve this
    tick) -- a bare non-None check would false-fire on every progression tick."""
    prior = _prior_state({1: _entity(kind="goblin")})
    upd = _update({1: _entity_update(kind_set="goblin")})
    events = ProgressionShaper().shape(prior, upd, tick=10)
    assert "entity_evolved" not in _types(events)


def test_skill_unlocked():
    prior = _prior_state({1: _entity(_identity())})
    upd = _update({1: _entity_update(_identity_update(learned_skills=["fireball"]))})
    events = ProgressionShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "skill_unlocked")
    assert ev.payload["skill_id"] == "fireball"


def test_trait_expressed():
    prior = _prior_state({1: _entity(_identity())})
    upd = _update({1: _entity_update(_identity_update(traits_add=["brave"]))})
    events = ProgressionShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "trait_expressed")
    assert ev.payload["trait_id"] == "brave"


def test_pillar_trait_unlocked():
    prior = _prior_state({1: _entity(_identity())})
    upd = _update({1: _entity_update(_identity_update(breakthroughs_add=["combat_mastery"]))})
    events = ProgressionShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "pillar_trait_unlocked")
    assert ev.payload["trait_id"] == "combat_mastery"


def test_progression_conversion_applied():
    prior = _prior_state({1: _entity(_identity())})
    upd = _update({1: _entity_update(_identity_update(unspent_ap_delta=-3))})
    events = ProgressionShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "progression_conversion_applied")
    assert ev.payload["ap_spent"] == 3


def test_progression_conversion_not_emitted_on_positive_delta():
    prior = _prior_state({1: _entity(_identity())})
    upd = _update({1: _entity_update(_identity_update(unspent_ap_delta=2))})
    events = ProgressionShaper().shape(prior, upd, tick=10)
    assert "progression_conversion_applied" not in _types(events)


def test_no_identity_update_produces_no_direct_field_events():
    prior = _prior_state({1: _entity(_identity())})
    upd = _update({1: _entity_update(identity=None)})
    events = ProgressionShaper().shape(prior, upd, tick=10)
    assert not any(e.event_type in (
        "xp_granted", "level_up", "skill_unlocked", "trait_expressed",
        "pillar_trait_unlocked", "progression_conversion_applied",
    ) for e in events)


def test_no_events_when_prior_entity_missing():
    prior = _prior_state({})
    upd = _update({1: _entity_update(_identity_update(evolution_points_delta=10))})
    events = ProgressionShaper().shape(prior, upd, tick=10)
    assert events == []


# ── progression_plateau_detected: cross-tick, any-update gating ───────────

def test_plateau_xp_rate_zero_fires_without_identity_update():
    """Regression test for the real bug found via kernel verification: plateau detection must
    run even when THIS tick's update has no identity sub-update at all (id_upd=None) — matching
    event_extractor.py's own dirty_entity_ids gate (any update, not identity-specific)."""
    prior = _prior_state({1: _entity(_identity(evolution_points=50))}, tick=0)
    # No identity update this tick — entity is dirty for some other reason (e.g. routing).
    upd = _update({1: _entity_update(identity=None)})
    tick = _XP_PLATEAU_TICKS + 1
    events = ProgressionShaper().shape(prior, upd, tick=tick)
    ev = next(e for e in events if e.event_type == "progression_plateau_detected")
    assert ev.payload["type"] == "xp_rate_zero"


def test_plateau_not_fired_before_threshold():
    prior = _prior_state({1: _entity(_identity(evolution_points=50))}, tick=0)
    upd = _update({1: _entity_update(identity=None)})
    events = ProgressionShaper().shape(prior, upd, tick=5)
    assert "progression_plateau_detected" not in _types(events)


def test_plateau_not_repeated_for_same_entity():
    prior = _prior_state({1: _entity(_identity(evolution_points=50))}, tick=0)
    upd = _update({1: _entity_update(identity=None)})
    tick = _XP_PLATEAU_TICKS + 1
    ProgressionShaper().shape(prior, upd, tick=tick)
    events2 = ProgressionShaper().shape(prior, upd, tick=tick + 1)
    assert "progression_plateau_detected" not in _types(events2)


def test_plateau_skill_silence_at_level_5_no_skills():
    prior = _prior_state({1: _entity(_identity(evolution_level=5, evolution_points=50))}, tick=0)
    upd = _update({1: _entity_update(identity=None)})
    events = ProgressionShaper().shape(prior, upd, tick=1)
    ev = next(e for e in events if e.event_type == "progression_plateau_detected")
    assert ev.payload["type"] == "skill_silence"
    assert ev.payload["level"] == 5


def test_plateau_skill_silence_not_fired_with_existing_skills():
    prior = _prior_state({1: _entity(_identity(
        evolution_level=5, evolution_points=50, learned_skills={"fireball"},
    ))}, tick=0)
    upd = _update({1: _entity_update(identity=None)})
    events = ProgressionShaper().shape(prior, upd, tick=1)
    assert "progression_plateau_detected" not in _types(events)


def test_plateau_resets_tracking_on_xp_change():
    prior = _prior_state({1: _entity(_identity(evolution_points=50))}, tick=0)
    upd_with_xp = _update({1: _entity_update(_identity_update(evolution_points_delta=5))})
    ProgressionShaper().shape(prior, upd_with_xp, tick=_XP_PLATEAU_TICKS)
    # XP changed at tick _XP_PLATEAU_TICKS, so plateau shouldn't fire again until another
    # _XP_PLATEAU_TICKS have passed from THAT tick, not the original tick=0.
    upd_no_xp = _update({1: _entity_update(identity=None)})
    events = ProgressionShaper().shape(prior, upd_no_xp, tick=_XP_PLATEAU_TICKS + 5)
    assert "progression_plateau_detected" not in _types(events)
