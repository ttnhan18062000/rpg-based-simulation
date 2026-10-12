"""M0 gate H6: a starvation death writes one typed record of the food ways the subject's pull judged open and in reach, and the ways it tried.

Staged on single states and updates (the recorder is a pure observer), plus one run through EventExtractor for the live header, the tally and
the OFF mode. Ways are asserted by kind, never by number.
"""
from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from src.ai.goals.ways import WayKind, ways_in_reach
from src.core.enums import PassiveDeathCause
from src.core.inventory import ItemStack
from src.engine.need_pull import ESCALATION_ONSET, HUNGER_LINE
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.run_state import EventExtractor, extract_events
from src.observability.starvation_record import (CHANNEL_LIVE_EVENT, CHANNEL_TALLY_EVENT, RECORD_EVENT, StarvationRecorder, _judged_ways)
from tests.helpers.scenario import compile_world

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
WHO = 2
HUNGRY = ESCALATION_ONSET * HUNGER_LINE + 5.0
SAMPLE_TICK = 10 * 7 - WHO % 10  # a strategic re-decision tick for this subject at the default cadence: (tick + id) % 10 == 0


@pytest.fixture(autouse=True)
def _clean():
    StarvationRecorder.reset_run_state()
    EventExtractor.reset_run_state()
    yield
    StarvationRecorder.reset_run_state()


def _world(carry=(), species=None, hunger=HUNGRY):
    state = compile_world(WORLD_ID)
    e = state.entities[WHO]
    props = dict(e.identity.properties)
    if species:
        props["species_id"] = species
    e = replace(e, biological=replace(e.biological, hunger=hunger, sleep_debt=0.0), identity=replace(e.identity, properties=props),
                inventory=replace(e.inventory, items=[ItemStack(item_id=i, quantity=1) for i in carry]))
    object.__setattr__(state, "entities", {WHO: e})
    object.__setattr__(state, "buildings", {})
    object.__setattr__(state, "resource_nodes", {})
    object.__setattr__(state, "corpses", {})
    return state


def _at_tick(state, tick):
    object.__setattr__(state, "tick", tick)
    return state


def _dying(state, tick):
    """The state after the fatal tick: the writer stamped the typed cause."""
    e = state.entities[WHO]
    dead = replace(e, lifecycle=replace(e.lifecycle, passive_death_cause=PassiveDeathCause.STARVATION, passive_death_cause_tick=tick))
    cur = replace(state, tick=tick)
    object.__setattr__(cur, "entities", {WHO: dead})
    return cur


def _update(*results):
    return SimpleNamespace(entity_updates={WHO: SimpleNamespace(intent_results=list(results))})


def _result(source_kind, accepted=False, source_id="x"):
    return SimpleNamespace(source_kind=source_kind, accepted=accepted, source_id=source_id)


def _records(events):
    return [e for e in events if e.event_type == RECORD_EVENT]


def test_a_death_with_an_untried_way_in_reach_is_recorded_as_untried():
    prior = _at_tick(_world(carry=["bread"]), SAMPLE_TICK)
    assert WayKind.CARRIED_FOOD in ways_in_reach(prior.entities[WHO], prior)
    StarvationRecorder.observe(prior, prior, SimpleNamespace(entity_updates={}))  # the re-decision tick: the pull judges its ways
    events = StarvationRecorder.observe(prior, _dying(prior, SAMPLE_TICK + 3), _update())
    (rec,) = _records(events)
    assert rec.payload["entity_id"] == WHO and rec.payload["cause_tick"] == SAMPLE_TICK + 3
    assert "CARRIED_FOOD" in rec.payload["ways_open_in_reach_union"]
    assert rec.payload["ways_attempted"] == []


def test_a_death_with_every_way_tried_has_nothing_untried():
    prior = _at_tick(_world(carry=["bread"]), SAMPLE_TICK)
    StarvationRecorder.observe(prior, prior, SimpleNamespace(entity_updates={}))
    StarvationRecorder.observe(prior, prior, _update(_result("CARRIED_FOOD", accepted=False)))  # tried, rejected
    (rec,) = _records(StarvationRecorder.observe(prior, _dying(prior, SAMPLE_TICK + 3), _update()))
    assert rec.payload["ways_attempted"] == ["CARRIED_FOOD"]
    assert set(rec.payload["ways_open_in_reach_union"]) <= set(rec.payload["ways_attempted"])


