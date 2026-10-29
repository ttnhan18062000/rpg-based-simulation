"""TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO, the owed scenario (survival-needs.md l.1015): a hungry worker with no gold
beside the inn is not fed, goes to its paid work, and eats once it can pay.

Run through the real kernel under the ATOMIC payment law (the law after the free-meal removal; main keeps CLAMP, where a broke subject is fed and this
path never fires). The core EAT action's own free relief (``core_actions.eat_update``, removed by D73) is switched off here so the inn is the only
way to a meal, which is the stack the removal lands. The subject is staged beside the inn on urban_political, alone, hungry enough to be pulled but far from the starvation line."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.config.profiles import PROD_SMALL
from src.engine import service_admission
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.engine.service_prices import EAT_PRICE_GOLD
from src.engine.work_shift import SHIFT_TICKS, WAGE_GOLD
from src.platform.rng import DeterministicRNG
from tests.helpers.scenario import DEFAULT_FLAGS, DEFAULT_SEED, compile_world

WHO = 2
INN_ID = 20003


@pytest.fixture
def no_free_meal_d73_shape(monkeypatch):
    """The free relief of the core EAT action (``core_actions.eat_update``) is removed, as D73 removes it. This patches the NAME ``can_use_inn_meal`` inside
    ``core_actions`` only: ``service_admission`` and ``building_services`` import their own reference, so admission and the inn's meal stay real and a meal
    here can only come from the inn's paid service."""
    monkeypatch.setattr("src.engine.domain.core_actions.can_use_inn_meal", lambda eater: False)


def _staged(hunger=50.0):
    state = compile_world("urban_political", seed=46)
    inn = state.buildings[INN_ID]
    e = state.entities[WHO]
    e = replace(e, navigation=replace(e.navigation, position=(inn.position[0], inn.position[1] + 1.0)),
                biological=replace(e.biological, hunger=hunger, sleep_debt=0.0), inventory=replace(e.inventory, gold=0, items=[]))
    object.__setattr__(state, "entities", {WHO: e})
    # Only the inn and the town hall: no shop to sell to and no node to gather, so the one earning way left is a paid shift.
    object.__setattr__(state, "buildings", {bid: b for bid, b in state.buildings.items() if bid in (INN_ID, 20000)})
    object.__setattr__(state, "resource_nodes", {})
    object.__setattr__(state, "corpses", {})
    return state


