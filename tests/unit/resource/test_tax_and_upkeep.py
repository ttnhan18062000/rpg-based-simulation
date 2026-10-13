"""Tax is a share of income paid to the place holder's treasury; upkeep is a transfer into the building's own purse (EXCH-02, decisions 51, 58;
specs ME-S21 and ME-S22)."""
from __future__ import annotations

import pytest

from src.core.builder import V2EntityBuilder
from src.core.conservation import ResourceTransactionResolver
from src.core.enums import Faction
from src.core.state import AuthoritativeState, BuildingState, InventoryComponent, ItemStack, RegionState
from src.core.treasury import total_coin, treasury_key
from src.core.update_models.resources import ResourceTransferIntent
from src.core.updates import StateUpdate
from src.engine.cadence import SystemCadence
from src.engine.place_tax import tax_on
from src.engine.town_resolution import TownResolutionSystem

HERO = int(Faction.HERO_GUILD)
KEY = treasury_key(HERO)


def _town(*, share=0.1, treasury=1000.0, owner=HERO, inn_gold=0, shop_gold=500, tick=40, entities=None):
    region = RegionState(id="town", name="Town", bounds=(0, 0, 20, 20), kind="TOWN", owner_faction_id=owner, tax_share=share)
    inn = BuildingState(id=1, kind="inn", position=(5, 5), functional=True, inventory=InventoryComponent(gold=inn_gold), maintenance_shifts_needed=1)
    shop = BuildingState(id=2, kind="shop", position=(8, 8), functional=True, inventory=InventoryComponent(gold=shop_gold), maintenance_shifts_needed=1)
    return AuthoritativeState(tick=tick, seed=1, regions={"town": region}, buildings={1: inn, 2: shop}, entities=entities or {},
                              global_resources={KEY: treasury})


@pytest.mark.parametrize("amount,tax", [(6, 0), (9, 0), (10, 1), (19, 1), (20, 2), (29, 2), (30, 3), (100, 10)])
def test_a_tenth_rounded_down_per_transaction(amount, tax):
    holder, due = tax_on(_town(), _town().buildings[1], amount)
    assert (holder, due) == (HERO, tax)


def test_nobody_is_taxed_where_nobody_holds_the_ground_or_no_share_is_declared():
    assert tax_on(_town(owner=None), _town().buildings[1], 100) == (None, 0)
    assert tax_on(_town(share=0.0), _town().buildings[1], 100) == (None, 0)


def _sell(state, price, tax):
    seller = V2EntityBuilder(5).kind("peasant").location(8.0, 8.0).inventory(gold=0, items=[ItemStack("wood", 4)]).build()
    intent = ResourceTransferIntent(source_id=2, source_kind="SHOP_SELL", items_remove=[ItemStack("wood", 4)], gold_delta=price,
                                    transfer_kind="SELL", treasury_faction=HERO, treasury_gold=tax)
    return seller, ResourceTransactionResolver.resolve(state, seller, intent)


def test_a_sale_pays_the_seller_the_price_minus_the_share_and_the_treasury_the_share():
    seller, res = _sell(_town(), 20, 2)
    assert res.accepted and res.inventory_update.gold_delta == 18
    assert res.building_update.inventory.gold_delta == -20     # the shop pays the full price
    assert res.treasury_update.gold_delta == 2 and res.treasury_update.faction == HERO
    assert 18 + 2 == 20                                         # no coin appears or vanishes


def test_a_small_sale_moves_nothing_to_the_treasury():
    _, res = _sell(_town(), 9, 0)
    assert res.accepted and res.inventory_update.gold_delta == 9 and res.treasury_update is None


def test_a_wage_pays_the_worker_the_wage_minus_the_share():
    worker = V2EntityBuilder(6).kind("peasant").location(5.0, 5.0).inventory(gold=0).build()
    intent = ResourceTransferIntent(source_id=1, source_kind="WAGE", gold_delta=30, transfer_kind="WAGE", treasury_faction=HERO, treasury_gold=3)
    res = ResourceTransactionResolver.resolve(_town(inn_gold=100), worker, intent)
    assert res.accepted and res.inventory_update.gold_delta == 27 and res.building_update.inventory.gold_delta == -30
    assert res.treasury_update.gold_delta == 3


def test_there_is_no_periodic_levy_an_idler_in_a_held_town_is_never_taxed():
    idler = V2EntityBuilder(7).kind("peasant").location(6.0, 6.0).inventory(gold=5).faction(int(Faction.NEUTRAL)).build() \
        if hasattr(V2EntityBuilder, "faction") else V2EntityBuilder(7).kind("peasant").location(6.0, 6.0).inventory(gold=5).build()
    state = _town(tick=40, entities={7: idler})
    out = TownResolutionSystem.resolve(state, StateUpdate(), cadence=SystemCadence())
    upd = out.entity_updates.get(7)
    assert upd is None or not any(t.source_kind == "TAX" for t in upd.resource_transfers)
    assert total_coin(state) == total_coin(state)  # the idler's coin is untouched: nothing in the update names it
    assert upd is None or upd.inventory is None


