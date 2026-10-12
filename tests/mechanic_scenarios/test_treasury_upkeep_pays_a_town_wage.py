"""ME-S21 (EXCH-02, decisions 37, 51 and 58, ruling 61): a building meets its upkeep from its own purse, the treasury tops up only a shortfall, and a
treasury that holds nothing leaves an empty building closed.

Upkeep is checked against the building's own purse: nothing is paid out to a payee, so a funded purse is never drawn down by it. The inn pays the
worker's wage (6 gold, under the tax floor) from its own purse. Coin is conserved across the treasury, the inn and the worker over the whole run.
Arms: (main) an inn with a purse of its own pays the wage and the treasury pays nothing; (shortfall) an empty inn is topped up by exactly the
shortfall and, at 5 against a wage of 6, cannot pay the wage until its own sales raise the purse (disclosed: how upkeep budgets wages is the
follow-up TCK-20261011-NEAREST-WORK-READS-THE-DECLARED-WORK-BUILDINGS-NOT-ONLY-THE-INN); (control) an empty treasury cannot top up, the inn is
disabled and offers no work, and no coin appears.
"""
from __future__ import annotations

from dataclasses import replace

from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, BuildingState, InventoryComponent, RegionState, TaskComponent
from src.core.treasury import total_coin, treasury_key
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.work_shift import SHIFT_START, WAGE_GOLD
from src.platform.rng import DeterministicRNG
from tests.helpers.kernel_pinning import PinnedNormalGovernor

HERO = int(Faction.HERO_GUILD)
KEY = treasury_key(HERO)
TICKS = 260  # one shift (200 ticks) plus the upkeep ticks before it


def _run(treasury: float, inn_gold: int = 0):
    region = RegionState(id="town", name="Town", bounds=(0, 0, 20, 20), kind="TOWN", owner_faction_id=HERO, tax_share=0.1)
    inn = BuildingState(id=10, kind="inn", position=(5.0, 5.0), functional=True, inventory=InventoryComponent(gold=inn_gold), hires_for_pay=True, maintenance_shifts_needed=1)
    worker = (V2EntityBuilder(1).kind("worker").properties({"species_id": "human"}).location(5.0, 6.0).inventory(gold=0)
              .social(public_reputation=0.0).lifecycle(active=True).combat(alive=True, readiness=100.0).build())
    worker = replace(worker, task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "WORK", "target_id": 10, SHIFT_START: 1}))
    state = AuthoritativeState(tick=0, seed=1, entities={1: worker}, buildings={10: inn}, regions={"town": region},
                               town_tiles={(5, 5), (5, 6)}, global_resources={KEY: treasury})
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(1),
                    governor=PinnedNormalGovernor(), flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True},
                    executor=LocalSequentialExecutor())
    try:
        before = total_coin(kernel.state)
        for _ in range(TICKS):
            kernel.tick_once()
        return kernel.state, total_coin(kernel.state) - before
    finally:
        kernel.shutdown()


def test_main_arm_an_inn_with_its_own_purse_pays_the_wage_and_the_treasury_pays_nothing():
    final, drift = _run(1000.0, inn_gold=100)
    assert final.global_resources[KEY] == 1000.0                    # the purse covered the upkeep: no top-up, no sink
    assert final.buildings[10].inventory.gold == 100 - WAGE_GOLD    # the only coin that left the purse is the wage
    assert final.entities[1].inventory.gold == WAGE_GOLD            # the worker earned the wage (6 is under the tax floor)
    assert final.buildings[10].functional is True
    assert drift == 0.0                                             # no coin appeared or vanished


def test_shortfall_arm_an_empty_inn_is_topped_up_for_upkeep_and_the_worker_is_paid_by_the_maintenance_shift():
    final, drift = _run(1000.0)
    # Upkeep is one shift's wage (6): the treasury tops the empty purse up by exactly that, twice over 260 ticks (before and after the period's
    # counter reset). The first top-up funds the worker's counted maintenance shift (the purse pays the wage), the second the next period's upkeep.
    assert final.global_resources[KEY] == 1000.0 - 2 * WAGE_GOLD
    assert final.buildings[10].inventory.gold == WAGE_GOLD and final.buildings[10].functional is True
    assert final.entities[1].inventory.gold == WAGE_GOLD            # the worker earned the wage from the topped-up purse
    assert drift == 0.0                                             # the treasury's coin moved to the worker: nothing appeared or vanished


def test_control_an_empty_treasury_pays_nobody_and_the_unpaid_inn_offers_no_work():
    final, drift = _run(0.0)
    assert final.global_resources[KEY] == 0.0
    assert final.buildings[10].inventory.gold == 0 and final.buildings[10].functional is False
    assert final.entities[1].inventory.gold == 0
    assert drift == 0.0
