"""TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING (PERF-D1 amendment A1): a shop's buy price must not depend on how long
the host took to compute the previous tick.

Before the fix `Kernel` turned the previous tick's measured compute time into `global_salience`, stored it in
`AuthoritativeState.pressure_signals`, and `DynamicPriceService.calculate_buy_price` scaled the price by
`1 + salience`, so the same seed on a slower host paid more. `audit_mode` zeroes the measured time, which hid the
defect from audited runs: these tests run with `audit_mode=False` on purpose, with a fake clock standing in for a fast
and for a very slow host.
"""
from __future__ import annotations

import inspect
import re
from dataclasses import replace
from pathlib import Path

import pytest

from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.items import ItemDefinition, ItemRegistry
from src.core.state import AuthoritativeState, BuildingState, ItemKind
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.systems.economy_systems.economy import DynamicPriceService
from src.town.shop import ShopService

TICKS = 3
FAST_STEP_NS = 1_000  # 1 microsecond per clock read
SLOW_STEP_NS = 20_000_000  # 20 ms per clock read: far above the tick budget


@pytest.fixture
def shop_world():
    ItemRegistry._items["healing_potion"] = ItemDefinition(
        id="healing_potion", name="Healing Potion", kind=ItemKind.CONSUMABLE, weight=0.5, value=100,
        properties={"heal_amount": 50},
    )
    shop = BuildingState(id=101, kind="shop", position=(0.0, 0.0), hp=100, functional=True)
    hero = V2EntityBuilder(1).kind("hero").location(0.5, 0.5).inventory(gold=1000).social(public_reputation=0.0).build()
    return AuthoritativeState(tick=1, seed=42, entities={1: hero}, buildings={101: shop})


def _run_with_clock(monkeypatch, state, step_ns):
    """Run TICKS real ticks with audit_mode off and a fake clock that advances `step_ns` per read."""
    now = [0]

    def fake_perf_counter_ns():
        now[0] += step_ns
        return now[0]

    monkeypatch.setattr("time.perf_counter_ns", fake_perf_counter_ns)
    kernel = Kernel(
        profile=PROD_SMALL, state=state, rng=DeterministicRNG(42),
        flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": False}, executor=LocalSequentialExecutor(),
    )
    try:
        for _ in range(TICKS):
            kernel.tick_once()
        return kernel._state
    finally:
        kernel.shutdown()


def _buy_cost(shop_world, final_state):
    """What a purchase costs against the shop at the pressure the run ended with."""
    priced = replace(shop_world, pressure_signals=dict(final_state.pressure_signals))
    res = ShopService.buy_item(priced.entities[1], "healing_potion", 1, priced)
    assert res is not None
    return res.entity_updates[1].resource_transfers[0].gold_cost


def test_buy_price_is_the_same_on_a_fast_and_a_very_slow_host(monkeypatch, shop_world):
    fast = _run_with_clock(monkeypatch, shop_world, FAST_STEP_NS)
    slow = _run_with_clock(monkeypatch, shop_world, SLOW_STEP_NS)

    assert _buy_cost(shop_world, fast) == _buy_cost(shop_world, slow) == 100


def test_no_measured_timing_reaches_authoritative_pressure_signals(monkeypatch, shop_world):
    for step_ns in (FAST_STEP_NS, SLOW_STEP_NS):
        final = _run_with_clock(monkeypatch, shop_world, step_ns)

        assert final.pressure_signals == {}, (step_ns, dict(final.pressure_signals))


def test_buy_price_is_a_function_of_the_item_value_alone():
    assert list(inspect.signature(DynamicPriceService.calculate_buy_price).parameters) == ["base_value"]
    assert DynamicPriceService.calculate_buy_price(100) == 100
    assert DynamicPriceService.calculate_buy_price(0.2) == 1  # the one-gold floor is unchanged


def test_no_source_reintroduces_the_salience_or_compute_ratio_signals():
    """Guard: the signals the shop price used to read must not come back under their old names."""
    src = Path(__file__).resolve().parents[3] / "src"
    pattern = re.compile(r"global_salience|compute_ratio")
    offenders = [str(p.relative_to(src)) for p in src.rglob("*.py") if pattern.search(p.read_text(encoding="utf-8"))]

    assert offenders == [], offenders