def test_a_broke_hungry_worker_beside_the_inn_earns_a_wage_and_then_buys_a_meal(monkeypatch, no_free_meal_d73_shape):
    monkeypatch.setattr(service_admission, "SERVICE_PAYMENT_LAW", service_admission.PaymentLaw.ATOMIC)
    kernel = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=_staged(), rng=DeterministicRNG(DEFAULT_SEED),
                    flags={**DEFAULT_FLAGS, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
    peak_gold, wage_tick, meal_tick = 0, None, None
    try:
        for _ in range(900):
            kernel.tick_once()
            ent = kernel._state.entities[WHO]
            if not ent.combat.alive:
                break
            peak_gold = max(peak_gold, ent.inventory.gold)
            if wage_tick is None and ent.inventory.gold >= WAGE_GOLD:
                wage_tick = kernel._state.tick
            if wage_tick is not None and meal_tick is None and ent.inventory.gold < peak_gold and ent.inventory.gold >= peak_gold - EAT_PRICE_GOLD:
                meal_tick = kernel._state.tick
    finally:
        kernel.shutdown()
    assert wage_tick is not None, "the broke hungry worker never earned a wage (no WORK is dispatched on arrival)"
    assert meal_tick is not None and meal_tick > wage_tick, "having earned, it never paid for a meal"


def _run_until_work(kernel, limit=300):
    for _ in range(limit):
        kernel.tick_once()
        ent = kernel._state.entities[WHO]
        if ent.task.payload.get("action") == "WORK":
            return kernel._state.tick
    return None


def _kernel(monkeypatch, hunger):
    monkeypatch.setattr(service_admission, "SERVICE_PAYMENT_LAW", service_admission.PaymentLaw.ATOMIC)
    return Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=_staged(hunger), rng=DeterministicRNG(DEFAULT_SEED),
                  flags={**DEFAULT_FLAGS, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())


def test_hunger_rising_during_a_feasible_shift_does_not_end_it_and_the_worker_is_paid_and_eats(monkeypatch, no_free_meal_d73_shape):
    """A pressing hunger (past the escalation onset) is the case where a wake would be tempting: the shift fits before the line, so it is finished."""
    kernel = _kernel(monkeypatch, hunger=70.0)
    try:
        started = _run_until_work(kernel)
        assert started is not None, "no shift began"
        hunger_at_start = kernel._state.entities[WHO].biological.hunger
        wage_tick = None
        for _ in range(SHIFT_TICKS + 30):
            kernel.tick_once()
            if kernel._state.entities[WHO].inventory.gold >= WAGE_GOLD:
                wage_tick = kernel._state.tick
                break
        hunger_at_wage = kernel._state.entities[WHO].biological.hunger
        for _ in range(300):
            kernel.tick_once()
            if kernel._state.entities[WHO].inventory.gold < WAGE_GOLD:
                break
        meal_paid = kernel._state.entities[WHO].inventory.gold < WAGE_GOLD
    finally:
        kernel.shutdown()
    assert wage_tick is not None and SHIFT_TICKS - 2 <= wage_tick - started <= SHIFT_TICKS + 5, "the wage comes at the end of one uninterrupted shift"
    assert hunger_at_wage > hunger_at_start, "hunger rose through the shift and did not end it"
    assert meal_paid, "paid, it bought its meal"


def test_a_present_threat_ends_a_held_shift_with_no_wage(monkeypatch, no_free_meal_d73_shape):
    from src.core.builder import V2EntityBuilder
    from src.core.enums import EntityRole, Faction

    kernel = _kernel(monkeypatch, hunger=50.0)
    try:
        started = _run_until_work(kernel)
        assert started is not None, "no shift began"
        subject = kernel._state.entities[WHO]
        goblin = (V2EntityBuilder(900).kind("monster").location(subject.navigation.position[0] + 1.0, subject.navigation.position[1])
                  .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, properties={"species_id": "goblin"})
                  .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True).lifecycle(active=True).build())
        kernel._state = replace(kernel._state, entities={**kernel._state.entities, 900: goblin})
        for _ in range(SHIFT_TICKS + 10):
            kernel.tick_once()
            ent = kernel._state.entities[WHO]
            if ent.inventory.gold >= WAGE_GOLD:
                break
        paid = kernel._state.entities[WHO].inventory.gold >= WAGE_GOLD and kernel._state.tick - started <= SHIFT_TICKS + 5
    finally:
        kernel.shutdown()
    assert not paid, "the shift was interrupted by a present threat to life, so the wage (paid on the last tick) is forfeited"


def test_a_present_threat_at_a_hiring_inn_never_makes_a_shift_that_ends_after_one_tick_and_the_shift_runs_once_it_is_gone(monkeypatch, no_free_meal_d73_shape):
    """The frontier s46 guard-9 shape in small (D73-shape probe: 58 one-tick shifts, each woken by the same hostile, none completed). The threat test is the
    real one but its answer is scripted for a window (a hostile in view of a broke, hungry worker at a hiring inn), so the seam is exact: through the real kernel
    no WORK is started that the next tick cuts off, the hunger project stays current, and when the threat is gone the shift starts, runs to its end and pays."""
    window_end = 80
    ticks = {"now": 0}

    def scripted(entity, state):
        return state.tick < window_end

    for module in ("src.engine.scheduler", "src.engine.work_shift", "src.engine.building_arrival"):
        monkeypatch.setattr(f"{module}.held_work_is_threatened", scripted)
    kernel = _kernel(monkeypatch, hunger=70.0)
    object.__setattr__(kernel._state, "buildings", {INN_ID: kernel._state.buildings[INN_ID]})
    held, project_ids, paid_at = {}, set(), None  # shift_start -> ticks the shift was held
    try:
        for _ in range(window_end + SHIFT_TICKS + 40):
            kernel.tick_once()
            ent = kernel._state.entities[WHO]
            project_ids.add(ent.strategic.current_project_id)
            if ent.task.payload.get("action") == "WORK":
                started = ent.task.payload.get("shift_start")
                held[started] = held.get(started, 0) + 1
            if paid_at is None and ent.inventory.gold >= WAGE_GOLD:
                paid_at = kernel._state.tick
    finally:
        kernel.shutdown()
    last = kernel._state.tick
    cut_off = {start: n for start, n in held.items() if n < SHIFT_TICKS - 2 and start <= last - SHIFT_TICKS}  # (a shift still running when the run stops is not cut off)
    assert not cut_off, f"a shift was started and cut off before its end (shift_start -> ticks held: {cut_off})"
    assert paid_at is not None and paid_at > window_end, "once the threat is gone the shift starts, finishes and pays"
    assert len({p for p in project_ids if p and p.startswith("proj_hunger")}) == 1, f"no second hunger project was made (saw {project_ids})"
