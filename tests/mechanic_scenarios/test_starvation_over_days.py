"""LB-S18 (owner decision 36, SURV-02 amendment): starvation weakens first and kills over days.

MAIN: a lone full-health person with no food reachable. Observables are the stage ORDER and the window, in ticks after the starving
line (hunger 95): it is weakened (hunger >= 85) with its health untouched before the line, loses health slowly after it, is still
alive a day (2400 ticks) past the line and dead by 3.5 days (8400). CONTROL: the same person eats a day past the line: it is no longer weakened, its health stops
falling and it stays alive. Hunger accumulates at 0.1 per tick (the base medium rate) and sleep debt is held at zero, so only
hunger acts.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Tuple

from src.config.profiles import PROD_SMALL
from src.engine import starvation as sv
from src.engine.executor import LocalSequentialExecutor
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from tests.helpers.scenario import DEFAULT_FLAGS, DEFAULT_SEED, compile_world

WORLD_ID = "mechanic_scenario_combat_judgement_withdrawal"
F, H = 2, 1
DAY = 2400  # ticks (1 tick = 36 s)


def _state(hunger=94.0, who=F, hp=100, need_profile=None):
    state = compile_world(WORLD_ID)
    entities = {who: state.entities[who]}  # the subject alone: nothing to fight
    e = entities[who]
    props = dict(e.identity.properties)
    if need_profile:
        props["need_profile_id"] = need_profile
    entities[who] = replace(e, biological=replace(e.biological, hunger=hunger, sleep_debt=0.0), identity=replace(e.identity, properties=props),
                            combat=replace(e.combat, hp=hp, max_hp=hp, atk=1))
    object.__setattr__(state, "entities", entities)
    return state


def _kernel(state):
    return Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(DEFAULT_SEED),
                  flags={**DEFAULT_FLAGS, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())


def _run(kernel, ticks, who=F) -> List[Tuple[int, float, int, bool]]:
    rows = []
    for _ in range(ticks):
        kernel.tick_once()
        e = kernel._state.entities[who]
        rows.append((kernel._state.tick, e.biological.hunger, e.combat.hp, e.combat.alive))
        if not e.combat.alive:
            break
    return rows


def _rates(monkeypatch):
    monkeypatch.setattr("src.engine.apply.need_rates", lambda entity: (0.1, 0.0))


def test_main_a_person_with_no_food_weakens_then_loses_health_slowly_and_dies_over_days(monkeypatch):
    _rates(monkeypatch)
    kernel = _kernel(_state())
    try:
        rows = _run(kernel, 7000)
    finally:
        kernel.shutdown()
    weakened_tick = next(t for t, h, hp, a in rows if h >= sv.WEAKENED_LINE)
    line_tick = next(t for t, h, hp, a in rows if h >= sv.STARVING_LINE)
    death_tick = next((t for t, h, hp, a in rows if not a), None)
    assert weakened_tick < line_tick, "the body must weaken before it starts losing health"
    # stage 1: weakened, health untouched until the line
    assert all(hp == 100 for t, h, hp, a in rows if t < line_tick)
    # stage 2: slow loss, alive a day past the line, dead by 3.5 days; death 2 to 3 days after the line
    at_day = next(hp for t, h, hp, a in rows if t == line_tick + DAY)
    assert 0 < at_day < 100, f"a day past the line it should be alive and hurt, hp {at_day}"
    assert death_tick is not None, "the person never died"
    assert 4800 <= death_tick - line_tick <= 7200, f"died {death_tick - line_tick} ticks after the line"
    assert death_tick - line_tick <= 3.5 * DAY


def test_control_a_person_who_eats_stops_losing_health_and_survives(monkeypatch):
    _rates(monkeypatch)
    kernel = _kernel(_state())
    try:
        rows = _run(kernel, 0)
        for _ in range(500):  # past the line, into stage 2
            kernel.tick_once()
        while kernel._state.entities[F].biological.hunger < sv.STARVING_LINE + 4:
            kernel.tick_once()
        crossed = kernel._state.tick
        for _ in range(DAY):
            kernel.tick_once()
        hurt = kernel._state.entities[F]
        assert hurt.combat.alive and hurt.combat.hp < 100
        # the person eats
        fed_entities = dict(kernel._state.entities)
        fed_entities[F] = replace(hurt, biological=replace(hurt.biological, hunger=0.0))
        kernel2 = _kernel(replace(kernel._state, entities=fed_entities))
    finally:
        kernel.shutdown()
    try:
        hp_after_meal = kernel2._state.entities[F].combat.hp
        for _ in range(800):  # hunger climbs back from 0 at 0.1 per tick: still below the weakened line (85)
            kernel2.tick_once()
        final = kernel2._state.entities[F]
        assert not sv.is_weakened(final.biological.hunger)
    finally:
        kernel2.shutdown()
    assert final.combat.alive and final.combat.hp == hp_after_meal, "health kept falling after the meal"
    assert crossed > 0


def test_main_second_kind_a_non_people_kind_with_its_own_need_profile_and_max_hp_dies_in_the_same_window(monkeypatch):
    """Owner decision 42: the rules cover every living kind. A goblin (35 max HP) on the carnivore need profile (hunger "high", 0.15 a tick):
    the profile sizes its hunger rate (real ``need_rates``, sleep debt held at zero) and its max HP sizes the loss period (round(6000 / 35) = 171),
    so it is weakened before the line with full health and dies 4800 to 7200 ticks after it."""
    from src.engine.biological_needs import need_rates as real_need_rates

    monkeypatch.setattr("src.engine.apply.need_rates", lambda entity: (real_need_rates(entity)[0], 0.0))
    kernel = _kernel(_state(who=H, hp=35, need_profile="carnivore_survival"))
    try:
        rows = _run(kernel, 7500, who=H)
    finally:
        kernel.shutdown()
    weakened_tick = next(t for t, h, hp, a in rows if h >= sv.WEAKENED_LINE)
    line_tick = next(t for t, h, hp, a in rows if h >= sv.STARVING_LINE)
    death_tick = next((t for t, h, hp, a in rows if not a), None)
    assert weakened_tick < line_tick
    assert all(hp == 35 for t, h, hp, a in rows if t < line_tick)
    assert 0 < next(hp for t, h, hp, a in rows if t == line_tick + DAY) < 35
    assert death_tick is not None and 4800 <= death_tick - line_tick <= 7200, f"died {None if death_tick is None else death_tick - line_tick} ticks after the line"
