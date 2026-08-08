"""Unit tests for TCK-20260806-PUSH-SHAPER-REGISTRY-WORLD-DYNAMICS.

Tests the apply-layer (push-based) WorldDynamicsShaper: region/demographic/spawn/narrative events
derived from prior_state + update alone. Includes the demographic_mortality case, closing Phase
1's own INFRA-324 deferral (see investigation.md).
"""
from __future__ import annotations
from unittest.mock import MagicMock

from src.domains.world_emergence.schema import WorldEventCategory
from src.observability.event_shapers import WorldDynamicsShaper, PHASE2_SHAPER_REGISTRY


def _entity(eid, kind="hero"):
    e = MagicMock()
    e.id = eid
    e.kind = kind
    return e


def _prior_state(entities=None, regions=None, tick=100):
    s = MagicMock()
    s.tick = tick
    s.entities = entities or {}
    s.regions = regions or {}
    s.feature_flags = {}
    return s


def _real_combat_upd(attacker_id=99, outcome_kind="KILL"):
    return MagicMock(attacker_id=attacker_id, outcome_kind=outcome_kind, hp_delta=-10, alive_set=False)


def _entity_update(combat=None):
    u = MagicMock()
    u.combat = combat
    u.intent_results = []
    u.identity = None
    u.property_updates = {}
    u.self_model_bundle_set = None
    u.strategic = None
    return u


def _update(entities_add=None, entities_remove=None, entity_updates=None,
            world_updates=None, building_updates=None, last_calamity_tick_set=None,
            world_events_add=None):
    u = MagicMock()
    u.entities_add = entities_add or []
    u.entities_remove = entities_remove or []
    u.entity_updates = entity_updates or {}
    u.world_updates = world_updates or {}
    u.building_updates = building_updates or {}
    u.last_calamity_tick_set = last_calamity_tick_set
    u.world_events_add = world_events_add or []
    return u


def _region(kind="forest", trauma_score=0.0):
    r = MagicMock()
    r.kind = kind
    r.trauma_score = trauma_score
    return r


def _types(events) -> list[str]:
    return [e.event_type for e in events]


def test_phase2_registry_contains_world_dynamics_shaper():
    assert "world_dynamics" in PHASE2_SHAPER_REGISTRY
    assert any(isinstance(s, WorldDynamicsShaper) for s in PHASE2_SHAPER_REGISTRY["world_dynamics"])


# ── demographic_birth / demographic_mortality ──────────────────────────────

def test_demographic_birth():
    new_ent = _entity(5, kind="villager")
    prior = _prior_state()
    upd = _update(entities_add=[new_ent])
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "demographic_birth")
    assert ev.payload["kind"] == "villager"


def test_demographic_mortality_without_combat_attacker():
    dead = _entity(3, kind="villager")
    prior = _prior_state(entities={3: dead})
    upd = _update(entities_remove=[3], entity_updates={3: _entity_update(combat=None)})
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "demographic_mortality")
    assert ev.payload["kind"] == "villager"


def test_demographic_mortality_not_emitted_with_real_combat_attacker():
    dead = _entity(3, kind="villager")
    prior = _prior_state(entities={3: dead})
    upd = _update(entities_remove=[3], entity_updates={3: _entity_update(combat=_real_combat_upd())})
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    assert "demographic_mortality" not in _types(events)


def test_demographic_mortality_not_emitted_when_prior_entity_missing():
    prior = _prior_state(entities={})
    upd = _update(entities_remove=[99])
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    assert "demographic_mortality" not in _types(events)


# ── boss_spawned / raid_party_spawned / narrative_milestone ────────────────

def test_boss_spawned_and_narrative_milestone():
    boss = _entity(7, kind="world_boss")
    prior = _prior_state()
    upd = _update(entities_add=[boss])
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    types = _types(events)
    assert "boss_spawned" in types
    assert "narrative_milestone" in types
    milestone = next(e for e in events if e.event_type == "narrative_milestone")
    assert milestone.payload["milestone"] == "first_boss_spawned"


def test_raid_party_spawned():
    raider = _entity(8, kind="goblin_raider")
    prior = _prior_state()
    upd = _update(entities_add=[raider])
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    assert "raid_party_spawned" in _types(events)
    assert "boss_spawned" not in _types(events)


def test_regular_spawn_no_boss_or_raid_event():
    villager = _entity(9, kind="villager")
    prior = _prior_state()
    upd = _update(entities_add=[villager])
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    assert "boss_spawned" not in _types(events)
    assert "raid_party_spawned" not in _types(events)


# ── tick-modulo events ──────────────────────────────────────────────────────

def test_ecology_cycle_completed_on_interval():
    prior = _prior_state(regions={"r1": _region(kind="forest")})
    upd = _update()
    events = WorldDynamicsShaper().shape(prior, upd, tick=200)
    ev = next(e for e in events if e.event_type == "ecology_cycle_completed")
    assert ev.payload["region_id"] == "r1"


def test_ecology_cycle_not_fired_off_interval():
    prior = _prior_state(regions={"r1": _region()})
    upd = _update()
    events = WorldDynamicsShaper().shape(prior, upd, tick=201)
    assert "ecology_cycle_completed" not in _types(events)


