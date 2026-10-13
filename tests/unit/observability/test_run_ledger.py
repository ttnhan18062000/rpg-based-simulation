"""M0 gate run ledger: the run-scoped counters the gate's validity and outcome rows read (transfers, hunger drops, deaths, adds by source, coin,
population, meat events), grouped by what a kind's diet declares, with a live header and one closing tally. Staged on single states and updates
(the ledger is a pure observer); groups are asserted by what the diet declares, never by a number tuned to the world.
"""
from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from src.ai.goals.kind_group import NO_DIET, UNDECLARED, kind_group, species_kind_group
from src.core.builder import V2EntityBuilder
from src.core.spawn_source import SpawnKind, SpawnSource
from src.observability.run_ledger import (
    LEDGER_LIVE_EVENT,
    LEDGER_TALLY_EVENT,
    POPULATION_SAMPLE_EVERY,
    UNSOURCED,
    RunLedger,
)
from tests.unit.observability.test_starvation_death_record import WHO, _at_tick, _world


@pytest.fixture(autouse=True)
def _clean():
    RunLedger.reset_run_state()
    RunLedger.configure(True)
    yield
    RunLedger.reset_run_state()


def _entity_update(*results):
    return SimpleNamespace(intent_results=list(results))


def _update(results=(), adds=(), sources=None, world_events=()):
    return SimpleNamespace(entity_updates={WHO: _entity_update(*results)}, entities_add=list(adds), entity_spawn_sources=sources or {},
                           world_events_add=list(world_events))


def _result(source_kind, accepted=True):
    return SimpleNamespace(source_kind=source_kind, accepted=accepted, source_id="x")


def _fed(state, hunger):
    e = state.entities[WHO]
    cur = replace(state)
    object.__setattr__(cur, "entities", {WHO: replace(e, biological=replace(e.biological, hunger=hunger))})
    return cur


def _tally(prior=None, current=None, update=None):
    prior = prior or _at_tick(_world(carry=["bread"]), 10)
    RunLedger.observe(prior, current or prior, update or _update())
    return RunLedger.tally_event().payload


def test_kind_groups_come_from_the_declared_diet_not_from_a_role():
    assert species_kind_group(None) == UNDECLARED
    assert kind_group(_world().entities[WHO]) != kind_group(_world(species="wolf").entities[WHO])
    assert "meat" in species_kind_group("wolf").split("+")


def test_the_live_header_opens_the_run_once_and_the_tally_closes_it():
    state = _at_tick(_world(), 10)
    first = RunLedger.observe(state, state, _update())
    again = RunLedger.observe(state, state, _update())
    assert [e.event_type for e in first] == [LEDGER_LIVE_EVENT] and again == []
    tally = RunLedger.closing_event({LEDGER_LIVE_EVENT: 1})
    assert tally is not None and tally.event_type == LEDGER_TALLY_EVENT and tally.severity == "WARNING"
    assert RunLedger.closing_event({}) is None  # a recorder that never saw the header writes no tally


def test_a_profile_with_no_observability_budget_leaves_the_ledger_silent():
    RunLedger.configure(False)
    state = _at_tick(_world(), 10)
    assert RunLedger.observe(state, state, _update()) == []
    assert RunLedger.closing_event({LEDGER_LIVE_EVENT: 1}).payload["first_tick"] is None  # never opened: nothing was observed


def test_accepted_and_rejected_transfers_are_counted_by_group_and_source():
    state = _at_tick(_world(carry=["bread"]), 10)
    group = kind_group(state.entities[WHO])
    payload = _tally(state, update=_update([_result("CARRIED_FOOD"), _result("TOWN_SERVICE", accepted=False)]))
    assert payload["transfers"] == {f"{group}|CARRIED_FOOD|accepted": 1, f"{group}|TOWN_SERVICE|rejected": 1}


def test_a_hunger_drop_is_counted_with_or_without_an_accepted_transfer():
    state = _at_tick(_world(carry=["bread"], hunger=80.0), 10)
    group = kind_group(state.entities[WHO])
    RunLedger.observe(state, _fed(state, 60.0), _update([_result("CARRIED_FOOD")]))
    RunLedger.observe(state, _fed(state, 50.0), _update([]))
    assert RunLedger.tally_event().payload["hunger_drops"] == {f"{group}|with_accepted_transfer": 1, f"{group}|without_transfer": 1}


