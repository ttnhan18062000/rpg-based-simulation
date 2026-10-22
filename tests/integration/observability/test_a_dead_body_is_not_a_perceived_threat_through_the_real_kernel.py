"""A dead body is not a perceived threat (TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT), through the real kernel.

Raider 27 of crowded_frontier seed 45 (the v1 gate's V3 death) at hp 2/70 stands at (54,40), east of an inn at (23,39). A guard and two workers lie (or stand) at
x 44-46 on its walk. When they lie there DEAD the raider must not panic from them; when they stand there ALIVE it still does. In the gate run they were corpses and
the raider shuttled between the corpses and the inn until it starved (the neighbour view lists the dead, and the panic gate counted them as threats).
"""
from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

PINNED = {11: (45.0, 41.0), 3: (46.0, 40.0), 2: (44.0, 40.0)}
REMOVED = (15, 18)  # the two wild hunters nearby: the east is quiet


def _run_raider(run_id, *, alive, hunger, ticks):
    """Panic ticks and the lowest hunger of raider 27 over `ticks` ticks, with the three townsfolk pinned alive or dead on its walk."""
    from tools.test_architecture.rpg_gate_run import build_kernel

    kernel = build_kernel("crowded_frontier", 45, run_id)
    panic_ticks, lowest_hunger = [], hunger
    try:
        state = kernel.state
        entities = dict(state.entities)
        raider = entities[27]
        entities[27] = replace(raider, navigation=replace(raider.navigation, position=(54.0, 40.0)), combat=replace(raider.combat, hp=2, max_hp=70),
                               biological=replace(raider.biological, hunger=hunger, sleep_debt=0.0), inventory=replace(raider.inventory, gold=10))
        object.__setattr__(state, "entities", entities)
        for _ in range(ticks):
            held = dict(kernel.state.entities)
            for eid, pos in PINNED.items():
                e = held[eid]
                held[eid] = replace(e, navigation=replace(e.navigation, position=pos), combat=replace(e.combat, hp=e.combat.max_hp if alive else 0, alive=alive))
            for eid in REMOVED:
                e = held[eid]
                held[eid] = replace(e, combat=replace(e.combat, hp=0, alive=False), lifecycle=replace(e.lifecycle, active=False))
            object.__setattr__(kernel.state, "entities", held)
            kernel.tick_once()
            raider = kernel.state.entities[27]
            if (raider.task.payload or {}).get("reason") == "PANIC_RETREAT":
                panic_ticks.append(kernel.state.tick)
            lowest_hunger = min(lowest_hunger, raider.biological.hunger)
            if not raider.combat.alive:
                break
        return panic_ticks, lowest_hunger
    finally:
        try:
            kernel.shutdown()
        except Exception:
            pass
        shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)


def test_a_corpse_in_view_gives_no_panic_retreat():
    panic_ticks, _ = _run_raider("corpse_no_panic", alive=False, hunger=50.0, ticks=60)
    assert panic_ticks == []


def test_a_live_hostile_in_view_still_panics():
    panic_ticks, _ = _run_raider("live_hostile_panics", alive=True, hunger=50.0, ticks=60)
    assert panic_ticks, "a hp-2 raider in sight of a live guard and two live workers must still flee"


def test_a_hungry_raider_with_the_townsfolk_dead_on_its_walk_reaches_a_meal_and_eats():
    panic_ticks, lowest = _run_raider("corpse_raider_eats", alive=False, hunger=80.0, ticks=300)
    assert lowest < 70.0, "the raider never ate"
