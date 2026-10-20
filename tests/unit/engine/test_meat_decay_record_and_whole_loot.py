"""A body that decays on the tick an accepted whole-body loot takes it gets one record, the loot (TCK-20261019-V2-MEAT-DECAYED-WRITTEN-FROM-THE-APPLIED-OUTCOME).

`MEAT_DECAYED` is written by the world-dynamics step before the transfers resolve; a body due to decay on tick T and looted whole on T used to carry a decay record
for meat the looter received, so the run ledger (looted) and the record (decayed) disagreed by that meat and the V2/H7 check (gate seed crowded/43, 2 units) failed.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

import src.core.registries  # noqa: F401  (seeds the item registry from content)
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.core.updates import CombatUpdate, EntityUpdate, ResourceTransferIntent, StateUpdate
from src.domains.world_emergence.schema import WorldEventCategory
from src.engine import behavior_consumers
from src.engine.apply import ApplyPath
from src.engine.carcass import RAW_MEAT_ITEM
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


def _creature(eid, species, pos):
    return (V2EntityBuilder(eid).kind("monster").location(*pos)
            .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, properties={"species_id": species})
            .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True).lifecycle(active=True)
            .biological(hunger=90.0).build())


def _world_with_one_body():
    """(state before the death, state with orc 1's body, the body id, its meat)."""
    orc = _creature(1, "orc", (10.0, 10.0))
    looter = _creature(9, "wolf", (11.0, 10.0))
    s0 = AuthoritativeState(tick=1, seed=42, entities={1: orc, 9: looter})
    deaths = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate(hp_delta=-500, alive_set=False))})
    s1 = ApplyPath.apply_generation(s0, deaths, next_tick=2)
    body = next(iter(s1.corpses.values()))
    meat = sum(s.quantity for s in body.items if s.item_id == RAW_MEAT_ITEM)
    assert meat > 0
    RunLedger._count_meat(s0, s1, deaths)  # the body's meat is "made" when it appears
    return s1, body, meat


def _decay_tick_update(state, looted: bool):
    decay_state = replace(state, tick=next(iter(state.corpses.values())).decay_tick)
    update = WorldDynamicsSystem.resolve_dynamics(decay_state, StateUpdate(), EntityGenerator(42))
    assert [e for e in update.world_events_add if e.category == WorldEventCategory.MEAT_DECAYED], "the decay step writes its record before the transfers resolve"
    if looted:
        body = next(iter(decay_state.corpses.values()))
        intent = ResourceTransferIntent(source_id=body.id, source_kind="CORPSE", items_add=list(body.items), transfer_kind="LOOT")
        update = replace(update, entity_updates={9: EntityUpdate(entity_id=9, resource_transfers=[intent])})
    return decay_state, ResourceTransactionSystem.resolve_all(decay_state, update)


def _books_after(decay_state, resolved):
    current = ApplyPath.apply_generation(decay_state, resolved, next_tick=decay_state.tick + 1)
    RunLedger._count_world_events(resolved)
    RunLedger._count_meat(decay_state, current, resolved)
    ledger = {"meat": dict(RunLedger._meat)}
    return ledger, float(RunLedger._world_events.get("meat_decayed_quantity", 0.0)), current


def test_a_body_that_decays_and_is_looted_whole_on_one_tick_gets_the_loot_and_no_decay_record():
    state, body, meat = _world_with_one_body()
    decay_state, resolved = _decay_tick_update(state, looted=True)

    assert not [e for e in resolved.world_events_add if e.category == WorldEventCategory.MEAT_DECAYED]
    results = [r for u in resolved.entity_updates.values() for r in u.intent_results if r.source_kind == "CORPSE"]
    assert len(results) == 1 and results[0].accepted

    ledger, decayed_quantity, current = _books_after(decay_state, resolved)
    assert ledger["meat"].get("looted") == meat and ledger["meat"].get("vanished", 0.0) == 0.0
    assert decayed_quantity == 0.0
    count, found = _check_meat_books(ledger, current, decayed_quantity)
    assert (count, found) == (0, []), found


def test_a_body_that_only_decays_keeps_exactly_one_decay_record_and_the_books_agree():
    state, body, meat = _world_with_one_body()
    decay_state, resolved = _decay_tick_update(state, looted=False)

    records = [e for e in resolved.world_events_add if e.category == WorldEventCategory.MEAT_DECAYED]
    assert len(records) == 1 and records[0].payload["quantity"] == float(meat)

    ledger, decayed_quantity, current = _books_after(decay_state, resolved)
    assert ledger["meat"].get("vanished") == meat and decayed_quantity == float(meat)
    assert _check_meat_books(ledger, current, decayed_quantity) == (0, [])


def test_a_refused_whole_loot_does_not_remove_the_decay_record():
    """A loot the resolver refuses (here: the body is already locked by an earlier transfer) takes nothing, so the decay record stays."""
    state, body, meat = _world_with_one_body()
    decay_state = replace(state, tick=body.decay_tick)
    update = WorldDynamicsSystem.resolve_dynamics(decay_state, StateUpdate(), EntityGenerator(42))
    full = ResourceTransferIntent(source_id=body.id, source_kind="CORPSE", items_add=list(body.items), transfer_kind="LOOT")
    update = replace(update, entity_updates={9: EntityUpdate(entity_id=9, resource_transfers=[full])})
    stuffed = replace(decay_state.entities[9], inventory=replace(decay_state.entities[9].inventory, max_slots=0))
    resolved = ResourceTransactionSystem.resolve_all(replace(decay_state, entities={**decay_state.entities, 9: stuffed}), update)

    results = [r for u in resolved.entity_updates.values() for r in u.intent_results if r.source_kind == "CORPSE"]
    assert len(results) == 1 and not results[0].accepted
    assert len([e for e in resolved.world_events_add if e.category == WorldEventCategory.MEAT_DECAYED]) == 1
