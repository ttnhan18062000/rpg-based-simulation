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
    CombatShaper, SHAPER_REGISTRY, run_shadow_shapers, EventShaper, _combat_entity_snapshot,
)


# ── Minimal mock builders ─────────────────────────────────────────────────────

def _entity(eid: int = 1, hp: int = 100, max_hp: int = 100, active: bool = True, kind: str = "hero",
            atk: int = 10, def_stat: int = 5, action_style: int = 0, evolution_level: int = 3,
            role: int | None = 2, faction_id: str = "town_a", race_id: str = "human",
            bravery: float = 0.5, task=None):
    e = MagicMock()
    e.id = eid
    e.kind = kind
    e.combat = MagicMock(hp=hp, max_hp=max_hp, atk=atk, def_stat=def_stat, action_style=action_style)
    e.lifecycle = MagicMock(active=active)
    e.identity = MagicMock(
        evolution_level=evolution_level,
        role=role,
        properties={"faction_id": faction_id, "race_id": race_id},
        personality=MagicMock(bravery=bravery),
    )
    e.task = task
    return e


def _prior_state(entities: dict, tick: int = 10):
    s = MagicMock()
    s.tick = tick
    s.entities = entities
    return s


def _real_combat_upd(attacker_id: int = 99, outcome_kind: str = "SURVIVE", hp_delta: int = -20,
                      alive_set=None, is_opportunity_attack: bool = False):
    return MagicMock(attacker_id=attacker_id, outcome_kind=outcome_kind, hp_delta=hp_delta,
                      alive_set=alive_set, is_opportunity_attack=is_opportunity_attack)


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


# ── _combat_entity_snapshot() (TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY) ────

def test_combat_entity_snapshot_returns_real_fields():
    ent = _entity(hp=42, max_hp=100, atk=15, def_stat=8, action_style=1, evolution_level=4,
                  role=2, faction_id="wolf_pack", race_id="wolf", bravery=0.35)
    snap = _combat_entity_snapshot(ent)
    assert snap["level"] == 4
    assert snap["hp"] == 42
    assert snap["max_hp"] == 100
    assert snap["atk"] == 15
    assert snap["def_stat"] == 8
    assert snap["role"] == "MONSTER"
    assert snap["faction_id"] == "wolf_pack"
    assert snap["race_id"] == "wolf"
    assert snap["bravery"] == 0.35
    assert snap["action_style"] == 1


def test_combat_entity_snapshot_none_entity_returns_none():
    assert _combat_entity_snapshot(None) is None


def test_combat_entity_snapshot_unmapped_role_falls_back_to_str():
    ent = _entity(role=999)
    snap = _combat_entity_snapshot(ent)
    assert snap["role"] == "999"


# ── combat_engagement_started (TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY) ────

def test_combat_engagement_started_fires_alongside_combat_initiated_goal_engage():
    defender = _entity(eid=1, hp=100, max_hp=100)
    attacker = _entity(eid=42, hp=100, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=42, hp_delta=-20,
                                                          is_opportunity_attack=False))})
    events = CombatShaper().shape(_prior_state({1: defender, 42: attacker}), upd, tick=10,
                                   mode=ObservabilityMode.NORMAL)
    types = _types(events)
    assert "combat_engagement_started" in types
    started = next(e for e in events if e.event_type == "combat_engagement_started")
    assert started.payload["trigger_reason"] == "GOAL_ENGAGE"
    assert started.payload["defender_snapshot"] is not None
    assert started.payload["attacker_snapshot"] is not None
    assert started.target_id == 42
    # A deliberate (non-OA) engage is not also a CAUGHT_FLEEING end this tick.
    assert "combat_engagement_ended" not in types


def test_combat_engagement_started_trigger_reason_opportunity_attack():
    defender = _entity(eid=1, hp=100, max_hp=100)
    attacker = _entity(eid=42, hp=100, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=42, hp_delta=-20,
                                                          is_opportunity_attack=True))})
    events = CombatShaper().shape(_prior_state({1: defender, 42: attacker}), upd, tick=10,
                                   mode=ObservabilityMode.NORMAL)
    started = next(e for e in events if e.event_type == "combat_engagement_started")
    assert started.payload["trigger_reason"] == "OPPORTUNITY_ATTACK"