def test_spawn_cadence_fired_on_interval_with_regular_spawns():
    villager = _entity(1, kind="villager")
    prior = _prior_state()
    upd = _update(entities_add=[villager])
    events = WorldDynamicsShaper().shape(prior, upd, tick=50)
    ev = next(e for e in events if e.event_type == "spawn_cadence_fired")
    assert ev.payload["spawned_count"] == 1


def test_spawn_cadence_not_fired_off_interval():
    villager = _entity(1, kind="villager")
    prior = _prior_state()
    upd = _update(entities_add=[villager])
    events = WorldDynamicsShaper().shape(prior, upd, tick=51)
    assert "spawn_cadence_fired" not in _types(events)


# ── world_updates-driven region events ─────────────────────────────────────

def test_region_trauma_delta():
    prior = _prior_state(regions={"r1": _region(trauma_score=10.0)})
    w_upd = MagicMock(trauma_delta=5.0, owner_faction_id_set=None, kind_set=None)
    upd = _update(world_updates={"r1": w_upd})
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "region_trauma_delta")
    assert ev.payload["delta"] == 5.0


def test_threat_evolved_on_threshold_crossing():
    prior = _prior_state(regions={"r1": _region(trauma_score=20.0)})
    w_upd = MagicMock(trauma_delta=10.0, owner_faction_id_set=None, kind_set=None)
    upd = _update(world_updates={"r1": w_upd})
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "threat_evolved")
    assert ev.payload["threshold"] == 25.0


def test_threat_evolved_not_fired_without_crossing():
    prior = _prior_state(regions={"r1": _region(trauma_score=10.0)})
    w_upd = MagicMock(trauma_delta=1.0, owner_faction_id_set=None, kind_set=None)
    upd = _update(world_updates={"r1": w_upd})
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    assert "threat_evolved" not in _types(events)


def test_region_ownership_changed():
    prior = _prior_state(regions={"r1": _region()})
    w_upd = MagicMock(trauma_delta=0.0, owner_faction_id_set="faction_2", kind_set=None)
    upd = _update(world_updates={"r1": w_upd})
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "region_ownership_changed")
    assert ev.payload["new_owner"] == "faction_2"


def test_region_transformed():
    prior = _prior_state(regions={"r1": _region()})
    w_upd = MagicMock(trauma_delta=0.0, owner_faction_id_set=None, kind_set="wasteland")
    upd = _update(world_updates={"r1": w_upd})
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "region_transformed")
    assert ev.payload["new_kind"] == "wasteland"


# ── building_sabotaged ──────────────────────────────────────────────────────

def test_building_sabotaged():
    prior = _prior_state()
    b_upd = MagicMock(hp_delta=-15.0)
    upd = _update(building_updates={"b1": b_upd})
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "building_sabotaged")
    assert ev.payload["building_id"] == "b1"
    assert ev.payload["hp_delta"] == -15.0


def test_building_sabotaged_not_fired_on_positive_hp_delta():
    prior = _prior_state()
    b_upd = MagicMock(hp_delta=5.0)
    upd = _update(building_updates={"b1": b_upd})
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    assert "building_sabotaged" not in _types(events)


# ── calamity_spawned ─────────────────────────────────────────────────────

def test_calamity_spawned():
    prior = _prior_state(tick=50)
    upd = _update(last_calamity_tick_set=50)
    events = WorldDynamicsShaper().shape(prior, upd, tick=50)
    assert "calamity_spawned" in _types(events)


def test_calamity_spawned_not_fired_on_different_tick():
    prior = _prior_state(tick=50)
    upd = _update(last_calamity_tick_set=40)
    events = WorldDynamicsShaper().shape(prior, upd, tick=50)
    assert "calamity_spawned" not in _types(events)


# ── world_events_add: world_emergence_event / narrative_milestone ─────────

def test_world_emergence_event_for_every_world_event():
    we = MagicMock(category=WorldEventCategory.FACTION_WAR_DECLARED, region_id="r1", subject="f1_vs_f2")
    prior = _prior_state()
    upd = _update(world_events_add=[we])
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    assert "world_emergence_event" in _types(events)


def test_narrative_milestone_first_war():
    we = MagicMock(category=WorldEventCategory.FACTION_WAR_DECLARED, region_id=None, subject="f1_vs_f2")
    prior = _prior_state()
    upd = _update(world_events_add=[we])
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "narrative_milestone")
    assert ev.payload["milestone"] == "first_war"


def test_narrative_milestone_first_sovereignty_transfer():
    we = MagicMock(category=WorldEventCategory.SOVEREIGNTY_SHIFT, region_id="r1", subject=None)
    prior = _prior_state()
    upd = _update(world_events_add=[we])
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    ev = next(e for e in events if e.event_type == "narrative_milestone")
    assert ev.payload["milestone"] == "first_sovereignty_transfer"


def test_narrative_milestone_not_fired_for_unrelated_category():
    we = MagicMock(category=WorldEventCategory.TERRITORY_TRANSFERRED, region_id="r1", subject="x")
    prior = _prior_state()
    upd = _update(world_events_add=[we])
    events = WorldDynamicsShaper().shape(prior, upd, tick=10)
    assert "narrative_milestone" not in _types(events)
    # world_emergence_event still fires for every WorldEvent regardless of category
    assert "world_emergence_event" in _types(events)
