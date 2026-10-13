"""EXCH-02, ruling 66: wages granted earlier in a tick are spent. `ResourceTransactionSystem.resolve_all` resolves a tick's intents one after another
in entity-id order; the purse, the treasury and the maintenance count are read as the tick stands so far, not as it started, so simultaneous
finishers cannot be paid coin the purse no longer holds or counted past the building's need."""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction, ReasonCode
from src.core.state import AuthoritativeState, BuildingState, InventoryComponent, RegionState
from src.core.treasury import treasury_key
from src.core.updates import EntityUpdate, ResourceTransferIntent, StateUpdate
from src.engine.economy import ResourceTransactionSystem
from src.engine.work_shift import WAGE_GOLD

HERO = int(Faction.HERO_GUILD)
KEY = treasury_key(HERO)


def _state(workers, *, purse, needed, hires=False, treasury=0.0, done=0):
    inn = BuildingState(id=10, kind="inn", position=(5.0, 5.0), functional=True, inventory=InventoryComponent(gold=purse),
                        maintenance_shifts_needed=needed, maintenance_shifts_done=done, hires_for_pay=hires)
    ents = {i: V2EntityBuilder(i).kind("worker").location(5.0, 6.0).inventory(gold=0).build() for i in range(1, workers + 1)}
    region = RegionState(id="r", name="R", bounds=(0, 0, 50, 50), owner_faction_id=HERO)
    return AuthoritativeState(tick=5, seed=1, entities=ents, buildings={10: inn}, regions={"r": region}, global_resources={KEY: treasury})


def _wage(worker_id, *, maintenance):
    return ResourceTransferIntent(source_id=10, source_kind="WAGE", gold_delta=WAGE_GOLD, transfer_kind="WAGE", transaction_id=f"wage:{worker_id}",
                                  treasury_faction=HERO, treasury_gold=0, treasury_pays=maintenance, maintenance_shift=maintenance)


def _resolve(state, maintenance):
    updates = {i: EntityUpdate(entity_id=i, resource_transfers=[_wage(i, maintenance=maintenance)]) for i in state.entities}
    return ResourceTransactionSystem.resolve_all(state, StateUpdate(entity_updates=updates))


def _results(out):
    return {i: next(r for r in u.intent_results) for i, u in out.entity_updates.items()}


def _paid(out):
    return {i: (u.inventory.gold_delta if u.inventory else 0) for i, u in out.entity_updates.items()}


def _coin_change(state, out):
    """Net change of all coin: workers' receipts + the building's purse change + the treasury's change. Zero when conserved."""
    workers = sum(_paid(out).values())
    purse = out.building_updates[10].inventory.gold_delta if 10 in out.building_updates and out.building_updates[10].inventory else 0
    treasury = out.resource_updates.get(KEY, 0.0)
    return workers + purse + treasury


def test_three_finishers_with_a_need_of_one_count_exactly_one_maintenance_shift():
    state = _state(3, purse=100, needed=1)
    out = _resolve(state, maintenance=True)
    assert [r.accepted for r in _results(out).values()] == [True, False, False]
    assert out.building_updates[10].maintenance_shifts_done_delta == 1
    assert _paid(out) == {1: WAGE_GOLD, 2: 0, 3: 0}
    assert _coin_change(state, out) == 0


def test_a_purse_holding_exactly_one_wage_pays_one_commercial_finisher_and_refuses_the_other():
    state = _state(2, purse=WAGE_GOLD, needed=0, hires=True)
    out = _resolve(state, maintenance=False)
    results = _results(out)
    assert results[1].accepted and not results[2].accepted and results[2].reason == ReasonCode.LIQUIDITY_EXHAUSTED
    assert _paid(out) == {1: WAGE_GOLD, 2: 0}
    assert out.building_updates[10].inventory.gold_delta == -WAGE_GOLD   # the purse is never driven below zero
    assert _coin_change(state, out) == 0


def test_the_treasury_top_up_is_spent_too_when_the_purse_is_empty():
    state = _state(3, purse=0, needed=3, treasury=WAGE_GOLD * 2)
    out = _resolve(state, maintenance=True)
    assert [r.accepted for r in _results(out).values()] == [True, True, False]   # two wages' worth in the treasury: the third is refused
    assert out.resource_updates[KEY] == -WAGE_GOLD * 2
    assert out.building_updates[10].maintenance_shifts_done_delta == 2
    assert _coin_change(state, out) == 0


def test_a_period_reset_staged_this_tick_is_kept_with_the_shift_counted_after_it():
    from src.core.updates import BuildingUpdate
    state = _state(1, purse=100, needed=1, done=1)
    reset = BuildingUpdate(building_id=10, maintenance_shifts_done_set=0)
    updates = {1: EntityUpdate(entity_id=1, resource_transfers=[_wage(1, maintenance=True)])}
    out = ResourceTransactionSystem.resolve_all(state, StateUpdate(entity_updates=updates, building_updates={10: reset}))
    assert _results(out)[1].accepted                                           # the staged reset opens the period: the shift counts
    assert out.building_updates[10].maintenance_shifts_done_set == 0 and out.building_updates[10].maintenance_shifts_done_delta == 1


def test_two_sales_to_a_shop_cannot_spend_its_purse_twice():
    from src.core.state import ItemStack
    state = _state(2, purse=0, needed=0)
    shop = replace(state.buildings[10], kind="shop", inventory=InventoryComponent(gold=10))
    ents = {i: replace(e, inventory=replace(e.inventory, items=[ItemStack("wood", 4)])) for i, e in state.entities.items()}
    state = replace(state, buildings={10: shop}, entities=ents)
    sells = {i: ResourceTransferIntent(source_id=10, source_kind="SHOP_SELL", items_remove=[ItemStack("wood", 4)], gold_delta=6,
                                       transfer_kind="SELL", transaction_id=f"sell:{i}") for i in state.entities}
    out = ResourceTransactionSystem.resolve_all(state, StateUpdate(entity_updates={i: EntityUpdate(entity_id=i, resource_transfers=[s]) for i, s in sells.items()}))
    assert [r.accepted for r in _results(out).values()] == [True, False]       # 10 gold covers one 6-gold sale, not two
    assert out.building_updates[10].inventory.gold_delta == -6


def test_the_order_is_deterministic_by_entity_id():
    first = _results(_resolve(_state(3, purse=100, needed=1), maintenance=True))
    again = _results(_resolve(_state(3, purse=100, needed=1), maintenance=True))
    assert {i: r.accepted for i, r in first.items()} == {i: r.accepted for i, r in again.items()} == {1: True, 2: False, 3: False}
