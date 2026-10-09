"""EXCH-02 (owner decision 34): a shift of work at an inn. The WORK action counts the ticks since the shift began (carried by the held task's
payload), pays WAGE_GOLD once, out of the inn's own purse, on the SHIFT_TICKS-th tick, and ends; a short purse pays nothing."""
from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.conservation import ResourceTransactionResolver
from src.core.enums import ReasonCode
from src.core.state import AuthoritativeState, BuildingState, InventoryComponent
from src.engine.domain.action_router import ActionRouter
from src.engine.work_shift import SHIFT_START, SHIFT_TICKS, WAGE_GOLD, nearest_work, shift_done, work_update


def _world(inn_gold=100, pos=(5.0, 6.0), tick=1):
    inn = BuildingState(id=10, kind="inn", position=(5.0, 5.0), functional=True, inventory=InventoryComponent(gold=inn_gold))
    ent = V2EntityBuilder(1).kind("worker").properties({"species_id": "human"}).location(*pos).inventory(gold=0).social(public_reputation=0.0).build()
    return AuthoritativeState(tick=tick, seed=1, entities={1: ent}, buildings={10: inn}, town_tiles={(5, 5), (5, 6)}), ent, inn


def test_no_wage_before_the_shift_is_done_and_the_wage_on_its_last_tick():
    state, ent, inn = _world()
    start = 100
    early = work_update(ent, {SHIFT_START: start}, start + SHIFT_TICKS - 2, state)[1]
    assert not early.resource_transfers and not shift_done(early)
    last = work_update(ent, {SHIFT_START: start}, start + SHIFT_TICKS - 1, state)[1]
    (wage,) = last.resource_transfers
    assert wage.source_kind == "WAGE" and wage.source_id == 10 and wage.gold_delta == WAGE_GOLD and shift_done(last)


def test_the_action_router_runs_work_and_the_wage_carries_a_per_shift_transaction_id():
    state, ent, inn = _world()
    payload = {"action": "WORK", "target_id": 10, SHIFT_START: 7}
    a = ActionRouter.execute_action(ent, payload, 7 + SHIFT_TICKS - 1, None, state)[1].resource_transfers[0]
    b = ActionRouter.execute_action(ent, payload, 7 + SHIFT_TICKS - 1, None, state)[1].resource_transfers[0]
    assert a.transaction_id == b.transaction_id  # the held action runs twice a tick; the shift is paid once


def test_the_wage_comes_out_of_the_inns_purse_and_a_short_purse_pays_nothing():
    state, ent, inn = _world(inn_gold=100)
    wage = work_update(ent, {SHIFT_START: 1}, SHIFT_TICKS, state)[1].resource_transfers[0]
    paid = ResourceTransactionResolver.resolve(state, ent, wage, reservations={})
    assert paid.accepted and paid.inventory_update.gold_delta == WAGE_GOLD and paid.building_update.inventory.gold_delta == -WAGE_GOLD
    short, ent2, _ = _world(inn_gold=WAGE_GOLD - 1)
    refused = ResourceTransactionResolver.resolve(short, ent2, wage, reservations={})
    assert not refused.accepted and refused.reason == ReasonCode.LIQUIDITY_EXHAUSTED


def test_a_subject_away_from_an_inn_has_no_shift_and_the_task_ends():
    state, ent, inn = _world(pos=(5.0, 9.0))
    out = work_update(ent, {SHIFT_START: 1}, 50, state)[1]
    assert shift_done(out) and not out.resource_transfers


def test_work_opens_only_where_an_inn_could_pay_a_wage():
    state, ent, inn = _world(inn_gold=WAGE_GOLD)
    assert nearest_work(state, ent) is inn
    poor, ent2, _ = _world(inn_gold=WAGE_GOLD - 1)
    assert nearest_work(poor, ent2) is None
    closed = replace(state, buildings={10: replace(inn, functional=False)})
    assert nearest_work(closed, ent) is None


def test_only_a_kind_that_keeps_coin_and_trades_is_served_or_hired():
    from src.engine.serves import keeps_coin, serves
    state, ent, inn = _world()
    assert keeps_coin(ent) and serves(state, ent, inn)
    wolf = replace(ent, identity=replace(ent.identity, properties={"species_id": "wolf"}))
    assert not keeps_coin(wolf) and not serves(state, wolf, inn)
    assert nearest_work(state, wolf) is None


def test_a_building_whose_region_belongs_to_a_hostile_faction_does_not_serve():
    from src.core.enums import Faction
    from src.core.state import RegionState
    state, ent, inn = _world()
    owner = Faction.MONSTER_HORDE
    region = RegionState(id="r", name="r", bounds=(0, 0, 20, 20), owner_faction_id=int(owner))
    hostile = replace(state, regions={"r": region})
    human = replace(ent, identity=replace(ent.identity, faction=Faction.TOWN_GUARD if hasattr(Faction, "TOWN_GUARD") else Faction.HERO_GUILD,
                                          properties={"species_id": "human", "faction_id": "town_council"}))
    from src.engine.serves import serves
    assert not serves(hostile, human, inn)  # a monster horde region does not serve a town council member
    free = replace(state, regions={"r": replace(region, owner_faction_id=None)})
    assert serves(free, human, inn)  # a region with no owner serves anyone with the trait