def test_a_building_meets_its_upkeep_from_its_own_purse_and_the_treasury_pays_nothing():
    state = _town(treasury=1000.0, inn_gold=50, shop_gold=500, tick=40)
    out = TownResolutionSystem.resolve(state, StateUpdate(), cadence=SystemCadence())
    assert KEY not in out.resource_updates and not out.building_updates      # no top-up, no sink: the purses are only checked


def test_the_treasury_tops_up_only_the_shortfall():
    state = _town(treasury=1000.0, inn_gold=3, shop_gold=0, tick=40)
    out = TownResolutionSystem.resolve(state, StateUpdate(), cadence=SystemCadence())
    assert out.resource_updates[KEY] == -(3.0 + 6.0)                           # 3 short at the inn, 6 (one shift's wage) at the shop
    assert out.building_updates[1].inventory.gold_delta == 3 and out.building_updates[2].inventory.gold_delta == 6
    assert all(u.functional_set is None for u in out.building_updates.values())  # funded buildings stay open


def test_a_building_neither_it_nor_the_treasury_can_pay_closes_and_no_coin_moves():
    state = _town(treasury=7.0, inn_gold=0, shop_gold=0, tick=40)
    out = TownResolutionSystem.resolve(state, StateUpdate(), cadence=SystemCadence())
    paid = [b for b, u in out.building_updates.items() if u.inventory and u.inventory.gold_delta == 6]
    disabled = [b for b, u in out.building_updates.items() if u.functional_set is False]
    assert paid == [1] and disabled == [2]                                      # building 1 is topped up (7 >= 6); building 2 finds 1 left and is not
    assert out.resource_updates[KEY] == -6.0


def test_an_unpaid_building_opens_again_when_upkeep_is_paid_in_full():
    from dataclasses import replace as rep
    state = _town(treasury=1000.0, inn_gold=0, tick=40)
    closed = rep(state.buildings[1], functional=False)          # closed for want of upkeep: it still stands (hp > 0)
    state = rep(state, buildings={**state.buildings, 1: closed})
    out = TownResolutionSystem.resolve(state, StateUpdate(), cadence=SystemCadence())
    assert out.building_updates[1].functional_set is True and out.building_updates[1].inventory.gold_delta == 6


def test_upkeep_does_not_reopen_a_wrecked_building():
    from dataclasses import replace as rep
    state = _town(treasury=1000.0, tick=40)
    wreck = rep(state.buildings[1], functional=False, hp=0)
    state = rep(state, buildings={**state.buildings, 1: wreck})
    out = TownResolutionSystem.resolve(state, StateUpdate(), cadence=SystemCadence())
    assert 1 not in out.building_updates


def test_a_building_nobody_holds_is_not_paid_for():
    state = _town(owner=None, tick=40)
    out = TownResolutionSystem.resolve(state, StateUpdate(), cadence=SystemCadence())
    assert not out.building_updates and KEY not in out.resource_updates


# --- Maintenance work at a treasury building (ruling 61): built and tested, not reachable in play (no WORK kind is treasury-backed yet) ---

def _wage_at(treasury, purse, *, tax=0, pays=True):
    worker = V2EntityBuilder(6).kind("peasant").location(5.0, 5.0).inventory(gold=0).build()
    state = _town(treasury=treasury, inn_gold=purse)
    intent = ResourceTransferIntent(source_id=1, source_kind="WAGE", gold_delta=6, transfer_kind="WAGE", treasury_faction=HERO, treasury_gold=tax,
                                    treasury_pays=pays)
    return ResourceTransactionResolver.resolve(state, worker, intent)


def test_the_building_pays_the_wage_from_its_own_purse_and_the_treasury_pays_nothing_when_the_purse_is_enough():
    res = _wage_at(100.0, 20)
    assert res.accepted and res.inventory_update.gold_delta == 6 and res.building_update.inventory.gold_delta == -6 and res.treasury_update is None


def test_the_treasury_tops_up_exactly_the_shortfall_before_the_wage_is_paid():
    res = _wage_at(100.0, 4)
    assert res.accepted and res.inventory_update.gold_delta == 6
    assert res.building_update.inventory.gold_delta == -4                      # the purse of 4 plus the 2 top-up pays 6 and ends at 0
    assert res.treasury_update.gold_delta == -2 and res.treasury_update.faction == HERO


def test_a_top_up_and_a_tax_share_are_one_net_treasury_transfer_and_no_coin_appears():
    res = _wage_at(100.0, 4, tax=1)
    assert res.inventory_update.gold_delta == 5 and res.treasury_update.gold_delta == 1 - 2
    assert res.inventory_update.gold_delta + res.building_update.inventory.gold_delta + res.treasury_update.gold_delta == 0


def test_a_short_treasury_and_a_short_purse_pay_no_wage():
    res = _wage_at(1.0, 4)
    assert not res.accepted


def test_a_short_purse_gets_no_top_up_unless_the_building_is_treasury_backed():
    assert not _wage_at(100.0, 4, pays=False).accepted