def test_a_death_is_counted_by_group_and_cause():
    state = _at_tick(_world(), 10)
    e = state.entities[WHO]
    dead = replace(state)
    object.__setattr__(dead, "entities", {WHO: replace(e, combat=replace(e.combat, alive=False), lifecycle=replace(e.lifecycle, death_reason="combat"))})
    assert _tally(state, dead)["deaths"] == {f"{kind_group(e)}|combat": 1}


def test_an_add_is_counted_by_its_declared_source_or_as_unsourced_and_its_purse_is_declared_coin():
    state = _at_tick(_world(), 10)
    base = V2EntityBuilder(500).build()
    born = replace(base, inventory=replace(base.inventory, gold=7))
    arrived = V2EntityBuilder(501).build()
    update = _update(adds=[born, arrived], sources={500: SpawnSource(SpawnKind.BIRTH, parent_ids=(1, 2))})
    payload = _tally(state, update=update)
    group = kind_group(born)
    assert payload["adds"] == {f"{group}|BIRTH": 1, f"{kind_group(arrived)}|{UNSOURCED}": 1}
    assert payload["declared_coin"] == 7.0


def test_coin_is_recorded_at_the_first_and_the_last_observed_tick():
    state = _at_tick(_world(), 10)
    richer = replace(state)
    e = state.entities[WHO]
    object.__setattr__(richer, "entities", {WHO: replace(e, inventory=replace(e.inventory, gold=e.inventory.gold + 5))})
    RunLedger.observe(state, state, _update())
    RunLedger.observe(state, richer, _update())
    payload = RunLedger.tally_event().payload
    assert payload["coin_last"] - payload["coin_first"] == 5.0


def test_population_is_sampled_at_the_first_tick_and_every_sample_period_by_group():
    state = _at_tick(_world(), 10)
    RunLedger.observe(state, state, _update())
    later = _at_tick(_world(), POPULATION_SAMPLE_EVERY)
    RunLedger.observe(later, later, _update())
    population = RunLedger.tally_event().payload["population"]
    assert set(population) == {"10", str(POPULATION_SAMPLE_EVERY)}
    assert population["10"] == {kind_group(state.entities[WHO]): 1}


def test_meat_events_are_counted_with_the_decayed_quantity():
    kill = SimpleNamespace(category=SimpleNamespace(name="FEEDING_KILL"), payload={})
    decay = SimpleNamespace(category=SimpleNamespace(name="MEAT_DECAYED"), payload={"quantity": 3.5})
    other = SimpleNamespace(category=SimpleNamespace(name="TERRITORY_TRANSFERRED"), payload={})
    events = _tally(update=_update(world_events=[kill, decay, decay, other]))["world_events"]
    assert events == {"FEEDING_KILL": 1, "MEAT_DECAYED": 2, "meat_decayed_quantity": 7.0}


def test_the_tally_is_deterministic_across_two_runs():
    payloads = []
    for _ in range(2):
        RunLedger.reset_run_state()
        RunLedger.configure(True)
        state = _at_tick(_world(carry=["bread"]), 10)
        RunLedger.observe(state, _fed(state, 5.0), _update([_result("CARRIED_FOOD")]))
        payloads.append(RunLedger.tally_event().payload)
    assert payloads[0] == payloads[1]


def test_reset_clears_every_counter():
    _tally(update=_update([_result("CARRIED_FOOD")]))
    RunLedger.reset_run_state()
    payload = RunLedger.tally_event().payload
    assert not payload["transfers"] and not payload["population"] and payload["first_tick"] is None


