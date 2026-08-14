"""Unit tests for EventExtractor WORLD DYNAMICS event emission (TCK-20260629-SIMQ-EMIT-WORLD).

Tests for: hazard_drain_applied, region_trauma_delta, region_ownership_changed,
region_transformed, calamity_spawned, boss_spawned, raid_party_spawned.
"""
from __future__ import annotations
from unittest.mock import MagicMock

from src.observability.config import ObservabilityMode
from src.observability.event_extractor import EventExtractor


# ── Minimal mock builders ─────────────────────────────────────────────────────

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


def _update_with_hazard(eid: int, hp_delta: int = -15):
    combat_upd = MagicMock()
    combat_upd.outcome_kind = "HAZARD"
    combat_upd.hp_delta = hp_delta
    eu = MagicMock()
    eu.property_updates = {}
    eu.resource_transfers = []
    eu.self_model_bundle_set = None
    eu.combat = combat_upd
    u = MagicMock()
    u.entity_updates = {eid: eu}
    u.world_updates = {}
    u.last_calamity_tick_set = None
    u.entities_add = []
    return u


def _update_with_world(world_updates: dict, tick: int = 10,
                        last_calamity: int | None = None, entities_add: list | None = None):
    u = MagicMock()
    u.entity_updates = {}
    u.world_updates = world_updates
    u.last_calamity_tick_set = last_calamity
    u.entities_add = entities_add or []
    return u


def _world_upd(trauma_delta: float = 0.0, owner_faction_id_set=None, kind_set=None):
    w = MagicMock()
    w.trauma_delta = trauma_delta
    w.owner_faction_id_set = owner_faction_id_set
    w.kind_set = kind_set
    return w


def _new_entity(kind: str, eid: int = 99):
    e = MagicMock()
    e.id = eid
    e.kind = kind
    return e


def _types(events) -> list[str]:
    return [e.event_type for e in events]


# ── hazard_drain_applied ──────────────────────────────────────────────────────

def test_hazard_drain_applied_emitted():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_hazard(1, -15), ObservabilityMode.NORMAL)
    assert "hazard_drain_applied" in _types(events)


def test_hazard_drain_applied_damage_in_payload():
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update_with_hazard(1, -20), ObservabilityMode.NORMAL)
    ev = next(e for e in events if e.event_type == "hazard_drain_applied")
    assert ev.payload["damage"] == 20


def test_hazard_drain_not_emitted_for_normal_combat():
    e = _entity()
    state = _state({1: e})
    combat_upd = MagicMock()
    combat_upd.outcome_kind = "COMBAT_DAMAGE"
    combat_upd.hp_delta = -10
    eu = MagicMock()
    eu.property_updates = {}
    eu.resource_transfers = []
    eu.self_model_bundle_set = None
    eu.combat = combat_upd
    u = MagicMock()
    u.entity_updates = {1: eu}
    u.world_updates = {}
    u.last_calamity_tick_set = None
    u.entities_add = []
    events = EventExtractor.extract(state, state, u, ObservabilityMode.NORMAL)
    assert "hazard_drain_applied" not in _types(events)


def test_hazard_damage_not_misclassified_as_combat():
    """TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX: a real HP drop caused by
    hazard drain (outcome_kind="HAZARD", no attacker_id) must fire hazard_drain_applied only —
    never combat_damage/combat_initiated, which the extractor previously emitted unconditionally
    on any hp_diff < 0 regardless of cause."""
    prior = _entity(1)
    prior.combat.hp = 100
    prior_state = _state({1: prior})
    curr = _entity(1)
    curr.combat.hp = 85
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update_with_hazard(1, -15), ObservabilityMode.NORMAL)
    types = _types(events)
    assert "hazard_drain_applied" in types
    assert "combat_damage" not in types
    assert "combat_initiated" not in types


def _dying_update(eid: int, death_reason, prior_combat_outcome_kind: str | None = None):
    """A same-tick EntityUpdate representing a lifecycle.active->False transition, with an
    optional combat_upd left over from the tick that actually caused the fatal damage (HAZARD
    drain sets outcome_kind on the SAME tick it drops HP <= 0, one tick before
    LifecycleSystem.resolve_lifecycle() finalizes the transition -- see
    TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION)."""
    eu = MagicMock()
    eu.property_updates = {}
    eu.resource_transfers = []
    eu.self_model_bundle_set = None
    if prior_combat_outcome_kind is not None:
        combat_upd = MagicMock()
        combat_upd.outcome_kind = prior_combat_outcome_kind
        combat_upd.attacker_id = None
        combat_upd.hp_delta = 0
        eu.combat = combat_upd
    else:
        eu.combat = None
    u = MagicMock()
    u.entity_updates = {eid: eu}
    u.world_updates = {}
    u.last_calamity_tick_set = None
    u.entities_add = []
    return u


