"""Unit tests for EventExtractor SOCIAL and FACTION event emission.

TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION

SOCIAL events: cooperation_event, contract_offer_created, contract_offer_accepted,
  contract_completed (FULFILLED bug fix), contract_lapsed (ACTIVE→EXPIRED only),
  contract_expired_offer, reputation_delta, group_joined, group_expelled.
  Gap documentation: contract_milestone_completed, social_memory_created.

FACTION events: diplomatic_transition, alliance_accepted, war_declared,
  military_conflict_resolved, territory_ownership_changed, faction_tension_delta,
  faction_extinct.
  Gap documentation: alliance_proposed, resource_seized.
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
    e.strategic.contracts = {}
    e.group_id = None
    e.social = MagicMock()
    e.social.public_reputation = 0.0
    return e


def _state(entities: dict, tick: int = 10, factions: dict | None = None):
    s = MagicMock()
    s.tick = tick
    s.entities = entities
    s.resource_nodes = {}
    s.factions = factions or {}
    return s


def _update(entity_updates: dict | None = None,
            faction_updates: list | None = None,
            world_events_add: list | None = None):
    u = MagicMock()
    u.entity_updates = entity_updates or {}
    u.world_updates = {}
    u.last_calamity_tick_set = None
    u.entities_add = []
    u.faction_updates = faction_updates if faction_updates is not None else []
    u.world_events_add = world_events_add if world_events_add is not None else []
    return u


def _update_with_prop(eid: int, prop: dict):
    eu = MagicMock()
    eu.property_updates = prop
    eu.combat_upd = None
    eu.self_model_bundle_set = None
    eu.intent_results = []
    eu.combat = None
    return _update({eid: eu})


def _contract_state(status_name: str):
    cs = MagicMock()
    cs.status = MagicMock()
    cs.status.name = status_name
    return cs


def _faction_update(faction_id: str,
                    diplomatic_relations_set: dict | None = None,
                    territory_add: tuple = (),
                    territory_remove: tuple = (),
                    tension_delta: float = 0.0):
    upd = MagicMock()
    upd.faction_id = faction_id
    upd.diplomatic_relations_set = diplomatic_relations_set or {}
    upd.territory_add = territory_add
    upd.territory_remove = territory_remove
    upd.tension_delta = tension_delta
    return upd


def _diplo_state(name: str):
    ds = MagicMock()
    ds.name = name
    return ds


def _world_event(category, subject: str = ""):
    we = MagicMock()
    we.category = category
    we.subject = subject
    return we


def _types(events) -> list[str]:
    return [e.event_type for e in events]


# ── S-01..S-03: cooperation_event (PP-05) ─────────────────────────────────────

def test_cooperation_event_emitted_when_decision_in_property_updates():
    e = _entity()
    state = _state({1: e})
    upd = _update_with_prop(1, {"last_cooperation_decision": "HELP"})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "cooperation_event" in _types(events)


def test_cooperation_event_payload_has_entity_id():
    e = _entity(eid=7)
    state = _state({7: e})
    upd = _update_with_prop(7, {"last_cooperation_decision": "ASSIST"})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    ev = next(x for x in events if x.event_type == "cooperation_event")
    assert ev.payload["entity_id"] == 7


def test_cooperation_event_not_emitted_when_no_decision():
    e = _entity()
    state = _state({1: e})
    upd = _update_with_prop(1, {"last_routing_family": "gather"})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "cooperation_event" not in _types(events)


# ── S-04..S-06: contract_offer_created (PP-35, new contract) ─────────────────

def test_contract_offer_created_when_new_offered_contract():
    prior = _entity()
    prior.strategic.contracts = {}
    curr = _entity()
    curr.strategic.contracts = {"c1": _contract_state("OFFERED")}
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "contract_offer_created" in _types(events)


def test_contract_offer_created_payload_has_contract_id():
    prior = _entity()
    prior.strategic.contracts = {}
    curr = _entity()
    curr.strategic.contracts = {"contract_99": _contract_state("OFFERED")}
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    ev = next(x for x in events if x.event_type == "contract_offer_created")
    assert ev.payload["contract_id"] == "contract_99"


def test_contract_offer_created_not_emitted_for_accepted_new_contract():
    prior = _entity()
    prior.strategic.contracts = {}
    curr = _entity()
    curr.strategic.contracts = {"c2": _contract_state("ACTIVE")}
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "contract_offer_created" not in _types(events)


# ── S-07..S-08: contract_offer_accepted (regression) ─────────────────────────

def test_contract_offer_accepted_offered_to_active():
    prior = _entity()
    prior.strategic.contracts = {"c1": _contract_state("OFFERED")}
    curr = _entity()
    curr.strategic.contracts = {"c1": _contract_state("ACTIVE")}
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "contract_offer_accepted" in _types(events)


def test_contract_offer_accepted_not_active_to_active():
    prior = _entity()
    prior.strategic.contracts = {"c1": _contract_state("ACTIVE")}
    curr = _entity()
    curr.strategic.contracts = {"c1": _contract_state("ACTIVE")}
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "contract_offer_accepted" not in _types(events)


# ── S-09..S-11: contract_completed (FULFILLED enum alias bug fix) ─────────────

def test_contract_completed_on_fulfilled_status():
    prior = _entity()
    prior.strategic.contracts = {"c1": _contract_state("ACTIVE")}
    curr = _entity()
    curr.strategic.contracts = {"c1": _contract_state("FULFILLED")}
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "contract_completed" in _types(events)


def test_contract_completed_payload_has_contract_id():
    prior = _entity()
    prior.strategic.contracts = {"contract_42": _contract_state("ACTIVE")}
    curr = _entity()
    curr.strategic.contracts = {"contract_42": _contract_state("FULFILLED")}
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    ev = next(x for x in events if x.event_type == "contract_completed")
    assert ev.payload["contract_id"] == "contract_42"


def test_contract_completed_not_on_failed_status():
    prior = _entity()
    prior.strategic.contracts = {"c1": _contract_state("ACTIVE")}
    curr = _entity()
    curr.strategic.contracts = {"c1": _contract_state("FAILED")}
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "contract_completed" not in _types(events)


# ── S-12..S-13: contract_lapsed (ACTIVE→EXPIRED only) ─────────────────────────

def test_contract_lapsed_on_active_to_expired():
    prior = _entity()
    prior.strategic.contracts = {"c1": _contract_state("ACTIVE")}
    curr = _entity()
    curr.strategic.contracts = {"c1": _contract_state("EXPIRED")}
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    types = _types(events)
    assert "contract_lapsed" in types
    assert "contract_expired_offer" not in types


def test_contract_lapsed_not_on_offered_to_expired():
    prior = _entity()
    prior.strategic.contracts = {"c1": _contract_state("OFFERED")}
    curr = _entity()
    curr.strategic.contracts = {"c1": _contract_state("EXPIRED")}
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "contract_lapsed" not in _types(events)


# ── S-14..S-16: contract_expired_offer (PP-36, OFFERED expiry) ───────────────

def test_contract_expired_offer_on_offered_to_expired():
    prior = _entity()
    prior.strategic.contracts = {"c1": _contract_state("OFFERED")}
    curr = _entity()
    curr.strategic.contracts = {"c1": _contract_state("EXPIRED")}
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "contract_expired_offer" in _types(events)


def test_contract_expired_offer_on_reap_removal():
    prior = _entity()
    prior.strategic.contracts = {"c_reaped": _contract_state("OFFERED")}
    curr = _entity()
    curr.strategic.contracts = {}
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "contract_expired_offer" in _types(events)


def test_contract_expired_offer_payload_has_contract_id():
    prior = _entity()
    prior.strategic.contracts = {"c_offer_77": _contract_state("OFFERED")}
    curr = _entity()
    curr.strategic.contracts = {}
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    ev = next(x for x in events if x.event_type == "contract_expired_offer")
    assert ev.payload["contract_id"] == "c_offer_77"


# ── S-17..S-20: reputation_delta (PP-18) ─────────────────────────────────────

def test_reputation_delta_emitted_on_significant_change():
    prior = _entity()
    prior.social.public_reputation = 0.3
    curr = _entity()
    curr.social.public_reputation = 0.42  # delta = 0.12 > 0.05
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "reputation_delta" in _types(events)


def test_reputation_delta_payload_has_delta_and_entity_id():
    prior = _entity(eid=3)
    prior.social.public_reputation = 0.0
    curr = _entity(eid=3)
    curr.social.public_reputation = 0.1
    prior_state = _state({3: prior})
    curr_state = _state({3: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    ev = next(x for x in events if x.event_type == "reputation_delta")
    assert "delta" in ev.payload
    assert ev.payload["entity_id"] == 3


def test_reputation_delta_not_emitted_below_threshold():
    prior = _entity()
    prior.social.public_reputation = 0.5
    curr = _entity()
    curr.social.public_reputation = 0.53  # delta = 0.03 < 0.05
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "reputation_delta" not in _types(events)


def test_reputation_delta_not_emitted_on_zero_change():
    prior = _entity()
    prior.social.public_reputation = 0.7
    curr = _entity()
    curr.social.public_reputation = 0.7
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "reputation_delta" not in _types(events)


# ── S-21..S-22: group_joined / group_expelled (regression) ───────────────────

def test_group_joined_on_group_id_set():
    prior = _entity()
    prior.group_id = None
    curr = _entity()
    curr.group_id = "guild_1"
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "group_joined" in _types(events)


def test_group_expelled_on_group_id_cleared():
    prior = _entity()
    prior.group_id = "guild_1"
    curr = _entity()
    curr.group_id = None
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "group_expelled" in _types(events)


# ── S-23..S-24: SOCIAL gap documentation tests ───────────────────────────────

def test_gap_contract_milestone_completed_not_emitted():
    """GAP: contract_milestone_completed cannot be emitted from state diff.
    ContractState (strategic.py:L177) has no milestone or progress tracking field.
    Same architectural constraint as commitment_abandoned in AGENCY ticket.
    Requires ContractState schema extension to add milestone tracking."""
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update(), ObservabilityMode.NORMAL)
    assert "contract_milestone_completed" not in _types(events)


def test_gap_social_memory_created_not_emitted():
    """GAP: social_memory_created cannot be emitted from state diff.
    CooperationPhase appends to entity.timeline (phase.py:L65), a transient
    in-memory buffer not persisted to EntityState.strategic.
    Requires entity.strategic.social_memories field to be added."""
    e = _entity()
    state = _state({1: e})
    events = EventExtractor.extract(state, state, _update(), ObservabilityMode.NORMAL)
    assert "social_memory_created" not in _types(events)


# ── F-01..F-04: diplomatic_transition (PP-10) ────────────────────────────────

def test_diplomatic_transition_emitted_from_faction_update():
    upd = _update(
        faction_updates=[
            _faction_update("faction_a", diplomatic_relations_set={"faction_b": _diplo_state("TENSE")})
        ]
    )
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "diplomatic_transition" in _types(events)


def test_diplomatic_transition_payload_has_faction_id_and_target():
    upd = _update(
        faction_updates=[
            _faction_update("fac_x", diplomatic_relations_set={"fac_y": _diplo_state("HOSTILE")})
        ]
    )
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    ev = next(x for x in events if x.event_type == "diplomatic_transition")
    assert ev.payload["faction_id"] == "fac_x"
    assert ev.payload["target_faction_id"] == "fac_y"
    assert ev.payload["new_state"] == "HOSTILE"


def test_diplomatic_transition_deduped_per_pair():
    """Both FactionUpdates for same pair (a→b and b→a) must produce exactly 1 event."""
    upd = _update(
        faction_updates=[
            _faction_update("fac_a", diplomatic_relations_set={"fac_b": _diplo_state("TENSE")}),
            _faction_update("fac_b", diplomatic_relations_set={"fac_a": _diplo_state("TENSE")}),
        ]
    )
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    diplo_events = [x for x in events if x.event_type == "diplomatic_transition"]
    assert len(diplo_events) == 1


def test_diplomatic_transition_not_emitted_on_empty_faction_updates():
    upd = _update(faction_updates=[])
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "diplomatic_transition" not in _types(events)


# ── F-05..F-07: alliance_accepted (PP-08/PP-10) ───────────────────────────────

def test_alliance_accepted_emitted_when_allied_state_set():
    upd = _update(
        faction_updates=[
            _faction_update("fac_a", diplomatic_relations_set={"fac_b": _diplo_state("ALLIED")})
        ]
    )
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "alliance_accepted" in _types(events)


def test_alliance_accepted_payload_has_faction_pair():
    upd = _update(
        faction_updates=[
            _faction_update("fac_a", diplomatic_relations_set={"fac_b": _diplo_state("ALLIED")})
        ]
    )
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    ev = next(x for x in events if x.event_type == "alliance_accepted")
    assert ev.payload["faction_id"] == "fac_a"
    assert ev.payload["partner_id"] == "fac_b"


def test_alliance_accepted_not_emitted_for_tense_transition():
    upd = _update(
        faction_updates=[
            _faction_update("fac_a", diplomatic_relations_set={"fac_b": _diplo_state("TENSE")})
        ]
    )
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "alliance_accepted" not in _types(events)


# ── F-08..F-10: war_declared (PP-10, WorldEvent) ─────────────────────────────

def test_war_declared_emitted_from_world_events_add():
    from src.domains.world_emergence.schema import WorldEventCategory
    upd = _update(world_events_add=[_world_event(WorldEventCategory.FACTION_WAR_DECLARED, "fac_a:fac_b")])
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "war_declared" in _types(events)


def test_war_declared_payload_has_faction_pair():
    from src.domains.world_emergence.schema import WorldEventCategory
    upd = _update(world_events_add=[_world_event(WorldEventCategory.FACTION_WAR_DECLARED, "orcs:elves")])
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    ev = next(x for x in events if x.event_type == "war_declared")
    assert ev.payload["faction_pair"] == "orcs:elves"


def test_war_declared_not_emitted_on_empty_world_events():
    upd = _update(world_events_add=[])
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "war_declared" not in _types(events)


# ── F-11..F-13: military_conflict_resolved (PP-11, WorldEvent) ───────────────

def test_military_conflict_resolved_on_territory_transferred():
    from src.domains.world_emergence.schema import WorldEventCategory
    upd = _update(world_events_add=[_world_event(WorldEventCategory.TERRITORY_TRANSFERRED, "region_5")])
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "military_conflict_resolved" in _types(events)


def test_military_conflict_resolved_on_war_ended_exhaustion():
    from src.domains.world_emergence.schema import WorldEventCategory
    upd = _update(world_events_add=[_world_event(WorldEventCategory.WAR_ENDED_EXHAUSTION, "fac_a:fac_b")])
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "military_conflict_resolved" in _types(events)


def test_military_conflict_resolved_payload_has_subject():
    from src.domains.world_emergence.schema import WorldEventCategory
    upd = _update(world_events_add=[_world_event(WorldEventCategory.TERRITORY_TRANSFERRED, "region_12")])
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    ev = next(x for x in events if x.event_type == "military_conflict_resolved")
    assert ev.payload["subject"] == "region_12"


# ── F-14..F-16: territory_ownership_changed (PP-11) ──────────────────────────

def test_territory_ownership_changed_on_territory_add():
    upd = _update(
        faction_updates=[_faction_update("fac_a", territory_add=("region_1",))]
    )
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "territory_ownership_changed" in _types(events)


def test_territory_ownership_changed_payload_has_faction_and_region():
    upd = _update(
        faction_updates=[_faction_update("fac_a", territory_add=("region_7",))]
    )
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    ev = next(x for x in events if x.event_type == "territory_ownership_changed")
    assert ev.payload["faction_id"] == "fac_a"
    assert ev.payload["region_id"] == "region_7"


def test_territory_ownership_changed_not_emitted_on_territory_remove():
    upd = _update(
        faction_updates=[_faction_update("fac_a", territory_remove=("region_1",))]
    )
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "territory_ownership_changed" not in _types(events)


def test_territory_ownership_changed_includes_faction_territory_pct():
    # TCK-20260807-FACTION-TERRITORY-PCT-PAYLOAD-GAP
    upd = _update(
        faction_updates=[_faction_update("fac_a", territory_add=("region_1",))]
    )
    current_faction = MagicMock(territory=("region_1", "region_2", "region_3"))
    state = _state({}, factions={"fac_a": current_faction})
    state.regions = {"region_1": MagicMock(), "region_2": MagicMock(),
                      "region_3": MagicMock(), "region_4": MagicMock()}
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    ev = next(x for x in events if x.event_type == "territory_ownership_changed")
    assert ev.payload["faction_territory_pct"] == 0.75


# ── F-17..F-19: faction_tension_delta (PP-09) ────────────────────────────────

def test_faction_tension_delta_on_nonzero_tension_delta():
    upd = _update(faction_updates=[_faction_update("fac_a", tension_delta=0.1)])
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "faction_tension_delta" in _types(events)


def test_faction_tension_delta_payload_has_delta():
    upd = _update(faction_updates=[_faction_update("fac_x", tension_delta=0.25)])
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    ev = next(x for x in events if x.event_type == "faction_tension_delta")
    assert ev.payload["faction_id"] == "fac_x"
    assert ev.payload["delta"] == 0.25


def test_faction_tension_delta_not_emitted_on_zero_delta():
    upd = _update(faction_updates=[_faction_update("fac_a", tension_delta=0.0)])
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "faction_tension_delta" not in _types(events)


# ── F-20..F-22: faction_extinct ───────────────────────────────────────────────

def _make_entity_with_faction(eid: int, faction_id: str, hp: int = 100):
    e = MagicMock()
    e.id = eid
    e.hp = hp
    e.kind = "hero"
    e.combat = MagicMock()
    e.combat.hp = hp
    e.combat.max_hp = 100
    e.lifecycle = MagicMock()
    e.lifecycle.active = hp > 0
    e.navigation = MagicMock()
    e.navigation.position = (0.0, 0.0)
    e.inventory = MagicMock()
    e.inventory.gold = 0.0
    e.identity = MagicMock()
    e.identity.evolution_points = 0
    e.identity.evolution_level = 1
    e.identity.faction = faction_id
    e.strategic = MagicMock()
    e.strategic.projects = {}
    e.strategic.leads = {}
    e.strategic.contracts = {}
    e.group_id = None
    e.social = MagicMock()
    e.social.public_reputation = 0.0
    return e


def test_faction_extinct_emitted_when_no_living_entities():
    dead_ent = _make_entity_with_faction(1, "orc_clan", hp=0)
    live_ent_prior = _make_entity_with_faction(1, "orc_clan", hp=50)

    prior_state = _state({1: live_ent_prior}, factions={"orc_clan": MagicMock()})
    curr_state = _state({1: dead_ent}, factions={"orc_clan": MagicMock()})

    upd = _update(faction_updates=[_faction_update("orc_clan")])
    events = EventExtractor.extract(prior_state, curr_state, upd, ObservabilityMode.NORMAL)
    assert "faction_extinct" in _types(events)


def test_faction_extinct_payload_has_faction_id():
    dead_ent = _make_entity_with_faction(1, "dark_elves", hp=0)
    live_ent_prior = _make_entity_with_faction(1, "dark_elves", hp=30)

    prior_state = _state({1: live_ent_prior}, factions={"dark_elves": MagicMock()})
    curr_state = _state({1: dead_ent}, factions={"dark_elves": MagicMock()})

    upd = _update(faction_updates=[_faction_update("dark_elves")])
    events = EventExtractor.extract(prior_state, curr_state, upd, ObservabilityMode.NORMAL)
    ev = next(x for x in events if x.event_type == "faction_extinct")
    assert ev.payload["faction_id"] == "dark_elves"


def test_faction_extinct_not_emitted_when_living_entities_remain():
    live_ent = _make_entity_with_faction(1, "dwarves", hp=80)
    prior_live = _make_entity_with_faction(1, "dwarves", hp=100)

    prior_state = _state({1: prior_live}, factions={"dwarves": MagicMock()})
    curr_state = _state({1: live_ent}, factions={"dwarves": MagicMock()})

    upd = _update(faction_updates=[_faction_update("dwarves")])
    events = EventExtractor.extract(prior_state, curr_state, upd, ObservabilityMode.NORMAL)
    assert "faction_extinct" not in _types(events)


# ── F-23..F-24: FACTION gap documentation tests ──────────────────────────────

def test_gap_alliance_proposed_not_emitted():
    """GAP: alliance_proposed cannot be emitted from EventExtractor.
    faction_directives is a local list in pipeline.py:L171 consumed only by
    AdventureDecisionPhase. It is never serialized into StateUpdate.
    Same architectural constraint as defer_with_reason in AGENCY ticket.
    Requires StateUpdate to carry faction_directives to expose this event."""
    state = _state({})
    upd = _update(faction_updates=[])
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "alliance_proposed" not in _types(events)


def test_gap_resource_seized_not_emitted():
    """GAP: resource_seized has no distinct WorldEvent from MilitaryConflictPhase.
    TERRITORY_TRANSFERRED covers region ownership transfer but not per-resource
    granularity. Blocked pending WorldEvent schema extension to add resource_seized
    category (src/domains/world_emergence/schema.py WorldEventCategory enum)."""
    from src.domains.world_emergence.schema import WorldEventCategory
    upd = _update(world_events_add=[_world_event(WorldEventCategory.TERRITORY_TRANSFERRED)])
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    assert "resource_seized" not in _types(events)


# ── Anti-drift guards ─────────────────────────────────────────────────────────

def test_no_simulation_quality_import_in_event_extractor():
    """EventExtractor must not import from src.simulation_quality (architecture boundary)."""
    import ast
    import pathlib
    src = pathlib.Path("src/observability/event_extractor.py").read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", "") or ""
            assert "simulation_quality" not in module, (
                f"event_extractor.py must not import simulation_quality (found: {module})"
            )


def test_diplomatic_dedup_four_factions_six_pairs():
    """4 factions, all transitioning to TENSE simultaneously → exactly 6 diplomatic_transition events."""
    factions = ["f1", "f2", "f3", "f4"]
    faction_updates = []
    for fa in factions:
        others = {fb: _diplo_state("TENSE") for fb in factions if fb != fa}
        faction_updates.append(_faction_update(fa, diplomatic_relations_set=others))

    upd = _update(faction_updates=faction_updates)
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    diplo_events = [x for x in events if x.event_type == "diplomatic_transition"]
    assert len(diplo_events) == 6


def test_empty_faction_updates_no_attribute_error():
    """faction_updates == [] must not raise AttributeError or produce faction events."""
    upd = _update(faction_updates=[])
    state = _state({})
    events = EventExtractor.extract(state, state, upd, ObservabilityMode.NORMAL)
    faction_types = [x.event_type for x in events if x.event_category == "faction"]
    assert faction_types == []


def test_world_events_add_missing_attribute_no_error():
    """StateUpdate without world_events_add attribute must not raise AttributeError."""
    u = MagicMock()
    u.entity_updates = {}
    u.world_updates = {}
    u.last_calamity_tick_set = None
    u.entities_add = []
    u.faction_updates = []
    del u.world_events_add  # simulate missing attribute
    state = _state({})
    events = EventExtractor.extract(state, state, u, ObservabilityMode.NORMAL)
    assert "war_declared" not in _types(events)


def test_contract_completed_fires_for_fulfilled_not_completed_name():
    """Regression guard: contract_completed must fire for FULFILLED (canonical .name),
    not COMPLETED (alias that .name never returns). Prevents regression of enum alias bug."""
    prior = _entity()
    prior.strategic.contracts = {"c_guard": _contract_state("ACTIVE")}
    curr = _entity()
    # Explicitly set name to FULFILLED (the canonical name Python Enum returns for aliases)
    curr.strategic.contracts = {"c_guard": _contract_state("FULFILLED")}
    prior_state = _state({1: prior})
    curr_state = _state({1: curr})
    events = EventExtractor.extract(prior_state, curr_state, _update(), ObservabilityMode.NORMAL)
    assert "contract_completed" in _types(events)
