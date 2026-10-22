"""A carcass the decay step removes and a same-tick meal puts back gets no decay record that tick (TCK-20261022-NO-MEAT-DECAYED-RECORD-FOR-A-CARCASS-RE-ADDED-ON-ITS-DECAY-TICK).

`MEAT_DECAYED` is written by the world-dynamics step from the tick-start state, before the transfers resolve. A hungry subject eating at a carcass on the tick it is
due to decay (EAT, CORPSE_FOOD) leaves a smaller body in `corpses_add_or_update`; the apply path removes the decayed body and then re-inserts that one, so the body
survives and decays a tick late. The record then claimed meat that never left (v1 gate: crowded_frontier/44 3.0 at t1604, frontier_living_world/46 1.0 at t2575),
and the V2/H7 check (decay records vs vanished bodies) failed by that meat. The record is written from the applied outcome: none now, one when the body leaves.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

import src.core.registries  # noqa: F401  (seeds the item registry from content)
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState, ItemStack
from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
from src.domains.world_emergence.schema import WorldEventCategory
from src.engine import behavior_consumers
from src.engine.apply import ApplyPath
from src.engine.carcass import RAW_MEAT_ITEM
from src.engine.domain.core_actions import corpse_meal
from src.engine.economy import ResourceTransactionSystem
from src.engine.world_dynamics import WorldDynamicsSystem
from src.observability.rpg_gate_metrics import _check_meat_books
from src.observability.run_ledger import RunLedger
from src.systems.world_systems.generator import EntityGenerator


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository

    repo = CatalogRepository("data/content")
    repo.load_all()
    behavior_consumers.configure_behavior_consumers(repo)
    yield
    behavior_consumers.reset_behavior_consumers()


@pytest.fixture(autouse=True)
def _ledger():
    RunLedger.reset_run_state()
    RunLedger.configure(True)
    yield
    RunLedger.reset_run_state()


def _creature(eid, species, pos, hunger=90.0):
    return (V2EntityBuilder(eid).kind("monster").location(*pos)
            .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, properties={"species_id": species})
            .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True).lifecycle(active=True)
            .biological(hunger=hunger).build())


def _world_with_a_body_of(meat: int):
    """(state with orc 1's body holding exactly `meat` raw meat, the body); its meat is `made` in the ledger."""
    s0 = AuthoritativeState(tick=1, seed=42, entities={1: _creature(1, "orc", (10.0, 10.0)), 9: _creature(9, "wolf", (11.0, 10.0))})
    deaths = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate(hp_delta=-500, alive_set=False))})
    s1 = ApplyPath.apply_generation(s0, deaths, next_tick=2)
    body = replace(next(iter(s1.corpses.values())), items=[ItemStack(item_id=RAW_MEAT_ITEM, quantity=meat)])
    state = replace(s1, corpses={body.id: body})
    RunLedger._count_meat(s0, state, deaths)
    return state, body


def _decay_tick(state, eater=None):
    """Run one decay tick at the body's decay tick: the decay step, then the economy with the eater's meal at the carcass (if any), then the apply path."""
    body = next(iter(state.corpses.values()))
    tick_state = replace(state, tick=max(state.tick, body.decay_tick))
    update = WorldDynamicsSystem.resolve_dynamics(tick_state, StateUpdate(), EntityGenerator(42))
    if eater is not None:
        meal = corpse_meal(tick_state.entities[eater], body, tick_state.tick)
        assert meal, "the eater has a meal at the carcass"
        update = replace(update, entity_updates={eater: EntityUpdate(entity_id=eater, resource_transfers=meal)})
    resolved = ResourceTransactionSystem.resolve_all(tick_state, update)
    current = ApplyPath.apply_generation(tick_state, resolved, next_tick=tick_state.tick + 1)
    RunLedger._count_world_events(resolved)
    RunLedger._count_meat(tick_state, current, resolved)
    return resolved, current


def _records(resolved):
    return [e for e in resolved.world_events_add if e.category == WorldEventCategory.MEAT_DECAYED]


def _books(current):
    ledger = {"meat": dict(RunLedger._meat)}
    return _check_meat_books(ledger, current, float(RunLedger._world_events.get("meat_decayed_quantity", 0.0))), ledger


def test_a_partial_meal_on_the_decay_tick_leaves_no_record_that_tick_and_the_remainder_is_recorded_when_the_body_leaves():
    """The crowded_frontier/44 case: 3 meat, one eaten on the decay tick, 2 left; the body survives the apply and decays the next tick."""
    state, body = _world_with_a_body_of(3)
    resolved, current = _decay_tick(state, eater=9)

    assert body.id in resolved.corpses_remove, "the decay step still removes it; the apply path keeps the re-added body (the decay timing is a separate ticket)"
    assert [c.id for c in resolved.corpses_add_or_update] == [body.id]
    assert _records(resolved) == [], "the body did not leave this tick, so no record of meat leaving"
    assert body.id in current.corpses and sum(s.quantity for s in current.corpses[body.id].items) == 2
    (count, found), ledger = _books(current)
    assert (count, found) == (0, []), found
    assert ledger["meat"].get("taken") == 1.0 and ledger["meat"].get("vanished", 0.0) == 0.0

    resolved2, current2 = _decay_tick(current)  # the next tick: the remainder leaves and is recorded with the meat it still holds
    assert [float(e.payload["quantity"]) for e in _records(resolved2)] == [2.0]
    (count, found), ledger = _books(current2)
    assert (count, found) == (0, []), found
    assert ledger["meat"]["made"] == ledger["meat"]["taken"] + ledger["meat"]["vanished"] == 3.0


def test_the_last_meat_eaten_on_the_decay_tick_leaves_no_meat_record_at_all():
    """The frontier_living_world/46 case: 1 meat, eaten on the decay tick; the empty body is kept and leaves a tick later with no meat to record."""
    state, body = _world_with_a_body_of(1)
    resolved, current = _decay_tick(state, eater=9)

    assert _records(resolved) == []
    assert body.id in current.corpses and sum(s.quantity for s in current.corpses[body.id].items) == 0
    resolved2, current2 = _decay_tick(current)
    assert _records(resolved2) == [], "an empty body has no meat to send out of the world"
    (count, found), ledger = _books(current2)
    assert (count, found) == (0, []), found
    assert ledger["meat"]["made"] == ledger["meat"]["taken"] == 1.0 and RunLedger._world_events.get("meat_decayed_quantity", 0.0) == 0.0


def test_a_body_that_decays_with_nobody_eating_keeps_its_one_record():
    """The control: nothing re-adds the body, so the record stays and the books agree (the existing behaviour is unchanged)."""
    state, body = _world_with_a_body_of(3)
    resolved, current = _decay_tick(state)

    assert [float(e.payload["quantity"]) for e in _records(resolved)] == [3.0]
    assert body.id not in current.corpses
    assert _books(current)[0] == (0, [])