def test_the_union_keeps_a_way_that_was_open_on_an_earlier_decision_but_not_at_death():
    early = _at_tick(_world(carry=["bread"]), SAMPLE_TICK)
    StarvationRecorder.observe(early, early, SimpleNamespace(entity_updates={}))
    later = _at_tick(_world(carry=[]), SAMPLE_TICK + 10)  # the food is gone by the next decision
    (rec,) = _records(StarvationRecorder.observe(later, _dying(later, SAMPLE_TICK + 13), _update()))
    assert "CARRIED_FOOD" in rec.payload["ways_open_in_reach_union"]
    assert "CARRIED_FOOD" not in rec.payload["ways_in_reach_at_death"]


def test_a_meal_resets_the_trail():
    prior = _at_tick(_world(carry=["bread"]), SAMPLE_TICK)
    StarvationRecorder.observe(prior, prior, SimpleNamespace(entity_updates={}))
    ate = replace(prior.entities[WHO], biological=replace(prior.entities[WHO].biological, hunger=HUNGRY - 30.0))
    after = replace(prior, tick=SAMPLE_TICK + 1)
    object.__setattr__(after, "entities", {WHO: ate})
    StarvationRecorder.observe(prior, after, _update(_result("CARRIED_FOOD", accepted=True)))
    later = _at_tick(_world(carry=[]), SAMPLE_TICK + 20)
    (rec,) = _records(StarvationRecorder.observe(later, _dying(later, SAMPLE_TICK + 23), _update()))
    assert rec.payload["ways_open_in_reach_union"] == [] and rec.payload["ways_attempted"] == []
    assert rec.payload["last_meal_tick"] == SAMPLE_TICK + 1


def test_a_diet_restricted_kind_lists_only_its_ways():
    wolf = _at_tick(_world(carry=["bread"], species="wolf"), SAMPLE_TICK)
    assert WayKind.CARRIED_FOOD not in ways_in_reach(wolf.entities[WHO], wolf), "a meat-only body cannot eat prepared bread"
    person = _at_tick(_world(carry=["bread"]), SAMPLE_TICK)
    assert WayKind.CARRIED_FOOD in ways_in_reach(person.entities[WHO], person)


def test_exactly_one_record_per_death():
    prior = _at_tick(_world(), SAMPLE_TICK)
    cur = _dying(prior, SAMPLE_TICK + 3)
    first = _records(StarvationRecorder.observe(prior, cur, _update()))
    again = _records(StarvationRecorder.observe(prior, cur, _update()))
    assert len(first) == 1 and again == []


def test_a_non_starvation_death_or_an_earlier_cause_tick_writes_no_record():
    prior = _at_tick(_world(), SAMPLE_TICK)
    e = prior.entities[WHO]
    other = replace(prior, tick=SAMPLE_TICK + 3)
    object.__setattr__(other, "entities", {WHO: replace(e, lifecycle=replace(e.lifecycle, passive_death_cause=PassiveDeathCause.STARVATION,
                                                                              passive_death_cause_tick=SAMPLE_TICK))})  # stamped on an earlier tick
    assert _records(StarvationRecorder.observe(prior, other, _update())) == []


def test_the_judged_set_equals_the_true_map_until_honest_perception_exists():
    """Column (a) and column (b) are the same today; only M1's honest-perception child may split them (then this pin is replaced)."""
    for carry, species in ((["bread"], None), ([], None), (["bread"], "wolf")):
        state = _world(carry=carry, species=species)
        assert _judged_ways(state.entities[WHO], state) == ways_in_reach(state.entities[WHO], state)


def test_the_record_is_deterministic_across_two_runs():
    payloads = []
    for _ in range(2):
        StarvationRecorder.reset_run_state()
        prior = _at_tick(_world(carry=["bread"]), SAMPLE_TICK)
        StarvationRecorder.observe(prior, prior, SimpleNamespace(entity_updates={}))
        (rec,) = _records(StarvationRecorder.observe(prior, _dying(prior, SAMPLE_TICK + 3), _update()))
        payloads.append(rec.payload)
    assert payloads[0] == payloads[1]


