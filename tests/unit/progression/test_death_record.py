"""Every death carries a durable typed record (cause, tick, last attacker, hazard kind), written only by the lifecycle resolver and applied through
the authoritative path; the body remembers who last hit it so a hazard or starvation death still names an attacker."""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.death_cause import DeathCause, DeathRecord
from src.core.enums import PassiveDeathCause
from src.core.region_resolution import resolve_region_among
from src.core.state import AuthoritativeState
from src.core.updates import CombatUpdate, EntityUpdate, LifecycleUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.systems.lifecycle import LifecycleSystem
from tests.unit.observability.test_starvation_death_record import WHO, _at_tick, _world


def _body(**combat):
    ent = V2EntityBuilder(1).location(0.0, 0.0).build()
    return replace(ent, combat=replace(ent.combat, **combat))


def test_old_age_writes_a_record_with_no_attacker():
    ent = V2EntityBuilder(1).location(0.0, 0.0).lifecycle(age_ticks=1000).build()
    ent = replace(ent, lifecycle=replace(ent.lifecycle, max_age_ticks=1000))
    upd = LifecycleSystem.resolve_lifecycle(AuthoritativeState(tick=100, seed=1, entities={1: ent}), StateUpdate()).entity_updates[1]
    assert upd.lifecycle.death_record_set == DeathRecord(cause=DeathCause.OLD_AGE, tick=100)


def test_a_killing_hit_names_its_attacker():
    state = AuthoritativeState(tick=100, seed=1, entities={1: _body()})
    kill = CombatUpdate(outcome_kind="KILL", is_lethal=True, attacker_id=9, damage_taken=5, hp_delta=-5)
    record = LifecycleSystem.resolve_lifecycle(state, StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=kill)})).entity_updates[1].lifecycle.death_record_set
    assert record == DeathRecord(cause=DeathCause.COMBAT, tick=100, last_attacker_id=9)


def test_a_starvation_death_names_the_body_that_last_hit_it():
    ent = _body(hp=0, alive=False, last_attacker_id=5)
    ent = replace(ent, lifecycle=replace(ent.lifecycle, passive_death_cause=PassiveDeathCause.STARVATION, passive_death_cause_tick=99))
    state = AuthoritativeState(tick=100, seed=1, entities={1: ent})
    record = LifecycleSystem.resolve_lifecycle(state, StateUpdate()).entity_updates[1].lifecycle.death_record_set
    assert record.cause is DeathCause.STARVATION and record.last_attacker_id == 5 and record.hazard_kind is None


def test_a_never_hit_body_has_no_last_attacker():
    ent = _body(hp=0, alive=False)
    ent = replace(ent, lifecycle=replace(ent.lifecycle, passive_death_cause=PassiveDeathCause.STARVATION, passive_death_cause_tick=99))
    record = LifecycleSystem.resolve_lifecycle(AuthoritativeState(tick=100, seed=1, entities={1: ent}), StateUpdate()).entity_updates[1].lifecycle.death_record_set
    assert record.last_attacker_id is None


def test_a_hazard_death_names_the_hazard_kind_of_the_region_it_stood_in():
    state = _at_tick(_world(), 100)
    x, y = state.entities[WHO].navigation.position
    region = resolve_region_among(state.regions.values(), x, y)
    assert region is not None
    haz = CombatUpdate(outcome_kind="HAZARD", alive_set=False, hazard_damage=3, hp_delta=-3)
    upd = LifecycleSystem.resolve_lifecycle(state, StateUpdate(entity_updates={WHO: EntityUpdate(entity_id=WHO, combat=haz)})).entity_updates[WHO]
    assert upd.lifecycle.death_record_set == DeathRecord(cause=DeathCause.HAZARD, tick=100, hazard_kind=region.hazard_kind)


def test_the_record_is_applied_through_the_authoritative_path_and_enters_the_canonical_state():
    ent = _body()
    state = AuthoritativeState(tick=100, seed=1, entities={1: ent})
    record = DeathRecord(cause=DeathCause.HAZARD, tick=100, last_attacker_id=4, hazard_kind="NATURAL_TERRAIN")
    nxt = ApplyPath.apply_generation(state, StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, lifecycle=LifecycleUpdate(death_record_set=record))}), 101, 101)
    assert nxt.entities[1].lifecycle.death_record == record and state.entities[1].lifecycle.death_record is None
    assert nxt.entities[1].lifecycle.to_canonical_dict()["death_record"] == record.to_dict()
    assert state.entities[1].lifecycle.to_canonical_dict()["death_record"] is None


def test_the_record_round_trips_and_an_unset_record_is_none():
    for record in (DeathRecord(DeathCause.COMBAT, 7, 3, None), DeathRecord(DeathCause.HAZARD, 9, None, "UNDEAD_CORRUPTION"), DeathRecord(DeathCause.OLD_AGE, 1)):
        assert DeathRecord.from_dict(record.to_dict()) == record
    assert LifecycleUpdate().is_noop() and not LifecycleUpdate(death_record_set=DeathRecord(DeathCause.COMBAT, 1)).is_noop()
    merged = LifecycleUpdate().merge(LifecycleUpdate(death_record_set=DeathRecord(DeathCause.COMBAT, 1)))
    assert merged.death_record_set == DeathRecord(DeathCause.COMBAT, 1)


def _hit(state, **fields):
    return ApplyPath.apply_generation(state, StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate(**fields))}), 101, 101).entities[1]


def test_a_damaging_hit_is_remembered_and_a_hazard_or_a_miss_leaves_it_alone():
    state = AuthoritativeState(tick=100, seed=1, entities={1: _body(hp=50, max_hp=50)})
    hit = _hit(state, attacker_id=8, damage_taken=4, hp_delta=-4)
    assert hit.combat.last_attacker_id == 8
    after_hazard = _hit(AuthoritativeState(tick=101, seed=1, entities={1: hit}), hazard_damage=2, hp_delta=-2)
    assert after_hazard.combat.last_attacker_id == 8
    after_miss = _hit(AuthoritativeState(tick=101, seed=1, entities={1: hit}), attacker_id=3, damage_taken=0)
    assert after_miss.combat.last_attacker_id == 8
    assert state.entities[1].combat.last_attacker_id is None
    assert hit.combat.to_canonical_dict()["last_attacker_id"] == 8


def test_the_last_attacker_is_the_most_recent_hit_at_any_time_before_death_with_no_recency():
    """A scratch at tick 100 is still named by a hazard death at tick 2100: recency is not recorded (a follow-up if testing or SimQ need it)."""
    hit = _hit(AuthoritativeState(tick=100, seed=1, entities={1: _body(hp=50, max_hp=50)}), attacker_id=8, damage_taken=1, hp_delta=-1)
    late = AuthoritativeState(tick=2100, seed=1, entities={1: replace(hit, combat=replace(hit.combat, hp=0, alive=False))})
    haz = CombatUpdate(outcome_kind="HAZARD", alive_set=False, hazard_damage=1, hp_delta=-1)
    record = LifecycleSystem.resolve_lifecycle(late, StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=haz)})).entity_updates[1].lifecycle.death_record_set
    assert record.cause is DeathCause.HAZARD and record.tick == 2100 and record.last_attacker_id == 8