def test_combat_engagement_started_not_emitted_when_already_damaged():
    defender = _entity(eid=1, hp=80, max_hp=100)
    attacker = _entity(eid=42, hp=100, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=42, hp_delta=-10))})
    events = CombatShaper().shape(_prior_state({1: defender, 42: attacker}), upd, tick=10,
                                   mode=ObservabilityMode.NORMAL)
    assert "combat_engagement_started" not in _types(events)


# ── combat_engagement_ended: KILL (TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY) ─

def test_combat_engagement_ended_kill_fires_alongside_entity_killed():
    defender = _entity(eid=1, hp=10, max_hp=100, active=True)
    killer = _entity(eid=7, hp=100, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(
        attacker_id=7, hp_delta=-10, alive_set=False, outcome_kind="KILL"))})
    events = CombatShaper().shape(_prior_state({1: defender, 7: killer}), upd, tick=10)
    types = _types(events)
    assert "entity_killed" in types
    assert "combat_engagement_ended" in types
    ended = next(e for e in events if e.event_type == "combat_engagement_ended")
    assert ended.payload["outcome"] == "KILL"
    assert ended.target_id == 7
    assert ended.payload["defender_snapshot"] is not None
    assert ended.payload["attacker_snapshot"] is not None


def test_combat_resolved_fires_alongside_kill():
    """TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX: combat_resolved (the real, ready
    CombatScorer signal that never had a producer) must fire for the KILL outcome."""
    defender = _entity(eid=1, hp=10, max_hp=100, active=True)
    killer = _entity(eid=7, hp=100, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(
        attacker_id=7, hp_delta=-10, alive_set=False, outcome_kind="KILL"))})
    events = CombatShaper().shape(_prior_state({1: defender, 7: killer}), upd, tick=10)
    resolved = [e for e in events if e.event_type == "combat_resolved"]
    assert len(resolved) == 1
    assert resolved[0].payload["outcome"] == "KILL"
    assert resolved[0].target_id == 7


# ── combat_engagement_ended: CAUGHT_FLEEING ─────────────────────────────────

def test_combat_engagement_ended_caught_fleeing_for_non_lethal_opportunity_attack():
    defender = _entity(eid=1, hp=100, max_hp=100)
    attacker = _entity(eid=42, hp=100, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=42, hp_delta=-20,
                                                          is_opportunity_attack=True,
                                                          outcome_kind="SURVIVE"))})
    events = CombatShaper().shape(_prior_state({1: defender, 42: attacker}), upd, tick=10,
                                   mode=ObservabilityMode.NORMAL)
    ended = [e for e in events if e.event_type == "combat_engagement_ended"]
    assert len(ended) == 1
    assert ended[0].payload["outcome"] == "CAUGHT_FLEEING"
    assert ended[0].target_id == 42


def test_combat_engagement_ended_caught_fleeing_not_emitted_for_deliberate_attack():
    defender = _entity(eid=1, hp=100, max_hp=100)
    attacker = _entity(eid=42, hp=100, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=42, hp_delta=-20,
                                                          is_opportunity_attack=False))})
    events = CombatShaper().shape(_prior_state({1: defender, 42: attacker}), upd, tick=10,
                                   mode=ObservabilityMode.NORMAL)
    assert "combat_engagement_ended" not in _types(events)


def test_combat_engagement_ended_caught_fleeing_not_emitted_when_also_a_kill():
    """A lethal opportunity attack is reported as KILL, not double-counted as CAUGHT_FLEEING."""
    defender = _entity(eid=1, hp=10, max_hp=100, active=True)
    attacker = _entity(eid=42, hp=100, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(
        attacker_id=42, hp_delta=-10, alive_set=False, outcome_kind="KILL",
        is_opportunity_attack=True))})
    events = CombatShaper().shape(_prior_state({1: defender, 42: attacker}), upd, tick=10)
    ended = [e for e in events if e.event_type == "combat_engagement_ended"]
    assert len(ended) == 1
    assert ended[0].payload["outcome"] == "KILL"


# ── combat_engagement_ended: PURSUIT_ABANDONED (task-only, no combat field) ─

def test_combat_engagement_ended_pursuit_abandoned_leash_return():
    prior = _entity(eid=1, task=MagicMock(payload={"target_id": 55}))
    e_upd = MagicMock(combat=None, task=MagicMock(payload_set={"reason": "LEASH_RETURN"}),
                       property_updates={})
    events = CombatShaper().shape(_prior_state({1: prior}), _update({1: e_upd}), tick=10)
    ended = [e for e in events if e.event_type == "combat_engagement_ended"]
    assert len(ended) == 1
    assert ended[0].payload["outcome"] == "PURSUIT_ABANDONED"
    assert ended[0].payload["reason"] == "LEASH_RETURN"
    assert ended[0].target_id == 55