def test_a_live_run_opens_with_the_header_and_closes_with_a_tally_that_matches_the_records():
    prior = _at_tick(_world(), SAMPLE_TICK)
    first = extract_events(prior, prior, SimpleNamespace(entity_updates={}))
    assert [e.event_type for e in first].count(CHANNEL_LIVE_EVENT) == 1
    died = extract_events(prior, _dying(prior, SAMPLE_TICK + 3), _update())
    assert [e.event_type for e in died].count(CHANNEL_LIVE_EVENT) == 0 and len(_records(died)) == 1
    tally = StarvationRecorder.tally_event(SAMPLE_TICK + 4)
    assert tally.event_type == CHANNEL_TALLY_EVENT
    assert tally.payload == {"starvation_deaths_seen": 1, "records_emitted": 1}


def test_an_off_mode_run_has_no_header_so_the_channel_reads_as_not_live():
    prior = _at_tick(_world(), SAMPLE_TICK)
    assert extract_events(prior, _dying(prior, SAMPLE_TICK + 3), _update(), ObservabilityMode.OFF) == []  # the kernel passes the mode
    assert StarvationRecorder._header_sent is False


def test_reset_run_state_clears_the_trail_the_counts_and_the_header():
    prior = _at_tick(_world(carry=["bread"]), SAMPLE_TICK)
    StarvationRecorder.observe(prior, prior, SimpleNamespace(entity_updates={}))
    StarvationRecorder.observe(prior, _dying(prior, SAMPLE_TICK + 3), _update())
    StarvationRecorder.reset_run_state()
    assert not StarvationRecorder._union and not StarvationRecorder._attempted and not StarvationRecorder._recorded
    assert StarvationRecorder._deaths_seen == 0 and StarvationRecorder._header_sent is False


def test_a_real_kernel_run_writes_the_header_one_record_and_a_matching_tally(monkeypatch):
    """End to end through the kernel's observability phase: a lone starving person dies, the record and the live header are in its events."""
    from src.config.profiles import PROD_SMALL
    from src.engine.executor import LocalSequentialExecutor
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG
    from tests.helpers.scenario import DEFAULT_FLAGS, DEFAULT_SEED

    monkeypatch.setattr("src.engine.apply.need_rates", lambda entity: (0.5, 0.0))
    monkeypatch.setattr("src.engine.starvation.hp_loss_period", lambda max_hp: 20)  # the staged body loses its one HP within a few ticks of the line
    state = _world(hunger=94.0)
    e = state.entities[WHO]
    object.__setattr__(state, "entities", {WHO: replace(e, combat=replace(e.combat, hp=1, max_hp=1, atk=1))})
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(DEFAULT_SEED),
                    flags={**DEFAULT_FLAGS, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
    seen = []
    kernel._event_listeners.append(lambda events: seen.extend(events))
    try:
        for _ in range(4000):
            kernel.tick_once()
            if not kernel._state.entities[WHO].combat.alive:
                break
        tally = StarvationRecorder.tally_event(kernel._state.tick)
    finally:
        kernel.shutdown()
        ObservabilityConfig.set_override_mode(None)
    assert not kernel._state.entities[WHO].combat.alive, "the staged subject never starved"
    assert [e.event_type for e in seen].count(CHANNEL_LIVE_EVENT) == 1
    assert len(_records(seen)) == 1 and tally.payload["starvation_deaths_seen"] == 1
    assert all(e.severity == "WARNING" for e in seen if e.source_system == "starvation_record"), "INFO would be dropped or sampled under pressure"
    assert kernel._event_recorder.event_count_by_type.get(CHANNEL_TALLY_EVENT) == 1, "shutdown must close the channel with its tally"


def test_a_meat_eater_with_prey_and_a_carcass_in_reach_lists_hunt_and_scavenge_and_no_plant_or_inn_way():
    """Diet decides the ways (D42/D44): the hunting batch's real kinds stand in (wolf: meat-only; goblin: believed low danger)."""
    from src.core.state import AuthoritativeState, CorpseState, ItemStack
    from tests.unit.ai.test_hunt_steps import _carcass, _goblin, _wolf, _consumers  # noqa: F401 (the module-scoped consumer fixture)

    wolf, goblin, carcass = _wolf(), _goblin(), _carcass()
    state = AuthoritativeState(tick=5, seed=1, entities={wolf.id: wolf, goblin.id: goblin}, corpses={carcass.id: carcass})
    ways = ways_in_reach(wolf, state)
    assert WayKind.HUNT_EAT_RAW in ways and WayKind.SCAVENGE in ways
    assert WayKind.INN_MEAL not in ways and WayKind.FORAGE not in ways
