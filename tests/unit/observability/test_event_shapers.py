"""Unit tests for TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT.

Tests the apply-layer (push-based) CombatShaper: derives events from prior_state + update alone,
no current_state diffing. See src/observability/event_shapers.py's module docstring and
stored_artifacts/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC/investigation.md's "Design
refinement" section for the architecture this exercises.
"""
from __future__ import annotations
from unittest.mock import MagicMock

from src.observability.config import ObservabilityMode
from src.observability.event_shapers import (
    CombatShaper, SHAPER_REGISTRY, run_shadow_shapers, EventShaper,
)


# ── Minimal mock builders ─────────────────────────────────────────────────────

def _entity(eid: int = 1, hp: int = 100, max_hp: int = 100, active: bool = True, kind: str = "hero"):
    e = MagicMock()
    e.id = eid
    e.kind = kind
    e.combat = MagicMock(hp=hp, max_hp=max_hp)
    e.lifecycle = MagicMock(active=active)
    return e


def _prior_state(entities: dict, tick: int = 10):
    s = MagicMock()
    s.tick = tick
    s.entities = entities
    return s


def _real_combat_upd(attacker_id: int = 99, outcome_kind: str = "SURVIVE", hp_delta: int = -20,
                      alive_set=None):
    return MagicMock(attacker_id=attacker_id, outcome_kind=outcome_kind, hp_delta=hp_delta,
                      alive_set=alive_set)


def _update(entity_updates: dict | None = None):
    u = MagicMock()
    u.entity_updates = entity_updates or {}
    return u


def _types(events) -> list[str]:
    return [e.event_type for e in events]


# ── Registry mechanism (generic) ────────────────────────────────────────────

def test_registry_contains_combat_shaper():
    assert "combat" in SHAPER_REGISTRY
    assert any(isinstance(s, CombatShaper) for s in SHAPER_REGISTRY["combat"])


def test_run_shadow_shapers_invokes_all_registered_shapers():
    dummy_events = [MagicMock(event_type="dummy_event")]

    class DummyShaper:
        def shape(self, prior_state, update, tick, mode=ObservabilityMode.LIGHT):
            return dummy_events

    original = SHAPER_REGISTRY.get("_test_dummy")
    SHAPER_REGISTRY["_test_dummy"] = [DummyShaper()]
    try:
        events = run_shadow_shapers(_prior_state({}), _update(), tick=10)
        assert dummy_events[0] in events
    finally:
        if original is None:
            del SHAPER_REGISTRY["_test_dummy"]
        else:
            SHAPER_REGISTRY["_test_dummy"] = original


# ── CombatShaper: core 4 events (NORMAL mode — no volumization filtering) ──

def test_combat_damage_and_initiated_for_real_combat():
    prior = _entity(hp=100, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=42, hp_delta=-20))})
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10, mode=ObservabilityMode.NORMAL)
    types = _types(events)
    assert "combat_damage" in types
    assert "combat_initiated" in types
    dmg = next(e for e in events if e.event_type == "combat_damage")
    assert dmg.payload["attacker_id"] == 42
    assert dmg.payload["damage"] == 20


def test_combat_initiated_not_emitted_when_already_damaged():
    prior = _entity(hp=80, max_hp=100)  # already below max
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=42, hp_delta=-10))})
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10, mode=ObservabilityMode.NORMAL)
    assert "combat_initiated" not in _types(events)


# ── CombatShaper: volumization rule (the fix TCK-20260806-PUSH-SHADOW-VALIDATION-PERF found
# missing — a real, frequent divergence in sustained-combat sequences) ─────

def test_combat_damage_suppressed_in_light_mode_when_not_lethal():
    prior = _entity(hp=100, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=42, hp_delta=-20, alive_set=True))})
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10, mode=ObservabilityMode.LIGHT)
    assert "combat_damage" not in _types(events)


def test_combat_damage_not_suppressed_in_light_mode_when_lethal():
    prior = _entity(hp=10, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=42, hp_delta=-10, alive_set=False))})
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10, mode=ObservabilityMode.LIGHT)
    assert "combat_damage" in _types(events)


def test_combat_damage_not_suppressed_in_normal_mode_even_when_not_lethal():
    prior = _entity(hp=100, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=42, hp_delta=-20, alive_set=True))})
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10, mode=ObservabilityMode.NORMAL)
    assert "combat_damage" in _types(events)


def test_combat_damage_default_mode_is_light():
    """Default mode (no explicit arg) must match event_extractor.py's own default (LIGHT) —
    confirms the shaper's default doesn't silently diverge from the old path's default."""
    prior = _entity(hp=100, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=42, hp_delta=-20, alive_set=True))})
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10)
    assert "combat_damage" not in _types(events)


