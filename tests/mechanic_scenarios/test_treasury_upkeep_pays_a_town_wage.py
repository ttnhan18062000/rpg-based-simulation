"""ME-S21 (EXCH-02, decisions 37, 51 and 58): a broke worker does town work paid out of the treasury's coin, and a treasury that holds none pays nobody.

The treasury of the faction holding the town pays the inn's upkeep INTO THE INN'S OWN PURSE; the inn pays the worker's wage from that purse; the
wage (6 gold) is under the tax floor (a tenth rounded down), so the worker keeps all of it. Coin is conserved across the treasury, the inn and the
worker over the whole run. Control: an empty treasury cannot pay the upkeep, the unpaid inn is disabled and offers no work, and no coin appears.
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


def _run(treasury: float):
    region = RegionState(id="town", name="Town", bounds=(0, 0, 20, 20), kind="TOWN", owner_faction_id=HERO, tax_share=0.1)
    inn = BuildingState(id=10, kind="inn", position=(5.0, 5.0), functional=True, inventory=InventoryComponent(gold=0))
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


def test_the_treasury_funds_the_inn_and_the_inn_pays_the_worker():
    final, drift = _run(1000.0)
    spent = 1000.0 - final.global_resources[KEY]
    assert spent > 0                                                # the treasury fell, by the upkeep it paid
    assert final.buildings[10].inventory.gold == spent - WAGE_GOLD  # ... all of which reached the inn's purse, less the one wage it paid
    assert final.entities[1].inventory.gold == WAGE_GOLD            # the worker earned the wage (6 is under the tax floor)
    assert final.buildings[10].functional is True
    assert drift == 0.0                                             # no coin appeared or vanished


def test_control_an_empty_treasury_pays_nobody_and_the_unpaid_inn_offers_no_work():
    final, drift = _run(0.0)
    assert final.global_resources[KEY] == 0.0
    assert final.buildings[10].inventory.gold == 0 and final.buildings[10].functional is False
    assert final.entities[1].inventory.gold == 0
    assert drift == 0.0