def test_combat_kill_not_emitted_for_hazard_caused_death():
    """TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION: a death whose own
    authoritative LifecycleComponent.death_reason isn't "COMBAT" (e.g. a hazard-drain-caused
    death, or the death_reason=None mass-despawn case) must not fire combat_kill -- it isn't a
    real combat event and shouldn't be penalized under the COMBAT pillar's attrition scoring."""
    prior = _entity(1)
    prior.lifecycle.active = True
    curr = _entity(1)
    curr.lifecycle.active = False
    curr.lifecycle.death_reason = None
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _dying_update(1, None, "HAZARD"), ObservabilityMode.NORMAL)
    assert "combat_kill" not in _types(events)


def test_combat_kill_emitted_for_genuine_combat_death():
    """Regression guard: a real combat-caused death (death_reason=="COMBAT", the value
    LifecycleSystem.resolve_lifecycle() assigns on ent_upd.combat.outcome_kind=="KILL") must
    still fire combat_kill -- this fix narrows the fallback, it doesn't remove it."""
    prior = _entity(1)
    prior.lifecycle.active = True
    curr = _entity(1)
    curr.lifecycle.active = False
    curr.lifecycle.death_reason = "COMBAT"
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _dying_update(1, "COMBAT", "KILL"), ObservabilityMode.NORMAL)
    assert "combat_kill" in _types(events)


# ── region_trauma_delta ───────────────────────────────────────────────────────

def test_region_trauma_delta_emitted():
    state = _state({})
    upd = _update_with_world({"region_1": _world_upd(trauma_delta=2.5)})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "region_trauma_delta" in _types(events)


def test_region_trauma_delta_payload():
    state = _state({})
    upd = _update_with_world({"region_A": _world_upd(trauma_delta=3.0)})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    ev = next(e for e in events if e.event_type == "region_trauma_delta")
    assert ev.payload["region_id"] == "region_A"
    assert ev.payload["delta"] == 3.0


def test_region_trauma_delta_not_emitted_when_zero():
    state = _state({})
    upd = _update_with_world({"region_1": _world_upd(trauma_delta=0.0)})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "region_trauma_delta" not in _types(events)


# ── region_ownership_changed ──────────────────────────────────────────────────

def test_region_ownership_changed_emitted():
    state = _state({})
    upd = _update_with_world({"region_1": _world_upd(owner_faction_id_set=2)})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "region_ownership_changed" in _types(events)


def test_region_ownership_changed_payload():
    state = _state({})
    upd = _update_with_world({"region_B": _world_upd(owner_faction_id_set=5)})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    ev = next(e for e in events if e.event_type == "region_ownership_changed")
    assert ev.payload["region_id"] == "region_B"
    assert "5" in ev.payload["new_owner"]


# ── region_transformed ────────────────────────────────────────────────────────

def test_region_transformed_emitted():
    state = _state({})
    upd = _update_with_world({"region_1": _world_upd(kind_set="corrupted")})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "region_transformed" in _types(events)


def test_region_transformed_payload():
    state = _state({})
    upd = _update_with_world({"region_C": _world_upd(kind_set="blighted")})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    ev = next(e for e in events if e.event_type == "region_transformed")
    assert ev.payload["region_id"] == "region_C"
    assert ev.payload["new_kind"] == "blighted"


# ── calamity_spawned ──────────────────────────────────────────────────────────

def test_calamity_spawned_emitted():
    state = _state({})
    state.tick = 10
    upd = _update_with_world({}, tick=10, last_calamity=10)
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "calamity_spawned" in _types(events)


def test_calamity_not_emitted_when_tick_mismatch():
    state = _state({})
    state.tick = 10
    upd = _update_with_world({}, tick=10, last_calamity=5)
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "calamity_spawned" not in _types(events)


# ── boss_spawned ──────────────────────────────────────────────────────────────

def test_boss_spawned_emitted_for_world_boss():
    state = _state({})
    upd = _update_with_world({}, entities_add=[_new_entity("world_boss", 99)])
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "boss_spawned" in _types(events)


def test_boss_spawned_emitted_for_ancient_sentinel():
    state = _state({})
    upd = _update_with_world({}, entities_add=[_new_entity("ancient_sentinel", 88)])
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "boss_spawned" in _types(events)


def test_boss_spawned_payload():
    state = _state({})
    upd = _update_with_world({}, entities_add=[_new_entity("world_boss", 99)])
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    ev = next(e for e in events if e.event_type == "boss_spawned")
    assert ev.payload["kind"] == "world_boss"


# ── raid_party_spawned ────────────────────────────────────────────────────────

def test_raid_party_spawned_emitted():
    state = _state({})
    upd = _update_with_world({}, entities_add=[_new_entity("goblin_raider", 77)])
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "raid_party_spawned" in _types(events)


def test_regular_spawn_no_world_event():
    state = _state({})
    upd = _update_with_world({}, entities_add=[_new_entity("hero", 10)])
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "boss_spawned" not in _types(events)
    assert "raid_party_spawned" not in _types(events)