def test_combat_engagement_ended_pursuit_abandoned_stalemate_break():
    prior = _entity(eid=1, task=MagicMock(payload={"target_id": 77}))
    e_upd = MagicMock(combat=None, task=MagicMock(payload_set={"reason": "STALEMATE_BREAK"}),
                       property_updates={})
    events = CombatShaper().shape(_prior_state({1: prior}), _update({1: e_upd}), tick=10)
    ended = [e for e in events if e.event_type == "combat_engagement_ended"]
    assert len(ended) == 1
    assert ended[0].payload["outcome"] == "PURSUIT_ABANDONED"
    assert ended[0].payload["reason"] == "STALEMATE_BREAK"


def test_combat_engagement_ended_pursuit_abandoned_not_emitted_for_other_reasons():
    """Real tactical.py reason codes unrelated to giving up a chase (e.g. PANIC_RETREAT) must
    not be misread as PURSUIT_ABANDONED."""
    prior = _entity(eid=1, task=MagicMock(payload={"target_id": 55}))
    e_upd = MagicMock(combat=None, task=MagicMock(payload_set={"reason": "PANIC_RETREAT"}),
                       property_updates={})
    events = CombatShaper().shape(_prior_state({1: prior}), _update({1: e_upd}), tick=10)
    assert "combat_engagement_ended" not in _types(events)


# ── combat_engagement_ended: ESCAPED (movement.py's new combat_escape tag) ──

def test_combat_engagement_ended_escaped_reads_movement_escape_tag():
    prior = _entity(eid=1)
    e_upd = MagicMock(combat=None, task=None,
                       property_updates={"combat_escape": "EVASIVE_SUCCESS",
                                         "combat_escape_evaded_ids": [7, 8]})
    events = CombatShaper().shape(_prior_state({1: prior}), _update({1: e_upd}), tick=10)
    ended = [e for e in events if e.event_type == "combat_engagement_ended"]
    assert len(ended) == 1
    assert ended[0].payload["outcome"] == "ESCAPED"
    assert ended[0].payload["evaded_ids"] == [7, 8]
    assert ended[0].payload["actor_snapshot"] is not None


def test_combat_engagement_ended_escaped_not_emitted_without_the_tag():
    prior = _entity(eid=1)
    e_upd = MagicMock(combat=None, task=None, property_updates={})
    events = CombatShaper().shape(_prior_state({1: prior}), _update({1: e_upd}), tick=10)
    assert "combat_engagement_ended" not in _types(events)


# ── combat_resolved (TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX) ──────────

def test_combat_resolved_fires_alongside_escaped():
    prior = _entity(eid=1)
    e_upd = MagicMock(combat=None, task=None,
                       property_updates={"combat_escape": "EVASIVE_SUCCESS",
                                         "combat_escape_evaded_ids": [7, 8]})
    events = CombatShaper().shape(_prior_state({1: prior}), _update({1: e_upd}), tick=10)
    resolved = [e for e in events if e.event_type == "combat_resolved"]
    assert len(resolved) == 1
    assert resolved[0].payload["outcome"] == "ESCAPED"


def test_combat_resolved_not_emitted_for_caught_fleeing():
    defender = _entity(eid=1, hp=100, max_hp=100)
    attacker = _entity(eid=42, hp=100, max_hp=100)
    upd = _update({1: MagicMock(combat=_real_combat_upd(attacker_id=42, hp_delta=-20,
                                                          is_opportunity_attack=True,
                                                          outcome_kind="SURVIVE"))})
    events = CombatShaper().shape(_prior_state({1: defender, 42: attacker}), upd, tick=10,
                                   mode=ObservabilityMode.NORMAL)
    assert "combat_resolved" not in _types(events)


def test_combat_resolved_not_emitted_for_pursuit_abandoned():
    prior = _entity(eid=1, task=MagicMock(payload={"target_id": 55}))
    e_upd = MagicMock(combat=None, task=MagicMock(payload_set={"reason": "LEASH_RETURN"}),
                       property_updates={})
    events = CombatShaper().shape(_prior_state({1: prior}), _update({1: e_upd}), tick=10)
    assert "combat_resolved" not in _types(events)