def test_a_real_kernel_run_writes_the_header_and_the_shutdown_tally_with_the_staged_world_counted(monkeypatch):
    """End to end through the kernel's observability phase and shutdown: the live header, the tally at close, WARNING severity, one subject sampled."""
    from src.config.profiles import PROD_SMALL
    from src.engine.executor import LocalSequentialExecutor
    from src.engine.kernel import Kernel
    from src.observability.config import ObservabilityConfig, ObservabilityMode
    from src.platform.rng import DeterministicRNG
    from tests.helpers.scenario import DEFAULT_FLAGS, DEFAULT_SEED

    state = _world(hunger=10.0)
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(DEFAULT_SEED),
                    flags={**DEFAULT_FLAGS, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
    seen = []
    kernel._event_listeners.append(lambda events: seen.extend(events))
    try:
        for _ in range(3):
            kernel.tick_once()
        tally = RunLedger.tally_event()
    finally:
        kernel.shutdown()
        ObservabilityConfig.set_override_mode(None)
    assert [e.event_type for e in seen].count(LEDGER_LIVE_EVENT) == 1
    assert all(e.severity == "WARNING" for e in seen if e.source_system == "run_ledger")
    assert sum(tally.payload["population"][str(tally.payload["first_tick"])].values()) == 1
    assert kernel._event_recorder.event_count_by_type.get(LEDGER_TALLY_EVENT) == 1, "shutdown must close the ledger with its tally"


def _with_corpses(state, corpses, tick=11):
    cur = replace(state, tick=tick)
    object.__setattr__(cur, "corpses", corpses)
    return cur


def _corpse(cid, meat):
    from src.core.state import CorpseState, ItemStack
    return CorpseState(id=cid, original_entity_id=cid, position=(0.0, 0.0), decay_tick=10**6, items=[ItemStack(item_id="raw_meat", quantity=meat)] if meat else [])


def test_the_ledgers_raw_meat_name_is_the_engines():
    from src.engine.carcass import RAW_MEAT_ITEM
    from src.observability import run_ledger
    assert run_ledger._RAW_MEAT == RAW_MEAT_ITEM


def test_meat_is_counted_as_made_taken_and_vanished_across_ticks():
    base = _at_tick(_world(), 10)
    RunLedger.observe(base, _with_corpses(base, {1: _corpse(1, 6)}), _update())  # a body appears with 6 meat
    one = _with_corpses(base, {1: _corpse(1, 6)})
    RunLedger.observe(one, _with_corpses(base, {1: _corpse(1, 4)}, 12), _update())  # 2 taken (eaten or looted)
    two = _with_corpses(base, {1: _corpse(1, 4)}, 12)
    RunLedger.observe(two, _with_corpses(base, {}, 13), _update())  # the body leaves the world holding 4
    assert RunLedger.tally_event().payload["meat"] == {"made": 6.0, "taken": 2.0, "vanished": 4.0}


def test_a_moved_entity_outside_the_world_extent_is_counted_with_an_example():
    state = _at_tick(_world(), 10)
    e = state.entities[WHO]
    out = replace(state)
    object.__setattr__(out, "entities", {WHO: replace(e, navigation=replace(e.navigation, position=(1.0e6, 1.0e6)))})
    payload = _tally(state, out)
    assert payload["out_of_world"] == {kind_group(e): 1} and payload["out_of_world_examples"][0]["entity_id"] == WHO


def test_attacks_and_kills_are_counted_by_attacker_and_victim_group():
    wolf, villager = _world(species="wolf").entities[WHO], _world().entities[WHO]
    state = _at_tick(_world(), 10)
    object.__setattr__(state, "entities", {WHO: villager, 99: replace(wolf, id=99)})
    hit = SimpleNamespace(attacker_id=99, hp_delta=-3, outcome_kind="SURVIVE")
    kill = SimpleNamespace(attacker_id=99, hp_delta=-9, outcome_kind="KILL")
    plain = SimpleNamespace(attacker_id=None, hp_delta=-1, outcome_kind="SURVIVE")  # starvation or hazard: not an attack
    for combat in (hit, kill, plain):
        RunLedger.observe(state, state, SimpleNamespace(entity_updates={WHO: SimpleNamespace(intent_results=[], combat=combat)}, entities_add=[], entity_spawn_sources={}, world_events_add=[]))
    a, v = kind_group(wolf), kind_group(villager)
    assert RunLedger.tally_event().payload["attacks"] == {f"{a}|{v}|hit": 1, f"{a}|{v}|kill": 1}