def test_near_death_survival_emitted_when_hp_crosses_threshold():
    prior = _entity(hp=25, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=42, hp_delta=-10))})  # 25->15
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10)
    assert "near_death_survival" in _types(events)
    nd = next(e for e in events if e.event_type == "near_death_survival")
    assert nd.payload["hp"] == 15
    assert nd.payload["max_hp"] == 100


def test_near_death_survival_not_emitted_when_entity_dies():
    prior = _entity(hp=25, max_hp=100, active=True)
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=42, hp_delta=-25, alive_set=False))})
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10)
    assert "near_death_survival" not in _types(events)


def test_entity_killed_emitted_directly_not_combat_kill():
    prior = _entity(hp=10, max_hp=100, active=True)
    upd = _update({1: MagicMock(combat=_real_combat_upd(
        attacker_id=7, hp_delta=-10, alive_set=False, outcome_kind="KILL"))})
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10)
    assert "entity_killed" in _types(events)
    assert "combat_kill" not in _types(events)
    killed = next(e for e in events if e.event_type == "entity_killed")
    assert killed.payload["killer_id"] == 7


def test_entity_killed_not_emitted_for_hazard_death():
    """TCK-20260806-PUSH-SHADOW-VALIDATION-PERF found this real: hazard drain can set
    alive_set=False (combat.alive=False) without lifecycle.active ever transitioning —
    LifecycleSystem.resolve_lifecycle() only flips lifecycle.active on outcome_kind=="KILL",
    never on alive_set alone. entity_killed must not fire for a hazard-caused "death"."""
    prior = _entity(hp=10, max_hp=100, active=True)
    upd = _update({1: MagicMock(combat=_real_combat_upd(
        attacker_id=None, hp_delta=-10, alive_set=False, outcome_kind="HAZARD"))})
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10)
    assert "entity_killed" not in _types(events)


def test_hero_death_unrecorded_emitted_for_hero_kind():
    prior = _entity(hp=10, max_hp=100, active=True, kind="hero")
    upd = _update({1: MagicMock(combat=_real_combat_upd(
        attacker_id=7, hp_delta=-10, alive_set=False, outcome_kind="KILL"))})
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10)
    assert "hero_death_unrecorded" in _types(events)


def test_hero_death_unrecorded_not_emitted_for_non_hero():
    prior = _entity(hp=10, max_hp=100, active=True, kind="goblin")
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=7, hp_delta=-10, alive_set=False))})
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10)
    assert "hero_death_unrecorded" not in _types(events)


# ── Non-combat HP loss exclusion (same collision risks the hotfix ticket found) ─

def test_hazard_damage_produces_hazard_event_not_combat():
    prior = _entity(hp=100, max_hp=100)
    hazard_upd = _real_combat_upd(attacker_id=None, outcome_kind="HAZARD", hp_delta=-15)
    upd = _update({1: MagicMock(combat=hazard_upd)})
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10)
    types = _types(events)
    assert "hazard_drain_applied" in types
    assert "combat_damage" not in types
    assert "combat_initiated" not in types


def test_biological_damage_not_misclassified_as_combat():
    """CombatUpdate's own dataclass default outcome_kind ("SURVIVE") is what biological.py's
    starvation/exhaustion damage relies on — attacker_id=None must exclude it regardless."""
    prior = _entity(hp=100, max_hp=100)
    bio_upd = _real_combat_upd(attacker_id=None, outcome_kind="SURVIVE", hp_delta=-1)
    upd = _update({1: MagicMock(combat=bio_upd)})
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10)
    types = _types(events)
    assert "combat_damage" not in types
    assert "combat_initiated" not in types
    assert "near_death_survival" not in types


def test_no_events_when_entity_update_has_no_combat_field():
    prior = _entity(hp=100, max_hp=100)
    upd = _update({1: MagicMock(combat=None)})
    events = CombatShaper().shape(_prior_state({1: prior}), upd, tick=10)
    assert events == []


def test_no_events_when_entity_not_in_prior_state():
    upd = _update({99: MagicMock(combat=_real_combat_upd())})
    events = CombatShaper().shape(_prior_state({}), upd, tick=10)
    assert events == []


# ── SHADOW-mode inertness ───────────────────────────────────────────────────

def test_run_shadow_shapers_does_not_touch_a_queue():
    """run_shadow_shapers only returns constructed events — it must never reach into any
    delivery mechanism itself. The caller (Kernel._phase_observability) is responsible for
    keeping SHADOW mode non-delivering; this test locks in that the module never imports a
    queue/recorder class to misuse (checked via real imports, not prose in the docstring)."""
    from src.observability import event_shapers
    module_names = set(dir(event_shapers))
    assert "BoundedObservabilityQueue" not in module_names
    assert "EventRecorder" not in module_names
